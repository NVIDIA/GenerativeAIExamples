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

# Creating an LLM Chain

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Implementing the Method

1. Edit the `RetrievalAugmentedGeneration/examples/simple_rag_api_catalog/chains.py` file and add the following `import` statements:

   ```{literalinclude} ./simple-example/code/api-catalog/llm/chains.py
   :language: python
   :start-after: start-llm-imports
   :end-before: end-llm-imports
   ```

1. Update the `llm_chain` method with the following statements:

   ```{literalinclude} ./simple-example/code/api-catalog/llm/chains.py
   :language: python
   :start-after: start-llm-chain-method
   :end-before: end-llm-chain-method
   ```

## Building and Running with Docker Compose

<!-- cp docs/simple-example/code/api-catalog/llm/chains.py RetrievalAugmentedGeneration/examples/simple_rag_api_catalog/chains.py -->

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

## Verify the LLM Chain Method Using Curl

You can access the Chain Server with a URL like <http://localhost:8081>.

- Confirm the `llm_chain` method runs by submitting a query:

  ```console
  $ curl -H "Content-Type: application/json" http://localhost:8081/generate \
      -d '{"messages":[{"role":"user", "content":"What should I see in Paris?"}], "use_knowledge_base": false}'
  ```

  *Example Output*

  ```{literalinclude} ./simple-example/output/api-catalog/llm/response.json
  ```

## Next Steps

- [](./rag-api-catalog.md)
- You can stop the containers by running the `docker compose -f deploy/compose/simple-rag-api-catalog.yaml down` command.
