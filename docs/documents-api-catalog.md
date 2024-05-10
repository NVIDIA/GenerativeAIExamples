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

# Listing and Searching Documents

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Implementing the Method

- Edit the `RetrievalAugmentedGeneration/examples/simple_rag_api_catalog/chains.py` file and add the following statements after the `import` statements.

  - Replace the `document_search` method with the following code:


    ```{literalinclude} ./simple-example/code/api-catalog/documents/chains.py
    :language: python
    :start-after: start-document-search-method
    :end-before: end-document-search-method
    ```

  - Replace the `get_documents` method with the following code:

    ```{literalinclude} ./simple-example/code/api-catalog/documents/chains.py
    :language: python
    :start-after: start-get-documents-method
    :end-before: end-get-documents-method
    ```

  - Replace the `delete_documents` method with the following code:

    ```{literalinclude} ./simple-example/code/api-catalog/documents/chains.py
    :language: python
    :start-after: start-delete-documents-method
    :end-before: end-delete-documents-method
    ```

## Building and Running with Docker Compose

<!-- cp docs/simple-example/code/api-catalog/documents/chains.py RetrievalAugmentedGeneration/examples/simple_rag_api_catalog/chains.py -->

Using the containers has one additional step this time: exporting your NVIDIA API key as an environment variable.

1. Build the container for the Chain Server:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/simple-rag-api-catalog.yaml build chain-server
   ```

1. Export your NVIDIA API key in an environment variable:

   ```console
   $ export NVIDIA_API_KEY=nvapi-...
   ```

1. Run the containers:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/simple-rag-api-catalog.yaml up -d
   ```

## Verify the Ingest Docs Method Using Curl

You can access the Chain Server with a URL like <http://localhost:8081>.

- Upload the README from the repository:

  ```console
  $ curl http://localhost:8081/documents -F "file=@README.md"
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/documents/ingest-docs.json
  :language: json
  ```

- List the ingested documents:

  ```console
  $ curl -X GET http://localhost:8081/documents
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/documents/get-documents.json
  :language: json
  ```

- Submit a query to search the documents:

  ```console
  $ curl -H "Content-Type: application/json" \
      http://localhost:8081/search \
      -d '{"query":"Does NVIDIA have sample RAG code?", "top_k":1}'
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/documents/document-search.json
  :language: json
  ```

- Confirm that the search returns relevant documents:

  ```console
  $ curl -H "Content-Type: application/json" \
      http://localhost:8081/search \
      -d '{"query":"Is vanilla ice cream better than chocolate ice cream?", "top_k":1}'
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/documents/ice-cream.json
  :language: json
  ```

- Confirm the delete method works:

  ```console
  $ curl -X DELETE http://localhost:8081/documents\?filename\=README.md
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/documents/delete-documents.json
  :language: json
  ```

## Next Steps

- [](./llm-api-catalog.md)
- You can stop the containers by running the `docker compose -f deploy/compose/simple-rag-api-catalog.yaml down` command.
