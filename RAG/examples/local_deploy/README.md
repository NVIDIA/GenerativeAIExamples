<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# On Premises Deployment Using NVIDIA NIM microservices with GPUs

You can adapt any example to use on premises machines and NVIDIA NIM microservices.
By performing the additional prerequisites that are required to get access to the containers and use GPUs with Docker,
you can use local machines with GPUs and local microservices instead of NVIDIA API Catalog endpoints.

## Prerequisites

- You have an active subscription to an NVIDIA AI Enterprise product or you are an [NVIDIA Developer Program](https://developer.nvidia.com/developer-program) member.

- Complete the [common prerequisites](../../../docs/common-prerequisites.md).

  Ensure that you configure the host with the NVIDIA Container Toolkit.

- A host with at least two NVIDIA A100, H100, or L40S GPUs.

  You need at least one GPU for the inference container and one GPU for the embedding container.
  By default, Milvus requires one GPU as well.

- You have an NGC API key.
  Refer to [Generating NGC API Keys](https://docs.nvidia.com/ngc/gpu-cloud/ngc-user-guide/index.html#generating-api-key)
  in the _NVIDIA NGC User Guide_ for more information.

## Start the Containers

1. Export NGC related environment variables:

   ```text
   export NGC_API_KEY="M2..."
   ```

1. Create a directory to cache the models and export the path to the cache as an environment variable:

   ```console
   mkdir -p ~/.cache/model-cache
   export MODEL_DIRECTORY=~/.cache/model-cache
   ```

1. Export the connection information for the inference and embedding services:

   ```console
   export APP_LLM_SERVERURL="nemollm-inference:8000"
   export APP_EMBEDDINGS_SERVERURL="nemollm-embedding:8000"
   ```

1. Start the example-specific containers.

   Replace the path in the following `cd` command with the path to the example that you want to run.

   ```console
   cd RAG/examples/basic_rag/langchain
   USERID=$(id -u) docker compose --profile local-nim --profile milvus up -d --build
   ```

   *Example Output*

   ```output
   ✔ Container milvus-minio                           Running
   ✔ Container chain-server                           Running
   ✔ Container nemo-retriever-embedding-microservice  Started
   ✔ Container milvus-etcd                            Running
   ✔ Container nemollm-inference-microservice         Started
   ✔ Container rag-playground                         Started
   ✔ Container milvus-standalone                      Started
   ```

1. Optional: Deploy Reranking service if needed by your example. This is required currently for only the [Multi-Turn Rag Example](../advanced_rag/multi_turn_rag/).
     ```console
     export APP_RANKING_SERVERURL="ranking-ms:8000"
     cd RAG/examples/local_deploy
     USERID=$(id -u) docker compose -f docker-compose-nim-ms.yaml up -d ranking-ms
     ```

2. Open a web browser and access <http://localhost:8090> to use the RAG Playground.

   Refer to [Using the Sample Web Application](../../../docs/using-sample-web-application.md)
   for information about uploading documents and using the web interface.

## Tips for GPU Use

When you start the microservices in the `local_deploy` directory, you can specify the GPUs use by setting the following environment variables before you run `docker compose up`.

INFERENCE_GPU_COUNT:
  Specify the number of GPUs to use with the NVIDIA NIM for LLMs container.

EMBEDDING_MS_GPU_ID:
  Specify the GPU IDs to use with the NVIDIA NeMo Retriever Text Embedding NIM container.

RANKING_MS_GPU_ID:
  Specify the GPU IDs to use with the NVIDIA NeMo Retriever Text Reranking NIM container.

VECTORSTORE_GPU_DEVICE_ID:
  Specify the GPU IDs to use with Milvus.

## Related Information

- [*NVIDIA NIM for LLMs*](https://docs.nvidia.com/nim/large-language-models/latest/index.html)

The preceding document frequently demonstrates using the curl command to interact with the microservices.
You can determine the IP address for each container by running `docker network inspect nvidia-rag | jq '.[].Containers[] | {Name, IPv4Address}'`.

## Next Steps

- [Vector Database Customizations](../../../docs/vector-database.md)
- Stop the containers by running `docker compose --profile local-nim down`.
