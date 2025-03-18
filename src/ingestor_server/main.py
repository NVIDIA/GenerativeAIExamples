# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""
This is the Main module for RAG ingestion pipeline integration
"""
import os
import asyncio
from typing import (
    List,
    Dict,
    Union,
    Any
)
import logging
from uuid import uuid4
from overrides import overrides
from datetime import datetime
from pymilvus import utility, connections

from langchain_core.documents import Document

from .base import BaseIngestor
from src.utils import (
    get_config,
    get_vectorstore,
    get_embedding_model,
    get_docs_vectorstore_langchain,
    get_nv_ingest_client,
    get_nv_ingest_ingestor,
    del_docs_vectorstore_langchain,
    get_minio_operator,
    get_unique_thumbnail_id_collection_prefix,
    get_unique_thumbnail_id_file_name_prefix,
    get_unique_thumbnail_id,
    create_collections,
    get_collection,
    delete_collections,
    ENABLE_NV_INGEST_VDB_UPLOAD
)

# Initialize global objects
logger = logging.getLogger(__name__)

SETTINGS = get_config()
DOCUMENT_EMBEDDER = document_embedder = get_embedding_model(model=SETTINGS.embeddings.model_name, url=SETTINGS.embeddings.server_url)
NV_INGEST_CLIENT_INSTANCE = get_nv_ingest_client()
MINIO_OPERATOR = get_minio_operator()

class NVIngestIngestor(BaseIngestor):
    """
    Main Class for RAG ingestion pipeline integration for NV-Ingest
    """

    _config = get_config()
    _vdb_upload_bulk_size = 500

    @overrides
    async def ingest_docs(
        self,
        filepaths: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main function called by ingestor server to ingest
        the documents to vector-DB

        Arguments:
            - filepaths: List[str] - List of absolute filepaths
            - kwargs: Any - Metadata about the file paths
        """

        logger.info("Performing ingestion for filepaths: %s in collection_name: %s",
                    filepaths, kwargs.get("collection_name"))

        try:

            # Peform ingestion using nvingest

            # Check if the provided collection_name exists in vector-DB
            # Connect to Milvus to check for collection availability
            from urllib.parse import urlparse
            url = urlparse(kwargs.get("vdb_endpoint"))
            connection_alias = f"milvus_{url.hostname}_{url.port}"
            connections.connect(connection_alias, host=url.hostname, port=url.port)

            try:
                if not utility.has_collection(kwargs.get("collection_name"), using=connection_alias):
                    raise ValueError(f"Collection {kwargs.get('collection_name')} does not exist in {kwargs.get('vdb_endpoint')}. Ensure a collection is created using POST /collections endpoint first.")
            finally:
                connections.disconnect(connection_alias)

            await self._nv_ingest_ingestion(
                filepaths=filepaths,
                **kwargs
            )

            # Generate response dictionary
            uploaded_documents = [
                {
                    "document_id": str(uuid4()),  # Generate a document_id from filename
                    "document_name": os.path.basename(filepath),
                    "size_bytes": os.path.getsize(filepath)
                }
                for filepath in filepaths
            ]

             # Get current timestamp in ISO format
            timestamp = datetime.utcnow().isoformat()
            # TODO: Store document_id, timestamp and document size as metadata

            response_data = {
                "message": "Document upload job successfully completed.",
                "total_documents": len(filepaths),
                "documents": uploaded_documents
            }

            return response_data

        except Exception as e:
            logger.error("Ingestion failed due to error: %s", e)
            from traceback import print_exc
            print_exc()
            return {"message": f"Ingestion failed due to error: {e}", "total_documents": 0, "documents": []}


    @staticmethod
    def create_collections(
        collection_names: List[str], vdb_endpoint: str, embedding_dimension: int, collection_type: str
    ) -> str:
        """
        Main function called by ingestor server to create new collections in vector-DB
        """
        logger.info(f"Creating collections {collection_names} at {vdb_endpoint}")
        return create_collections(collection_names, vdb_endpoint, embedding_dimension, collection_type)


    @staticmethod
    def delete_collections(
        vdb_endpoint: str, collection_names: List[str],
    ) -> Dict[str, Any]:
        """
        Main function called by ingestor server to delete collections in vector-DB
        """
        logger.info(f"Deleting collections {collection_names} at {vdb_endpoint}")
        response = delete_collections(collection_names, vdb_endpoint)
        # Delete from Minio
        for collection in collection_names:
            collection_prefix = get_unique_thumbnail_id_collection_prefix(collection)
            delete_object_names = MINIO_OPERATOR.list_payloads(collection_prefix)
            MINIO_OPERATOR.delete_payloads(delete_object_names)
        return response


    @staticmethod
    def get_collections(vdb_endpoint: str) -> Dict[str, Any]:
        """
        Main function called by ingestor server to get all collections in vector-DB.

        Args:
            vdb_endpoint (str): The endpoint of the vector database.

        Returns:
            Dict[str, Any]: A dictionary containing the collection list, message, and total count.
        """
        try:
            logger.info(f"Getting collection list from {vdb_endpoint}")

            # Fetch collections from vector store
            collection_info = get_collection(vdb_endpoint)

            return {
                "message": "Collections listed successfully.",
                "collections": collection_info,
                "total_collections": len(collection_info)
            }

        except Exception as e:
            logger.error(f"Failed to retrieve collections: {e}")
            return {
                "message": f"Failed to retrieve collections due to error: {str(e)}",
                "collections": [],
                "total_collections": 0
            }


    @staticmethod
    def get_documents(collection_name: str, vdb_endpoint: str) -> Dict[str, Any]:
        """
        Retrieves filenames stored in the vector store.
        It's called when the GET endpoint of `/documents` API is invoked.

        Returns:
            Dict[str, Any]: Response containing a list of documents with metadata.
        """
        try:
            vs = get_vectorstore(DOCUMENT_EMBEDDER, collection_name, vdb_endpoint)
            if not vs:
                raise ValueError(f"Failed to get vectorstore instance for collection: {collection_name}. Please check if the collection exists in {vdb_endpoint}.")

            documents_list = get_docs_vectorstore_langchain(vs)

            # Generate response format
            documents = [
                {
                    "document_id": "",  # TODO - Use actual document_id
                    "document_name": os.path.basename(doc),  # Extract file name
                    "timestamp": "",  # TODO - Use actual timestamp
                    "size_bytes": 0  # TODO - Use actual size
                }
                for doc in documents_list
            ]

            return {
                "documents": documents,
                "total_documents": len(documents),
                "message": "Document listing successfully completed.",
            }

        except Exception as e:
            logger.exception(f"Failed to retrieve documents due to error {e}.")
            return {"documents": [], "total_documents": 0, "message": f"Document listing failed due to error {e}."}


    @staticmethod
    def delete_documents(document_names: List[str], document_ids: List[str], collection_name: str, vdb_endpoint: str) -> Dict[str, Any]:
        """Delete documents from the vector index.
        It's called when the DELETE endpoint of `/documents` API is invoked.

        Args:
            document_names (List[str]): List of filenames to be deleted from vectorstore.
            document_ids (List[str]): List of document IDs to be deleted from vectorstore.
            collection_name (str): Name of the collection to delete documents from.
            vdb_endpoint (str): Vector database endpoint.

        Returns:
            Dict[str, Any]: Response containing a list of deleted documents with metadata.
        """

        try:
            logger.info(f"Deleting documents {document_names} from collection {collection_name} at {vdb_endpoint}")

            # Get vectorstore instance
            vs = get_vectorstore(DOCUMENT_EMBEDDER, collection_name, vdb_endpoint)
            if not vs:
                raise ValueError(f"Failed to get vectorstore instance for collection: {collection_name}. Please check if the collection exists in {vdb_endpoint}.")

            if not len(document_names):
                raise ValueError("No document names provided for deletion. Please provide document names to delete.")

            # TODO: Delete based on document_ids if provided
            if del_docs_vectorstore_langchain(vs, document_names):
                # Generate response dictionary
                documents = [
                    {
                        "document_id": "",  # TODO - Use actual document_id
                        "document_name": doc,
                        "size_bytes": 0 # TODO - Use actual size
                    }
                    for doc in document_names
                ]
                # Delete from Minio
                for doc in document_names:
                    filename_prefix = get_unique_thumbnail_id_file_name_prefix(collection_name, doc)
                    delete_object_names = MINIO_OPERATOR.list_payloads(filename_prefix)
                    MINIO_OPERATOR.delete_payloads(delete_object_names)
                return {f"message": "Files deleted successfully", "total_documents": len(documents), "documents": documents}

        except Exception as e:
            return {f"message": f"Failed to delete files due to error: {e}", "total_documents": 0, "documents": []}

        return {f"message": "Failed to delete files due to error. Check logs for details.", "total_documents": 0, "documents": []}

    @staticmethod
    def _prepare_metadata(
        result_element: Dict[str, Union[str, dict]]
    ) -> Dict[str, str]:
        """
        Only used if ENABLE_NV_INGEST_VDB_UPLOAD=False
        Prepare metadata object w.r.t. to a single chunk

        Arguments:
            - result_element: Dict[str, Union[str, dict]]] - Result element for single chunk

        Returns:
            - metadata: Dict[str, str] - Dict of metadata for s single chunk
            {
                "source": "<filepath>",
                "chunk_type": "<chunk_type>", # ["text", "image", "table", "chart"]
                "source_name": "<filename>",
                "content": "<base64_str encoded content>" # Only for ["image", "table", "chart"]
            }
        """
        source_id = result_element.get("metadata").get("source_metadata").get("source_id")

        # Get chunk_type
        if result_element.get("document_type") == "structured":
            chunk_type = result_element.get("metadata").get("content_metadata").get("subtype")
        else:
            chunk_type = result_element.get("document_type")

        # Get base64_str encoded content, empty str in case of text
        content = result_element.get("metadata").get("content") if chunk_type != "text" else ""

        metadata = {
            "source": source_id, # Add filepath (Key-name same for backward compatibility)
            "chunk_type": chunk_type, # ["text", "image", "table", "chart"]
            "source_name": os.path.basename(source_id), # Add filename
            # "content": content # content encoded in base64_str format [Must not exceed 64KB]
        }
        return metadata

    def _prepare_langchain_documents(
        self,
        results: List[List[Dict[str, Union[str, dict]]]]
    ) -> List[Document]:
        """
        Only used if ENABLE_NV_INGEST_VDB_UPLOAD=False
        Prepare langchain documents based on the results obtained using nv-ingest

        Arguments:
            - results: List[List[Dict[str, Union[str, dict]]]] - Results obtained from nv-ingest

        Returns
            - List[Document] - List of langchain documents
        """
        documents = list()
        for result in results:
            for result_element in result:
                # Prepare metadata
                metadata = self._prepare_metadata(result_element=result_element)
                # Extract documents page_content and prepare docs
                page_content = None
                # For textual data
                if result_element.get("document_type") == "text":
                    page_content = result_element.get("metadata")\
                                                 .get("content")

                # For both tables and charts
                elif result_element.get("document_type") == "structured":
                    structured_page_content = result_element.get("metadata")\
                                                 .get("table_metadata")\
                                                 .get("table_content")
                    subtype = result_element.get("metadata").get("content_metadata").get("subtype")
                    # Check for tables
                    if subtype == "table" and self._config.nv_ingest.extract_tables:
                        page_content = structured_page_content
                    # Check for charts
                    elif subtype == "chart" and self._config.nv_ingest.extract_charts:
                        page_content = structured_page_content

                # For image captions
                elif result_element.get("document_type") == "image" and self._config.nv_ingest.extract_images:
                    page_content = result_element.get("metadata")\
                                                 .get("image_metadata")\
                                                 .get("caption")
                # Add doc to list
                if page_content:
                    documents.append(
                        Document(
                            page_content=page_content, metadata=metadata
                        )
                    )
        return documents

    def _add_documents_to_vectorstore(
        self,
        documents: List[Document],
        collection_name: str,
        vdb_endpoint: str
    ) -> None:
        """
        Only used if ENABLE_NV_INGEST_VDB_UPLOAD=False
        Add langchain documents to vectorstore

        Arguments:
            - documents: List[Document] - List of langchain documents
            - collection_name: str - VectorDB collection name
        """
        vs = get_vectorstore(DOCUMENT_EMBEDDER, collection_name, vdb_endpoint)
        for i in range(0, len(documents), self._vdb_upload_bulk_size):
            sub_documents = documents[i:i+self._vdb_upload_bulk_size]
            # Add documents to vectorstore
            vs.add_documents(sub_documents)

    @staticmethod
    def _put_content_to_minio(
        results: List[List[Dict[str, Union[str, dict]]]],
        collection_name: str,
    ) -> None:
        """
        Put nv-ingest image/table/chart content to minio
        """
        if not os.getenv("ENABLE_CITATIONS", "True") in ["True", "true"]:
            logger.info(f"Skipping minio insertion for collection: {collection_name}")
            return # Don't perform minio insertion if captioning is disabled

        for result in results:
            for result_element in result:
                if result_element.get("document_type") in ["image", "structured"]:
                    # Pull content from result_element
                    content = result_element.get("metadata").get("content")
                    file_name = os.path.basename(result_element.get("metadata").get("source_metadata").get("source_id"))
                    page_number = result_element.get("metadata").get("content_metadata").get("page_number")
                    location = result_element.get("metadata").get("content_metadata").get("location")

                    if location is not None:
                        # Get unique_thumbnail_id
                        unique_thumbnail_id = get_unique_thumbnail_id(
                            collection_name=collection_name,
                            file_name=file_name,
                            page_number=page_number,
                            location=location
                        )
                        # Put payload to minio
                        MINIO_OPERATOR.put_payload(
                            payload={"content": content},
                            object_name=unique_thumbnail_id
                        )

    async def _nv_ingest_ingestion(
        self,
        filepaths: List[str],
        **kwargs
    ) -> None:
        """
        This methods performs following steps:
        - Perform extraction and splitting using NV-ingest ingestor
        - Prepare langchain documents from the nv-ingest results
        - Embeds and add documents to Vectorstore collection

        Arguments:
            - filepaths: List[str] - List of absolute filepaths
            - kwargs: Any - Metadata about the file paths
        """
        nv_ingest_ingestor = get_nv_ingest_ingestor(
            nv_ingest_client_instance=NV_INGEST_CLIENT_INSTANCE,
            filepaths=filepaths,
            **kwargs
        )
        logger.info(f"Performing ingestion with parameters: {kwargs}")
        results = await asyncio.to_thread(nv_ingest_ingestor.ingest)
        logger.debug("NV-ingest Job for collection_name: %s is complete!", kwargs.get("collection_name"))

        if not results:
            error_message = "NV-Ingest ingestion failed with no results. Please check the ingestor-server microservice logs for more details."
            logger.error(error_message)
            raise Exception(error_message)

        self._put_content_to_minio(
            results=results,
            collection_name=kwargs.get("collection_name")
        )

        if not ENABLE_NV_INGEST_VDB_UPLOAD:
            logger.debug("Performing embedding and vector DB upload")

            # Prepare the documents for nv-ingest results
            documents = self._prepare_langchain_documents(results)

            # Add all documents to VectorStore
            self._add_documents_to_vectorstore(
                documents=documents,
                collection_name=kwargs.get("collection_name"),
                vdb_endpoint=kwargs.get("vdb_endpoint")
            )
            logger.debug("Vector DB upload complete to: %s in collection %s", kwargs.get("vdb_endpoint"), kwargs.get("collection_name"))