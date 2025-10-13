<!--
  SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Vector Database Customization
<!-- TOC -->

* [Available Vector Databases](#available-vector-databases)
* [Configuring Milvus with GPU Acceleration](#configuring-milvus-with-gpu-acceleration)
* [Configuring pgvector as the Vector Database](#configuring-pgvector-as-the-vector-database)
* [Configuring Support for an External Milvus or pgvector database](#configuring-support-for-an-external-milvus-or-pgvector-database)
* [Adding a New Vector Store](#adding-a-new-vector-store)
    * [LlamaIndex Framework](#llamaindex-framework)
    * [LangChain Framework](#langchain-framework)

<!-- /TOC -->

## Available Vector Databases

By default, the Docker Compose files for the examples deploy Milvus as the vector database with CPU-only support.
You must install the NVIDIA Container Toolkit to use Milvus with GPU acceleration.

The available vector databases in the examples are shown in the following list:

- LlamaIndex: Milvus, pgvector
- LangChain: FAISS, Milvus, pgvector

The following customizations are common:

- Use Milvus with GPU acceleration.
- Use pgvector as an alternative to Milvus.
  pgvector uses CPU only.
- Use your own vector database and prevent deploying a vector database with each RAG example.

## Configuring Milvus with GPU Acceleration

1. Edit the `RAG/examples/local_deploy/docker-compose-vectordb.yaml` file and make the following changes to the Milvus service.

   - Change the image tag to include the `-gpu` suffix:

     ```yaml
     milvus:
       container_name: milvus-standalone
       image: milvusdb/milvus:v2.4.5-gpu
       ...
     ```

   - Add the GPU resource reservation:

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

1. Stop and start the containers:

   ```console
   docker compose down
   docker compose up -d --build
   ```

   Note: when deploying milvus with `local-nim` you have to use `milvus` profile to deploy the vectorstore
   ```
   docker compose --profile local-nim --profile milvus up -d --build
   ```

1. Optional: View the chain server logs to confirm the vector database is operational.

   1. View the logs:

      ```console
      docker logs -f chain-server
      ```

   1. Upload a document to the knowledge base.
      Refer to [Use Unstructured Documents as a Knowledge Base](./using-sample-web-application.md#use-unstructured-documents-as-a-knowledge-base) for more information.

   1. Confirm the log output includes the vector database:

      ```output
      INFO:RAG.src.chain_server.utils:Using milvus collection: nvidia_api_catalog
      INFO:RAG.src.chain_server.utils:Vector store created and saved.
      ```

## Configuring pgvector as the Vector Database

1. Export the following environment variables in your terminal:

   ```console
   export POSTGRES_PASSWORD=password
   export POSTGRES_USER=postgres
   export POSTGRES_DB=api
   ```

1. Edit the `docker-compose.yaml` file for the RAG example and set the following environment variables for the Chain Server:

   ```yaml
   environment:
     APP_VECTORSTORE_URL: "pgvector:5432"
     APP_VECTORSTORE_NAME: "pgvector"
     POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
     POSTGRES_USER: ${POSTGRES_USER:-postgres}
     POSTGRES_DB: ${POSTGRES_DB:-api}
     ...
   ```

1. Start the containers:

   ```console
   docker compose --profile pgvector up -d --build
   ```

1. Optional: View the chain server logs to confirm the vector database is operational.

   1. View the logs:

      ```console
      docker logs -f chain-server
      ```

   1. Upload a document to the knowledge base.
      Refer to [Use Unstructured Documents as a Knowledge Base](./using-sample-web-application.md#use-unstructured-documents-as-a-knowledge-base) for more information.

   1. Confirm the log output includes the vector database:

      ```output
      INFO:RAG.src.chain_server.utils:Using PGVector collection: nvidia_api_catalog
      INFO:RAG.src.chain_server.utils:Vector store created and saved.
      ```

To stop pgvector and the other containers run `docker compose --profile pgvector down`.

## Configuring Support for an External Milvus or pgvector database

1. Edit the `docker-compose.yaml` file for the RAG example and make the following edits.

   - Remove or comment the `include` path to the `docker-compose-vectordb.yaml` file:

     ```yaml
     include:
       - path:
         # - ../../local_deploy/docker-compose-vectordb.yaml
         - ../../local_deploy/docker-compose-nim-ms.yaml
     ```

   - To use an external Milvus server, specify the connection information:

     ```yaml
     environment:
       APP_VECTORSTORE_URL: "http://<milvus-hostname-or-ipaddress>:19530"
       APP_VECTORSTORE_NAME: "milvus"
       ...
     ```

   - To use an external pgvector server, specify the connection information:

     ```yaml
     environment:
       APP_VECTORSTORE_URL: "<pgvector-hostname-or-ipaddress>:5432"
       APP_VECTORSTORE_NAME: "pgvector"
       ...
     ```

     Also export the `POSTGRES_PASSWORD`, `POSTGRES_USER`, and `POSTGRES_DB` environment variables in your terminal.

1. Start the containers:

   ```console
   docker compose up -d --build
   ```

## Adding a New Vector Store

You can extend the code to add support for any vector store.

### LlamaIndex Framework

1. Navigate to the file `RAG/src/chain_server/utils.py` from the project's root directory. This file contains the utility functions used for vector store interactions.

2. Modify the `get_vector_index` function to handle your new vector store. Implement the logic for creating your vector store object within this function.

   ```python
   def get_vector_index():
      # existing code
      elif config.vector_store.name == "chromadb":
         import chromadb
         from llama_index.vector_stores.chroma import ChromaVectorStore

         if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
         logger.info(f"Using Chroma collection: {collection_name}")
         chroma_client = chromadb.EphemeralClient()
         chroma_collection = chroma_client.create_collection(collection_name)
         vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
   ```

3. Modify the `get_docs_vectorstore_llamaindex` function to retrieve the list of files stored in your new vector store.

   ```python
   def get_docs_vectorstore_llamaindex():
      # existing code
      elif settings.vector_store.name == "chromadb":
         ref_doc_info = index.ref_doc_info
         # iterate over all the document in vectorstore and return unique filename
         for _ , ref_doc_value in ref_doc_info.items():
               metadata = ref_doc_value.metadata
               if 'filename' in metadata:
                  filename = metadata['filename']
                  decoded_filenames.append(filename)
         decoded_filenames = list(set(decoded_filenames))
   ```

4. Update the `del_docs_vectorstore_llamaindex` function to handle document deletion in your new vector store.

   ```python
   def del_docs_vectorstore_llamaindex(filenames: List[str]):
      # existing code
      elif settings.vector_store.name == "chromadb":
         ref_doc_info = index.ref_doc_info
         # Iterate over all the filenames and if filename present in metadata of doc delete it
         for filename in filenames:
               for ref_doc_id, doc_info in ref_doc_info.items():
                  if 'filename' in doc_info.metadata and doc_info.metadata['filename'] == filename:
                     index.delete_ref_doc(ref_doc_id, delete_from_docstore=True)
                     logger.info(f"Deleted documents with filenames {filename}")
   ```

5. In your custom `chains.py` implementation, import the functions from `utils.py`.
   The sample `chains.py` in `RAG/examples/basic_rag/llamaindex` already imports the functions.

   ```python
   from RAG.src.chain_server.utils import (
       get_vector_index,
       get_docs_vectorstore_llamaindex,
       del_docs_vectorstore_llamaindex,
   )
   ```

6. Update `RAG/src/chain_server/requirements.txt` with any additional package required for the vector store.

   ```text
   # existing dependency
   llama-index-vector-stores-chroma
   ```

7. Build and start the containers.

   1. Navigate to the example directory.

      ```console
      cd RAG/examples/basic_rag/llamaindex
      ```

   1. Set the `APP_VECTORSTORE_NAME` environment variable for the `chain-server` microservice in your `docker-compose.yaml` file.
      Set it to the name of your newly added vector store.

      ```yaml
      APP_VECTORSTORE_NAME: "chromadb"
      ```

   1. Build and deploy the microservice.

      ```console
      docker compose up -d --build chain-server rag-playground
      ```

### LangChain Framework

1. Navigate to the file `RAG/src/chain_server/utils.py` in the project's root directory.

2. Modify the `create_vectorstore_langchain` function to handle your new vector store. Implement the logic for creating your vector store object within it.

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

3. Update the `get_docs_vectorstore_langchain` function to retrieve a list of documents from your new vector store. Implement your retrieval logic within it.

   ```python
   def get_docs_vectorstore_langchain(vectorstore: VectorStore) -> List[str]:
      # Existing code
      elif  settings.vector_store.name == "chromadb":
         chroma_data = vectorstore.get()
         filenames = set([extract_filename(metadata) for metadata in chroma_data.get("metadatas", [])])
         return filenames
   ```

4. Update the `del_docs_vectorstore_langchain` function to handle document deletion in your new vector store.

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

5. In your custom `chains.py` implementation, import the preceding functions from `utils.py`.
   The sample `chains.py` in `RAG/examples/basic_rag/langchain` already imports the functions.

   ```python
   from RAG.src.chain_server.utils import (
      create_vectorstore_langchain, 
      get_docs_vectorstore_langchain, 
      del_docs_vectorstore_langchain, 
      get_vectorstore
   )
   ```

6. Update `RAG/src/chain_server/requirements.txt` with any additional package required for the vector store.

   ```text
   # existing dependency
   langchain-core==0.1.40 # Update this dependency as there is conflict with existing one
   langchain-chroma
   ```

7. Build and start the containers.

   1. Navigate to the example directory.

      ```console
      cd RAG/examples/basic_rag/langchain
      ```

   1. Set the `APP_VECTORSTORE_NAME` environment variable for the `chain-server` microservice in your `docker-compose.yaml` file.
      Set it to the name of your newly added vector store.

      ```yaml
      APP_VECTORSTORE_NAME: "chromadb"
      ```

   1. Build and deploy the microservices.

      ```console
      docker compose up -d --build chain-server rag-playground
      ```
