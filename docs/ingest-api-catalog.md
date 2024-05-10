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

# Implementing the Ingest Docs Method

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Implementing the Method

1. Edit the `RetrievalAugmentedGeneration/examples/simple_rag_api_catalog/chains.py` file and add the following statements after the `import` statements.

   The following statements use the FAISS vector store for the embeddings that the NVIDIA API Catalog model creates.

   ```{literalinclude} ./simple-example/code/api-catalog/ingest/chains.py
   :language: python
   :start-after: start-ingest-faiss
   :end-before: end-ingest-faiss
   ```

1. Add the import statements for libraries:

   ```{literalinclude} ./simple-example/code/api-catalog/ingest/chains.py
   :language: python
   :start-after: start-ingest-imports
   :end-before: end-ingest-imports
   ```

1. Update the `ingest_docs` method with the following statements:

   ```{literalinclude} ./simple-example/code/api-catalog/ingest/chains.py
   :language: python
   :start-after: start-ingest-docs-method
   :end-before: end-ingest-docs-method
   ```

## Building and Running with Docker Compose

<!-- cp docs/simple-example/code/api-catalog/ingest/chains.py RetrievalAugmentedGeneration/examples/simple_rag_api_catalog/chains.py -->

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

- Confirm the `ingest_docs` method runs by uploading a sample document, such as the README from the repository:

  ```console
  $ curl http://localhost:8081/documents -F "file=@README.md"
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/boilerplate/ingest-docs.json
  :language: json
  ```

  View the logs for the Chain Server to see the logged message from the method:

  ```console
  $ docker logs chain-server
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/ingest/chain-server.log
  :language: output
  ```

## Next Steps

- [](./documents-api-catalog.md)
- You can stop the containers by running the `docker compose -f deploy/compose/simple-rag-api-catalog.yaml down` command.
