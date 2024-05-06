<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Configuring an Alternative Vector Database

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Supported Vector Databases

By default, the Docker Compose files for the examples deploy Milvus as the vector database.
Alternatively, you can deploy pgvector.

## Configuring pgvector as the Vector Database

1. Edit the Docker Compose file for the example, such as `deploy/compose/rag-app-text-chatbot.yaml`.

   Update the environment variables within the chain server service:

   ```yaml
   services:
     chain-server:
       container_name: chain-server
       environment:
         APP_VECTORSTORE_NAME: "pgvector"
         APP_VECTORSTORE_URL: "pgvector:5432"
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
         POSTGRES_USER: ${POSTGRES_USER:-postgres}
         POSTGRES_DB: ${POSTGRES_DB:-api}
    ```

    The preceding example shows the default values for the database user, password, and database.
    To override the defaults, edit the values in the Docker Compose file, or set the values in the `compose.env` file.

    `Note`: If you have existing setup remove `deploy/compose/volumes` directory to avoid pgvector crash. 

1. Optional: If a container for a vector database is running, stop the container:

   ```console
   $ docker compose -f deploy/compose/docker-compose-vectordb.yaml down
   ```

1. Stop and then start the services:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/<rag-example>.yaml down
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/<rag-example>.yaml up -d --remove-orphans
   ```

1. Start the pgvector container:

   ```console
   $ docker compose -f deploy/compose/docker-compose-vectordb.yaml up -d pgvector
   ```

1. Optional: View the chain server logs to confirm the vector database.

   1. View the logs:

      ```console
      $ docker logs -f chain-server
      ```

   1. Upload a document to the knowledge base.
      Refer to [](./using-sample-web-application.md#use-unstructured-documents-as-a-knowledge-base) for more information.

   1. Confirm the log output includes the vector database:

      ```output
      INFO:example:Ingesting <file-name>.pdf in vectorDB
      INFO:RetrievalAugmentedGeneration.common.utils:Using pgvector as vector store
      INFO:RetrievalAugmentedGeneration.common.utils:Using PGVector collection: <example-name>
      ```

## Configuring Milvus as the Vector Database

1. Edit the Docker Compose file for the example, such as `deploy/compose/rag-app-text-chatbot.yaml`.

   Update the environment variables within the chain server service:

   ```yaml
   services:
     chain-server:
       container_name: chain-server
       environment:
         APP_VECTORSTORE_NAME: "milvus"
         APP_VECTORSTORE_URL: "http://milvus:19530"
    ```

1. Optional: If a container for a vector database is running, stop the container:

   ```console
   $ docker compose -f deploy/compose/docker-compose-vectordb.yaml down
   ```

1. Stop and then start the services:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/<rag-example>.yaml down
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/<rag-example>.yaml up -d --remove-orphans
   ```

1. Start the Milvus container:

   ```console
   $ docker compose -f deploy/compose/docker-compose-vectordb.yaml up -d milvus
   ```

1. Optional: View the chain server logs to confirm the vector database.

   1. View the logs:

      ```console
      $ docker logs -f chain-server
      ```

   1. Upload a document to the knowledge base.
      Refer to [](./using-sample-web-application.md#use-unstructured-documents-as-a-knowledge-base) for more information.

   1. Confirm the log output includes the vector database:

      ```output
      INFO:example:Ingesting <file-name>.pdf in vectorDB
      INFO:RetrievalAugmentedGeneration.common.utils:Using milvus as vector store
      INFO:RetrievalAugmentedGeneration.common.utils:Using milvus collection: <example-name>
      ```
