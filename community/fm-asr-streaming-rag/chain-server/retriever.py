# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import os
import time
import requests

from common import get_logger, MAX_DOCS
from utils import get_reranker, get_embedder
from statistics import stdev, mean

from langchain.docstore.document import Document
from pymilvus import (
    MilvusClient,
    MilvusException,
    Collection,
    connections,
    utility,
    CollectionSchema,
    DataType,
    FieldSchema
)

logger = get_logger(__name__)

MILVUS_URI = f"{os.environ.get('MILVUS_STANDALONE_URI', 'localhost')}:19530"
DEFAULT_DB_NAME = "FM_Radio_Stream"

class NVRetriever:
    def __init__(self, milvus_uri=MILVUS_URI, db_name=DEFAULT_DB_NAME):
        self._create_collection(milvus_uri, db_name)
        self.client = MilvusClient(
            collection_name=self.collection_name,
            uri=f'http://{milvus_uri}',
            vector_field="embedding",
            overwrite=False
        )
        # Try to use NIM endpoints, if not found, use endpoints at https://build.nvidia.com
        try:
            self.embed_client = get_embedder()
        except requests.exceptions.ConnectionError as e:
            logger.warning("Falling back to API Endpoint for Embedding model")
            logger.warning(f"Embedding NIM instance not found, using NVIDIA API endpoint ({e})")
            self.embed_client = get_embedder(local=False)
        try:
            self.rerank_client = get_reranker()
        except requests.exceptions.ConnectionError as e:
            logger.warning("Falling back to API Endpoint for Reranking model")
            logger.warning(f"Reranking NIM instance not found, using NVIDIA API endpoint ({e})")
            self.rerank_client = get_reranker(local=False)

    def _create_collection(self, milvus_uri, db_name):
        """ Connect to standalone Milvus & create collection
        """
        # Connect to standalone Milvus server
        connected = False
        start_time = time.time()
        timeout = 300
        wait_sec = 5
        while not connected:
            try:
                connections.connect(uri=f'http://{milvus_uri}')
                connected = True
            except MilvusException:
                # Check for timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    logger.error(f"Timeout: {milvus_uri} not open after {elapsed_time} seconds")
                    raise TimeoutError

                # Wait a short period before trying again
                logger.warning(f"Waiting {wait_sec}s for Milvus at {milvus_uri}")
                time.sleep(wait_sec)

        # Drop old collection
        self.collection_name = f"{db_name}_Collection"
        utility.drop_collection(self.collection_name)

        # Define schema
        self.index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128, "nprobe": 8,},
        }
        reference_id = FieldSchema(
            name="reference_id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        source_id = FieldSchema(
            name="source_id",
            dtype=DataType.VARCHAR,
            default_value="Source ID Unknown",
            max_length=4096
        )
        text = FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            default_value="Text Unknown",
            max_length=4096
        )
        embedding = FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=1024
        )
        self.schema = CollectionSchema(
            fields=[reference_id, source_id, text, embedding],
            description="FM Radio Stream"
        )

        # Create collection
        self.collection = Collection(
            name=self.collection_name,
            schema=self.schema,
            using="default"
        )
        self.collection.create_index(
            field_name="embedding",
            index_params=self.index_params,
            index_name="embedding_index"
        )

    def add_docs(self, docs, source_id):
        """ Add documents to vector DB
        """
        for doc in docs:
            # Embed into Milvus database
            embedding = self._embed(doc, input_type="passage")
            result = self.collection.insert([[source_id], [doc], [embedding]])
            self.collection.load()
            logger.info(
                f"Embedded document {result.insert_count} to {self.collection_name}"
            )

    def _embed(self, doc, input_type="passage"):
        """ Use the NeMo Embedding microservice and store
        """
        if input_type == "passage":
            return self.embed_client.embed_documents([doc])[0]
        else:
            return self.embed_client.embed_query(doc)

    def _rerank_docs(self, docs, query):
        """ Use the NeMo Reranking microservice
        """
        rankings = self.rerank_client.compress_documents(
            query=query,
            documents=[Document(page_content=doc['entity']['text']) for doc in docs]
        )
        for i, rank in enumerate(rankings):
            docs[i]['relevance_score'] = rank.metadata['relevance_score']
        return sorted(docs, key=lambda doc: doc['relevance_score'], reverse=True)

    def _reformat(self, doc):
        return Document(
            page_content=doc['entity']['text'],
            metadata={
                'tstamp': None, #todo
                'source_id': doc['entity']['source_id']
            }
        )

    def _drop_outliers(self, docs, min_cv=0.1):
        """ Drop any documents that are not relevant enough
        """
        scores = [doc['relevance_score'] for doc in docs]
        low_rank_score = scores[0] - max(stdev(scores), min_cv * abs(mean(scores)))
        return list(filter(lambda doc: doc['relevance_score'] >= low_rank_score, docs))

    def search(self, query, max_entries=MAX_DOCS):
        # Do similarity search on Milvus DB
        search_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {
                "radius": 3.0,
                "range_filter": 0.0,
            },
        }
        self.collection.load()
        docs = self.client.search(
            data=[self._embed(query, input_type="query")],
            limit=max_entries,
            collection_name=self.collection_name,
            search_params=search_params,
            output_fields=["reference_id", "source_id", "text"]
        )[0]
        if len(docs) == 0:
            return []

        # Do reranking
        docs = self._rerank_docs(docs, query)
        if len(docs) > 5:
            docs = self._drop_outliers(docs)

        #todo Sort chronologically?
        return [self._reformat(doc) for doc in docs]