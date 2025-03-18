<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Enable text only ingestion support
For ingesting text only files, developers do not need to deploy the complete pipeline with all NIMs connected. In case your usecase requires extracting text from files, follow steps below to deploy just the necassary components.

1. Follow steps outlined in the [quickstart guide](quickstart.md#start-using-on-prem-models) till step 3.

2. While deploying the NIMs in step 4, selectively deploy just the NIMs necessary for rag-server and the page-elements NIM for ingestion.

   ```bash
   USERID=$(id -u) docker compose --profile rag -f deploy/compose/nims.yaml up -d
   ```

   ```bash
   USERID=$(id -u) docker compose -f deploy/compose/nims.yaml up page-elements -d
   ```

   Confirm all the below mentioned NIMs are running and the one's specified below are in healthy state before proceeding further. Make sure to allocate GPUs according to your hardware (2xH100 or 4xA100 to `nim-llm-ms` based on your deployment GPU profile) as stated in the quickstart guide.

   ```bash
   watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
   ```

   ```output
      NAMES                                   STATUS

      nemoretriever-ranking-ms                Up 14 minutes (healthy)
      nemoretriever-embedding-ms              Up 14 minutes (healthy)
      nim-llm-ms                              Up 14 minutes (healthy)
      compose-page-elements-1                 Up 14 minutes
   ```

3. Continue following the rest of steps in quickstart to deploy the ingestion-server and rag-server containers.

4. Once the ingestion and rag servers are deployed, open the [ingestion notebook](../notebooks/ingestion_api_usage.ipynb) and follow the steps. While trying out the the `Upload Document Endpoint` set the payload to below. We are setting `extract_tables`, `extract_charts` to `False`.
   ```bash
       data = {
        "vdb_endpoint": "http://milvus:19530",
        "collection_name": collection_name,
        "extraction_options": {
            "extract_text": True,
            "extract_tables": False,
            "extract_charts": False,
            "extract_images": False,
            "extract_method": "pdfium",
            "text_depth": "page",
        },
        "split_options": {
            "chunk_size": 1024,
            "chunk_overlap": 150
        }
    }
   ```

5. After ingestion completes, you can try out the queries relevant to the text in the documents using [retrieval notebook](../notebooks/retriever_api_usage.ipynb).

**📝 Note:**
In case you are [interacting with cloud hosted models](quickstart.md#start-using-nvidia-hosted-models) and want to enable text only mode, then in step 2, just export these specific environment variables as shown below:
   ```bash
   export APP_EMBEDDINGS_SERVERURL=""
   export APP_LLM_SERVERURL=""
   export APP_RANKING_SERVERURL=""
   export EMBEDDING_NIM_ENDPOINT="https://integrate.api.nvidia.com/v1"
   export YOLOX_HTTP_ENDPOINT="https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-page-elements-v2"
   export YOLOX_INFER_PROTOCOL="http"
   ```