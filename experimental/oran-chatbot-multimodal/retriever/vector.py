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

from abc import ABC, abstractmethod
from typing import Any
import os

from pydantic import BaseModel
from qdrant_client import QdrantClient
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from qdrant_client.http.models import PointStruct, VectorParams, Distance

class VectorClient(ABC, BaseModel):

    hostname : str
    port : str
    collection_name : str

    @abstractmethod
    def connect(self):
        ...

    def disconnect(self):
        ...

    @abstractmethod
    def search(self, query_vectors, limit=5):
        ...

    @abstractmethod
    def update(self):
        ...


class MilvusVectorClient(VectorClient):

    hostname : str = "localhost"
    port : str = "19530"
    metric_type : str = "L2"
    index_type : str = "IVF_FLAT"
    nlist : int = 100
    index_field_name : str = "embedding"
    nprobe : int = 5
    vector_db : Any = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vector_db = self.connect(self.collection_name, self.hostname, self.port)
        self._create_index(self.metric_type, self.index_type, self.index_field_name, self.nlist)
        self.vector_db.load()

    def _create_index(self, metric_type, index_type, field_name, nlist=100):

        index_params = {
            "metric_type": metric_type,  # or "IP" depending on your requirement
            "index_type": index_type,  # You can choose other types like IVF_PQ based on your need
            "params": {"nlist": nlist}  # Adjust the nlist parameter as per your requirements
        }
        self.vector_db.create_index(field_name=field_name, index_params=index_params)

    def connect(self, collection_name, hostname, port, alias="default"):
        connections.connect(alias, host=hostname, port=port)
        try:
            vector_db = Collection(name=collection_name)
            return vector_db
        except:
            # create the vector DB using default embedding dimensions of 1024
            vector_db = self.create_collection(collection_name, embedding_size=1024)
            return self.vector_db

    def disconnect(self, alias="default"):
        connections.disconnect(alias)

    def search(self, query_vectors, limit=5):
        search_params = {
            "metric_type": self.metric_type,
            "params": {"nprobe": self.nprobe}
        }

        search_results = self.vector_db.search(
            data=query_vectors,
            anns_field=self.index_field_name,  # Replace with your vector field name
            param=search_params,
            output_fields=["content", "metadata"],
            limit=limit
        )
        concatdocs = ""
        sources = {}
        # return concatdocs, sources
        print("Number of results: ", len(search_results[0]))
        for idx, result in enumerate(search_results[0]):
            hit = result
            doc_content = hit.entity.get("content")
            doc_metadata = hit.entity.get("metadata")
            print(doc_metadata)
            # Storing metadata and content in sources dictionary
            sources[doc_metadata["source"]] = {"doc_content": doc_content, "doc_metadata": doc_metadata}

            # # Concatenating document content with an identifier
            concatdocs += f"[[DOCUMENT {idx}]]\n\n" + doc_content + "\n\n"

        # Note: The return statement should be outside the for loop
        return concatdocs, sources

    def __del__(self):
        self.disconnect()

    def update(self, documents, embeddings, collection_name):
         # Processing each document
        insert_data = []
        for i, doc in enumerate(documents):
            # Prepare data for insertion
            example = {
                "id": i,
                "content": doc.page_content,
                "embedding": embeddings[i],
                "metadata": doc.metadata
            }
            insert_data.append(example)

        self.vector_db.insert(insert_data)

    def get_schema(self, embedding_size):
        # Define the primary key field along with other fields
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),  # Primary key field
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10000),  # Text field with up to 10000 characters
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_size),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]

        schema = CollectionSchema(fields, "Collection for storing document embeddings and metadata")
        return schema

    def create_collection(self, collection_name, embedding_size):
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)

        schema = self.get_schema(embedding_size)
        self.vector_db = Collection(name=collection_name, schema=schema)

class QdrantVectorClient(VectorClient):
    hostname : str = "localhost"
    port : int = 6333
    vector_db : Any = None


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vector_db = self.connect(self.hostname, self.port)

    def connect(self, hostname, port):
        client = QdrantClient(host=hostname, port=port)
        return client

    def search(self, query_vectors, limit=5):

        search_results = self.vector_db.search(
            collection_name=self.collection_name,
            query_vector=query_vectors,
            query_filter=None,
            limit=limit
                )

        # Perform a similarity search in the Qdrant collection
        concatdocs = ""
        sources = {}
        print("Number of results: ", len(search_results))
        idx = 0
        for result in search_results:
            idx += 1
            doc_content = result.payload["content"]
            doc_metadata = result.payload["metadata"]

            # print(doc_metadata)
            sources[doc_metadata["source"]] = {"doc_content": doc_content, "doc_metadata": doc_metadata}
            concatdocs += f"[[DOCUMENT {idx}]]\n\n" + doc_content + "\n\n"

        return concatdocs, sources

    def disconnect(self):
        self.vector_db.close()

    def update(self, documents, embeddings, collection_name):
        current_source = None
        for i, doc in enumerate(documents):
            if doc.metadata['source'] != current_source:
                current_source = doc.metadata['source']
            doc_id = os.path.splitext(os.path.basename(doc.metadata["source"]))[0]
            if "page_num" in doc.metadata:
                doc_id += "_page" + str(doc.metadata["page_num"])

            payload = {
                "content": doc.page_content,
                "metadata": doc.metadata
            }

            self.vector_db.upsert(
                collection_name=collection_name,
                wait=True,
                points=[PointStruct(id=i, vector=embeddings[i], payload=payload)]
            )
            print(f"Added document {doc_id} to the collection.")


    def create_collection(self, collection_name, embedding_size):
        try:
             self.vector_db.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE)
            )
        except Exception as e:
            if "already exists" in str(e):
                print(f"Collection {collection_name} already exists. Skipping creation.")
            else:
                raise
