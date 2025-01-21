<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customize Your Vector Database

By default, the Docker Compose files for the examples deploy [Milvus](https://milvus.io/) as the vector database with CPU-only support.
You must install the NVIDIA Container Toolkit to use Milvus with GPU acceleration. 
You can also extend the code to add support for any vector store. 

- [Configure Milvus with GPU Acceleration](#configure-milvus-with-gpu-acceleration)
- [Configure Support for an External Milvus Database](#configure-support-for-an-external-milvus-database)
- [Add a Custom Vector Store](#add-a-custom-vector-store)



## Configure Milvus with GPU Acceleration

Use the following procedure to configure Milvus with GPU Acceleration.

1. In the `deploy/vectordb.yaml` file, change the image tag to include the `-gpu` suffix.

   ```yaml
   milvus:
     container_name: milvus-standalone
     image: milvusdb/milvus:v2.4.4-gpu
     ...
   ```

1. In the `deploy/vectordb.yaml` file, add the GPU resource reservation.

   ```yaml
   ...
   depends_on:
     - "etcd"
     - "minio"
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             capabilities: ["gpu"]
             device_ids: ['${VECTORSTORE_GPU_DEVICE_ID:-0}']
   profiles: ["nemo-retriever", "milvus", ""]
   ```


## Configure Support for an External Milvus Database

Use the following procedure to add support for an external Milvus database.

1. In the `docker-compose.yaml` file, remove or comment-out the `include` path to the `vectordb.yaml` file:

   ```yaml
   include:
     - path:
       # - ./vectordb.yaml
       - ./nims.yaml
   ```

1. In the `docker-compose.yaml` file, specify the connection information.

   ```yaml
   environment:
     APP_VECTORSTORE_URL: "http://<milvus-hostname-or-ipaddress>:19530"
     APP_VECTORSTORE_NAME: "milvus"
     ...
   ```

1. Restart the containers.



## Add a Custom Vector Store

Use the following procedure to extend the code to add support for any vector store.

1. Navigate to the file `src/utils.py` in the project's root directory.

1. Modify the `create_vectorstore_langchain` function to handle your new vector store. Implement the logic for creating your vector store object within it.

   ```python
   def create_vectorstore_langchain(document_embedder, collection_name: str = "") -> VectorStore:
      # existing code
      elif config.vector_store.name == "chromadb":
         from langchain_chroma import Chroma
         import chromadb

         logger.info(f"Using Chroma collection: {collection_name}")
         persistent_client = chromadb.PersistentClient()
         vectorstore = Chroma(
            client=persistent_client,
            collection_name=collection_name,
            embedding_function=document_embedder,
         )
   ```

1. Update the `get_docs_vectorstore_langchain` function to retrieve a list of documents from your new vector store. Implement your retrieval logic within it.

   ```python
   def get_docs_vectorstore_langchain(vectorstore: VectorStore) -> List[str]:
      # Existing code
      elif  settings.vector_store.name == "chromadb":
         chroma_data = vectorstore.get()
         filenames = set([extract_filename(metadata) for metadata in chroma_data.get("metadatas", [])])
         return filenames
   ```

1. Update the `del_docs_vectorstore_langchain` function to handle document deletion in your new vector store.

   ```python
   def del_docs_vectorstore_langchain(vectorstore: VectorStore, filenames: List[str]) -> bool:
      # Existing code
      elif  settings.vector_store.name == "chromadb":
         chroma_data = vectorstore.get()
         for filename in filenames:
               ids_list = [chroma_data.get("ids")[idx] for idx, metadata in enumerate(chroma_data.get("metadatas", [])) if extract_filename(metadata) == filename]
               vectorstore.delete(ids_list)
         return True
   ```

1. In your `chains.py` implementation, import the preceding functions from `utils.py`. The sample `chains.py` already imports the functions.

   ```python
   from .utils import (
      create_vectorstore_langchain,
      get_docs_vectorstore_langchain,
      del_docs_vectorstore_langchain,
      get_vectorstore
   )
   ```

1. Update `requirements.txt` and add any additional packages that the vector store requires.

   ```text
   # existing dependency
   langchain-chroma
   ```

1. Navigate to the root directory.

1. Set the `APP_VECTORSTORE_NAME` environment variable for the `rag-server` microservice. Set it to the name of your newly added vector store.

   ```yaml
   export APP_VECTORSTORE_NAME: "chromadb"
   ```

1. Build and deploy the microservices.

   ```console
   docker compose -f deploy/compose/docker-compose.yaml up -d --build
   ```
