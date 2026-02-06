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
import logging
import os
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
        logger = logging.getLogger(__name__)
        if self.use_bge_m3:
            try:
                from pymilvus.model.hybrid import BGEM3EmbeddingFunction
                self.ef = BGEM3EmbeddingFunction(use_fp16=False, device="cpu")
                self.dense_dim = self.ef.dim["dense"]
                return
            except Exception as exc:
                logger.warning("BGEM3 embedding unavailable, falling back to random embeddings: %s", exc)
                self.use_bge_m3 = False
        self.dense_dim = 768
        self.ef = self.random_embedding

    def random_embedding(self, texts):
        rng = np.random.default_rng()
        return {
            "dense": np.random.rand(len(texts), self.dense_dim),
            "sparse": [{d: rng.random() for d in random.sample(range(1000), random.randint(20, 30))} for _ in texts],
        }

    def _schema_signature(self, schema):
        fields = []
        for field in schema.fields:
            params = dict(getattr(field, "params", {}) or {})
            fields.append((field.name, field.dtype, field.is_primary, field.auto_id, params))
        return sorted(fields, key=lambda item: item[0])

    def _schema_matches(self, existing_schema, desired_schema):
        return self._schema_signature(existing_schema) == self._schema_signature(desired_schema)

    def _drop_on_schema_mismatch(self):
        value = os.getenv("MILVUS_DROP_SCHEMA_MISMATCH", "true")
        return value.strip().lower() in {"1", "true", "yes", "y"}

    def _has_index(self, field_name):
        return any(index.field_name == field_name for index in self.collection.indexes)

    def setup_milvus_collection(self):
        connections.connect("default", host="localhost", port="19530")

        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=self.dense_dim),
        ]
        schema = CollectionSchema(fields, "")
        if utility.has_collection(self.collection_name):
            existing = Collection(self.collection_name)
            if not self._schema_matches(existing.schema, schema):
                if self._drop_on_schema_mismatch():
                    logging.getLogger(__name__).warning(
                        "Dropping Milvus collection '%s' due to schema mismatch.",
                        self.collection_name,
                    )
                    existing.drop()
                    self.collection = Collection(self.collection_name, schema, consistency_level="Strong")
                else:
                    raise ValueError(
                        "Milvus collection '%s' exists with a different schema. "
                        "Set MILVUS_DROP_SCHEMA_MISMATCH=true to drop and recreate it."
                        % self.collection_name
                    )
            else:
                self.collection = existing
        else:
            self.collection = Collection(self.collection_name, schema, consistency_level="Strong")

        sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"}
        if not self._has_index("sparse_vector"):
            self.collection.create_index("sparse_vector", sparse_index)
        dense_index = {"index_type": "FLAT", "metric_type": "IP"}
        if not self._has_index("dense_vector"):
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
            try:
                from pymilvus.model.reranker import BGERerankFunction
                bge_rf = BGERerankFunction(device='cpu')
                results = bge_rf(query, result_texts, top_k=k)
                return results
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "BGE reranker unavailable, returning hybrid search results: %s", exc
                )
                return res
        else:
            return res
