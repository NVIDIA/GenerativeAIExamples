<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Basic RAG Using LangChain

# What driver is “missing”?
1. You need the NVIDIA proprietary GPU driver on the host with CUDA 12.x support, plus the NVIDIA Container Toolkit.
2. Recommended driver branch: R550+ (or at least R535+) so it’s compatible with CUDA 12.x images used by Milvus GPU and NIM.
3. Also required: nvidia-container-toolkit configured with Docker so the nvidia runtime is available.
If you’re on WSL2/Windows: install the Windows NVIDIA driver with WSL2 GPU support and enable GPU for Docker Desktop/WSL. The error “WSL environment detected but no adapters were found” means no GPU is exposed to WSL/Docker.

# How to run without a local GPU (CPU-only path)
Option A: Use pgvector (CPU) instead of Milvus GPU and keep LLM/embeddings on NVIDIA AI Endpoints:
1. Set vector DB to pgvector:
  Override env: APP_VECTORSTORE_NAME=pgvector
2. Start only the pgvector service via profiles:
   export NVIDIA_API_KEY=YOUR_KEY   # required for NVIDIA AI Endpoints
   export APP_VECTORSTORE_NAME=pgvector
   docker compose --profile pgvector up -d --build
This avoids the Milvus GPU container entirely and uses CPU Postgres+pgvector.
Option B: Keep Milvus but switch to CPU image:
1. Edit RAG/examples/local_deploy/docker-compose-vectordb.yaml:
    - Change image: milvusdb/milvus:v2.4.15-gpu to milvusdb/milvus:v2.4.15
    - Remove the deploy.resources.reservations.devices block.
2. Then run docker compose up -d --build.
Don’t enable the NIM microservices profiles (local-nim, nemo-retriever) unless you have a GPU—they each reserve GPUs.

# If you do want local GPU
- Install an NVIDIA driver R550+ (or R535+) on the host; verify nvidia-smi works.
- Install and configure NVIDIA Container Toolkit:
  sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
- On WSL2, ensure the Windows NVIDIA driver with WSL support is installed and Docker Desktop has GPU enabled.

## Example Features

This example deploys a basic RAG pipeline for chat Q&A and serves inferencing from an NVIDIA API Catalog endpoint.
You do not need a GPU on your machine to run this example.

| Model                    | Embedding                | Framework | Vector Database | File Types   |
| ------------------------ | ------------------------ | --------- | --------------- | ------------ |
| meta/llama3-70b-instruct | nvidia/nv-embedqa-e5-v5 | LangChain | Milvus          | TXT, PDF, MD |

![Diagram](../../../../docs/images/basic_rag_langchain_arch.png)

## Prerequisites

Complete the [common prerequisites](../../../../docs/common-prerequisites.md).

## Build and Start the Containers

1. Export your NVIDIA API key as an environment variable:

   ```text
   export NVIDIA_API_KEY="nvapi-<...>"
   ```

1. Start the containers:

   ```console
   cd RAG/examples/basic_rag/langchain/
   docker compose up -d --build
   ```

   *Example Output*

   ```output
    ✔ Network nvidia-rag           Created
    ✔ Container rag-playground     Started
    ✔ Container milvus-minio       Started
    ✔ Container chain-server       Started
    ✔ Container milvus-etcd        Started
    ✔ Container milvus-standalone  Started
   ```

1. Confirm the containers are running:

   ```console
   docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   CONTAINER ID   NAMES               STATUS
   39a8524829da   rag-playground      Up 2 minutes
   bfbd0193dbd2   chain-server        Up 2 minutes
   ec02ff3cc58b   milvus-standalone   Up 3 minutes
   6969cf5b4342   milvus-minio        Up 3 minutes (healthy)
   57a068d62fbb   milvus-etcd         Up 3 minutes (healthy)
   ```

1. Open a web browser and access <http://localhost:8090> to use the RAG Playground.

   Refer to [Using the Sample Web Application](../../../../docs/using-sample-web-application.md)
   for information about uploading documents and using the web interface.

## Next Steps

- [Vector Database Customizations](../../../../docs/vector-database.md)
- Stop the containers by running `docker compose down`.
