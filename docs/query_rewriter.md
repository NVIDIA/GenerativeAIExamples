<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Enable query rewriting support
Query rewriting enables higher accuracy for multiturn queries by making an additional LLM call to decontextualize the incoming question, before sending it to the retrieval pipeline.

Once you have followed [steps in quick start guide](./quickstart.md#deploy-with-docker-compose) to launch the blueprint, to enable query rewriting support, developers have two options:

- [Enable query rewriting support](#enable-query-rewriting-support)
  - [Using on-prem model (Recommended)](#using-on-prem-model-recommended)
  - [Using cloud hosted model](#using-cloud-hosted-model)


## Using on-prem model (Recommended)
1. Deploy the `llama3.1-8b-instruct` model on-prem. You need a H100 or A100 GPU to deploy this model.
   ```bash
   export LLM_8B_MS_GPU_ID=<AVAILABLE_GPU_ID>
   docker compose -f deploy/compose/nims.yaml --profile llama-8b up -d
   ```

2. Make sure the nim-llm container is up and in healthy state before proceeding further
   ```bash
   docker ps --filter "name=nim-llm-llama-8b" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   NAMES                                   STATUS
   nim-llm-llama-8b                     Up 38 minutes (healthy)
   ```

3. Enable query rewriting
   Export the below environment variable and relaunch the rag-server container.
   ```bash
   export APP_QUERYREWRITER_SERVERURL="nim-llm-llama-8b:8000"
   export ENABLE_QUERYREWRITER="True"
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

   Alternatively, you can enable this at runtime during retrieval by setting `enable_query_rewriting: True` as part of the schema of POST /generate API, without relaunching the containers. Refer to the [retrieval notebook](../notebooks/retriever_api_usage.ipynb).


## Using cloud hosted model
1. Set the server url to empty string to point towards cloud hosted model
   ```bash
   export APP_QUERYREWRITER_SERVERURL=""
   ```

2. Relaunch the rag-server container by enabling query rewriter.
   ```bash
   export ENABLE_QUERYREWRITER="True"
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

[!TIP]: You can change the model name and model endpoint in case of an externally hosted LLM model by setting these two environment variables and restarting the rag services
```bash
export APP_QUERYREWRITER_SERVERURL="<llm_nim_http_endpoint_url>"
export APP_QUERYREWRITER_MODELNAME="<model_name>"
```