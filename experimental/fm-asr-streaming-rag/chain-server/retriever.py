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
import requests
import json
import time

from common import get_logger, NVIDIA_API_KEY
from statistics import stdev, mean
from datetime import datetime

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

RETRIEVER_URI = os.environ.get('NEMO_RETRIEVER_URI', 'localhost:1984')
MILVUS_URI = os.environ.get('MILVUS_STANDALONE_URI', 'localhost:19530')
DEFAULT_DB_NAME = "FM_Radio_Stream"
EMBEDDING_ENDPOINT = "https://ai.api.nvidia.com/v1/retrieval/nvidia/embeddings"
RERANKING_ENDPOINT = "https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking"

class NemoRetrieverInterface:
    """ Uses NeMo Retriever microservice for embeddings / retrieval
    """
    def __init__(self, retriever_uri=RETRIEVER_URI):
        self.retriever_uri = retriever_uri

        # Connect to Retreiver Microservice
        connected = False
        start_time = time.time()
        timeout = 300
        wait_sec = 5
        while not connected:
            try:
                # Initialize collection and get ID
                response = requests.post(
                    f"http://{self.retriever_uri}/v1/collections",
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps({
                        'name': f'{DEFAULT_DB_NAME}_Collection',
                        'pipeline': 'ranked_hybrid'
                    })
                )
                response.raise_for_status()
                connected = True
            except requests.exceptions.ConnectionError:
                # Check for timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    logger.error(f"Timeout: {self.retriever_uri} not open after {elapsed_time} seconds")
                    raise TimeoutError

                # Wait a short period before trying again
                logger.warning(f"Waiting {wait_sec}s for Retriever MS at {self.retriever_uri}")
                time.sleep(wait_sec)
            except requests.HTTPError as e:
                logger.error(f"Error {e} when initializing collection at {self.retriever_uri}")
                return
            except requests.Timeout:
                logger.error(f"Timeout reached when initializing collection at {self.retriever_uri}")
                return

        self.collection = response.json()['collection']
        self.collection_url = f"http://{self.retriever_uri}/v1/collections/{self.collection['id']}"
        logger.info(f"Initialized collection {self.collection['id']}")

    def _reformat(self, doc):
        return Document(
            page_content=doc['content'],
            metadata={
                'tstamp': datetime.fromisoformat(doc['metadata']['_indexed_at']),
                'source_id': doc['metadata']['source_id']
            }
        )

    def _drop_outliers(self, docs, min_cv=0.1):
        """ Drop any documents that are not relevant enough
        """
        if self.collection["pipeline"] == "ranked_hybrid":
            # With reranking
            scores = [doc['score'] for doc in docs]
            low_rank_score = scores[0] - max(stdev(scores), min_cv * abs(mean(scores)))
            return list(filter(lambda doc: doc['score'] >= low_rank_score, docs))
        else:
            # Without reranking
            pass

    def add_docs(self, docs, source_id):
        """ Add documents to vector DB
        """
        for doc in docs:
            self._embed(doc, source_id)

    def _embed(self, doc, source_id):
        """ Use the NeMo Retriever Embedding microservice
        """
        try:
            response = requests.post(
                f"{self.collection_url}/documents",
                headers={'Content-Type': 'application/json'},
                data=json.dumps([{
                    "content": doc,
                    "format": "txt",
                    "metadata": {"source_id": source_id}
                }])
            )
            response.raise_for_status()
            logger.info(
                f"Embedded document {response.json()['documents'][0]['id']} "
                f"to {self.collection_url} [CODE {response.status_code}]"
            )
        except requests.HTTPError as e:
            logger.error(f"Error {e} when embedding to {self.collection_url}")
        except requests.Timeout:
            logger.error(f"Timeout reached when embedding to {self.collection_url}")

    def search(self, query, max_entries=None):
        """ Use the NeMo Retriever Embedding microservice
        """
        try:
            response = requests.post(
                f"{self.collection_url}/search",
                headers={'Content-Type': 'application/json'},
                data=json.dumps({"query": query})
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"Error {e} when embedding to {self.collection_url}")
            return None
        except requests.Timeout:
            logger.error(f"Timeout reached when embedding to {self.collection_url}")
            return None

        docs = response.json()["chunks"]
        logger.info(f"Retrieved {len(docs)} docs")
        if len(docs) == 0:
            return []

        if len(docs) > 1:
            docs = self._drop_outliers(docs)
        return [self._reformat(doc) for doc in docs[:max_entries]]

class NvidiaApiInterface:
    def __init__(self, milvus_uri=MILVUS_URI, db_name=DEFAULT_DB_NAME):
        self._create_collection(milvus_uri, db_name)
        self.client = MilvusClient(
            collection_name=self.collection_name,
            uri=f'http://{milvus_uri}',
            vector_field="embedding",
            overwrite=False
        )
        self.headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "application/json",
        }
        self.session = requests.Session()

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
        # Call embedding API endpoint
        try:
            response = self.session.post(
                EMBEDDING_ENDPOINT,
                headers=self.headers,
                json={
                    "input": doc,
                    "input_type": input_type,
                    "model": "NV-Embed-QA"
                }
            )
            response.raise_for_status()
            return response.json()['data'][0]['embedding']
        except requests.HTTPError as e:
            logger.error(f"Error {e} when embedding with API Endpoint")
        except requests.Timeout:
            logger.error(f"Timeout reached when embedding with API Endpoint")

    def _rerank_docs(self, docs, query):
        """ Use the NeMo Reranking microservice
        """
        # Call embedding API endpoint
        try:
            response = self.session.post(
                RERANKING_ENDPOINT,
                headers=self.headers,
                json={
                    "query": {"text": query},
                    "model": "nv-rerank-qa-mistral-4b:1",
                    "passages": [{"text": doc['entity']['text']} for doc in docs]
                }
            )
            response.raise_for_status()
            return response.json()['rankings']
        except requests.HTTPError as e:
            logger.error(f"Error {e} when embedding with API Endpoint")
        except requests.Timeout:
            logger.error(f"Timeout reached when embedding with API Endpoint")

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
        scores = [doc['logit'] for doc in docs]
        low_rank_score = scores[0] - max(stdev(scores), min_cv * abs(mean(scores)))
        return list(filter(lambda doc: doc['logit'] >= low_rank_score, docs))

    def search(self, query, max_entries=None):
        # Do similarity search on Milvus DB
        search_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {
                "radius": 1.0,
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
        rankings = self._rerank_docs(docs, query)
        for (rank, doc) in zip(rankings, docs):
            doc['logit'] = rank['logit']

        if len(docs) > 1:
            docs = self._drop_outliers(docs)
        return [self._reformat(doc) for doc in docs]