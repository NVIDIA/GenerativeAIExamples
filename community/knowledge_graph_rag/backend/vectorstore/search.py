# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import string
import numpy as np
from pymilvus import (
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection, AnnSearchRequest, RRFRanker, connections,
)

class SearchHandler:
    def __init__(self, collection_name, use_bge_m3=True, use_reranker=True):
        self.use_bge_m3 = use_bge_m3
        self.use_reranker = use_reranker
        self.collection_name = collection_name
        self.dense_dim = None
        self.ef = None
        self.setup_embeddings()
        self.setup_milvus_collection()

    def setup_embeddings(self):
        if self.use_bge_m3:
            from pymilvus.model.hybrid import BGEM3EmbeddingFunction
            self.ef = BGEM3EmbeddingFunction(use_fp16=False, device="cpu")
            self.dense_dim = self.ef.dim["dense"]
        else:
            self.dense_dim = 768
            self.ef = self.random_embedding

    def random_embedding(self, texts):
        rng = np.random.default_rng()
        return {
            "dense": np.random.rand(len(texts), self.dense_dim),
            "sparse": [{d: rng.random() for d in random.sample(range(1000), random.randint(20, 30))} for _ in texts],
        }

    def setup_milvus_collection(self):
        connections.connect("default", host="localhost", port="19530")

        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=self.dense_dim),
        ]
        schema = CollectionSchema(fields, "")
        self.collection = Collection(self.collection_name, schema, consistency_level="Strong")

        sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"}
        self.collection.create_index("sparse_vector", sparse_index)
        dense_index = {"index_type": "FLAT", "metric_type": "IP"}
        self.collection.create_index("dense_vector", dense_index)
        self.collection.load()

    def insert_data(self, docs):
        doc_page_content = [doc.page_content for doc in docs]
        docs_embeddings = self.ef(doc_page_content)
        entities = [doc_page_content, docs_embeddings["sparse"], docs_embeddings["dense"]]
        self.collection.insert(entities)
        self.collection.flush()

    def search_and_rerank(self, query, k=2):
        query_embeddings = self.ef([query])

        sparse_search_params = {"metric_type": "IP"}
        sparse_req = AnnSearchRequest(query_embeddings["sparse"], "sparse_vector", sparse_search_params, limit=k)
        dense_search_params = {"metric_type": "IP"}
        dense_req = AnnSearchRequest(query_embeddings["dense"], "dense_vector", dense_search_params, limit=k)

        res = self.collection.hybrid_search([sparse_req, dense_req], rerank=RRFRanker(), limit=k, output_fields=['text'])
        res = res[0]

        if self.use_reranker:
            result_texts = [hit.fields["text"] for hit in res]
            from pymilvus.model.reranker import BGERerankFunction
            bge_rf = BGERerankFunction(device='cpu')
            results = bge_rf(query, result_texts, top_k=k)
            return results
        else:
            return res