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

# Using NVIDIA NIM for LLMs

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Running Examples on NIM for LLMs

NVIDIA NIM for LLMs provides the enterprise-ready approach for deploying large language models (LLMs).

If you are approved for [early access to NVIDIA NeMo Microservices](https://developer.nvidia.com/nemo-microservices), you can run the examples with NIM for LLMs.


## Prerequisites

- You have early access to NVIDIA NeMo Microservices.
- Clone the Generative AI examples Git repository using Git LFS:

  ```console
  $ sudo apt -y install git-lfs
  $ git clone git@github.com:NVIDIA/GenerativeAIExamples.git
  $ cd GenerativeAIExamples/
  $ git lfs pull
  ```

- A host with an NVIDIA A100, H100, or L40S GPU.

- Verify NVIDIA GPU driver version 535 or later is installed and that the GPU is in compute mode:

  ```console
  $ nvidia-smi -q -d compute
  ```

  *Example Output*

  ```{code-block} output
  ---
  emphasize-lines: 4,9
  ---
  ==============NVSMI LOG==============

  Timestamp                                 : Sun Nov 26 21:17:25 2023
  Driver Version                            : 535.129.03
  CUDA Version                              : 12.2

  Attached GPUs                             : 1
  GPU 00000000:CA:00.0
      Compute Mode                          : Default
  ```

  If the driver is not installed or below version 535, refer to the [*NVIDIA Driver Installation Quickstart Guide*](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html).

- Install Docker Engine and Docker Compose.
  Refer to the instructions for [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

- Install the NVIDIA Container Toolkit.

  1. Refer to the [installation documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

  1. When you configure the runtime, set the NVIDIA runtime as the default:

     ```console
     $ sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
     ```

     If you did not set the runtime as the default, you can reconfigure the runtime by running the preceding command.

  1. Verify the NVIDIA container toolkit is installed and configured as the default container runtime:

     ```console
     $ cat /etc/docker/daemon.json
     ```

     *Example Output*

     ```json
     {
         "default-runtime": "nvidia",
         "runtimes": {
             "nvidia": {
                 "args": [],
                 "path": "nvidia-container-runtime"
             }
         }
     }
     ```

   1. Run the `nvidia-smi` command in a container to verify the configuration:

      ```console
      $ sudo docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi -L
      ```

      *Example Output*

      ```output
      GPU 0: NVIDIA A100 80GB PCIe (UUID: GPU-d8ce95c1-12f7-3174-6395-e573163a2ace)
      ```

- Optional: Enable NVIDIA Riva automatic speech recognition (ASR) and text to speech (TTS).

  - To launch a Riva server locally, refer to the [Riva Quick Start Guide](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/quick-start-guide.html).

    - In the provided `config.sh` script, set `service_enabled_asr=true` and `service_enabled_tts=true`, and select the desired ASR and TTS languages by adding the appropriate language codes to `asr_language_code` and `tts_language_code`.

    - After the server is running, assign its IP address (or hostname) and port (50051 by default) to `RIVA_API_URI` in `deploy/compose/compose.env`.

  - Alternatively, you can use a hosted Riva API endpoint. You might need to obtain an API key and/or Function ID for access.

    In `deploy/compose/compose.env`, make the following assignments as necessary:

    ```bash
    export RIVA_API_URI="<riva-api-address/hostname>:<port>"
    export RIVA_API_KEY="<riva-api-key>"
    export RIVA_FUNCTION_ID="<riva-function-id>"
    ```


## Deploy NIM for LLMs and NeMo Retriever Embedding

- Deploy an LLM with NIM for LLMs, such as Llama-2-13b-chat-hf or Mixtral 8x7b Instruct.
  Refer to the [Llama 2 70B Chat](https://docs.nvidia.com/ai-enterprise/nim-llm/latest/quickstart/llama2-70b-chat.html) quick start, or another quick start in the _NVIDIA NIM for LLMs_ documentation.

- Deploy a text embedding model, such as NV-Embed-QA.
  Refer to [Deploying Text Embedding Models](https://developer.nvidia.com/docs/nemo-microservices/embedding/source/deploy.html)
  in the _NVIDIA NeMo Retriever Embedding_ documentation.


## Build and Start the Chain Server and RAG Playground

1. In the Generative AI Examples repository, edit the `deploy/compose/compose.env` file.

   Add the following environment variables.

   ```bash
   # Name of the deployed LLM model.
   export APP_LLM_MODELNAME=<inference-model-name>

   export APP_LLM_MODELENGINE=nvidia-ai-endpoints

   # IP of system where llm is deployed.
   export APP_LLM_SERVERURL="<ip-address>:<port>"

   # Name of the deployed embedding model (NV-Embed-QA)
   export APP_EMBEDDINGS_MODELNAME=<embedding-model-name>

   export APP_EMBEDDINGS_MODELENGINE=nvidia-ai-endpoints
   # IP of system where embedding model is deployed.
   export APP_EMBEDDINGS_SERVERURL="<ip-address>:<port>"
   ...
   ```

1. From the root of the repository, build the containers:

   ```console
   $ docker compose \
       --env-file deploy/compose/compose.env \
       -f deploy/compose/rag-app-text-chatbot.yaml \
       build chain-server rag-playground
   ```

   You can specify a different Docker Compose file, such as `deploy/compose/rag-app-multiturn-chatbot.yaml`.

1. Start the Chain Server and RAG Playground:

   ```console
   $ docker compose \
       --env-file deploy/compose/compose.env \
       -f deploy/compose/rag-app-text-chatbot.yaml \
       up -d --no-deps chain-server rag-playground
   ```

   The `-d` argument starts the services in the background and the `--no-deps` argument avoids starting a second inference server.

   `Note`: To avoid memory issues, deploy the chain server on a separate GPU from the LLM. Update `device_ids` in `chain-server` service of `deploy/compose/rag-app-text-chatbot.yaml` (or relevant Docker Compose file) to specify a different GPU
   ```yaml
        deploy:
          resources:
            reservations:
              devices:
                - driver: nvidia
                  device_ids: ['<free-gpu-id>']
                  capabilities: [gpu]
   ```

1. Start the Milvus vector database:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/docker-compose-vectordb.yaml up -d milvus
   ```
   `Note`: To avoid memory issues, deploy the milvus on a separate GPU from the LLM. Update `VECTORSTORE_GPU_DEVICE_ID` in `deploy/compose/compose.env`
   ```console
   export VECTORSTORE_GPU_DEVICE_ID=<free-gpu-id>
   ```

1. Confirm the containers are running:

   ```console
   $ docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   CONTAINER ID   NAMES                  STATUS
   256da0ecdb7b   rag-playground         Up About an hour
   2974aa4fb2ce   chain-server           Up About an hour
   f96712f57ff8   <nim-llms>             Up About an hour
   5e1cf74192d6   <embedding-ms>         Up About an hour
   5be2b57bb5c1   milvus-standalone      Up About an hour
   a6609c22c171   milvus-minio           Up About an hour
   b23c0858c4d4   milvus-etcd            Up About an hour
   ```


## Stopping the Containers

1. Stop the vector database:

   ```console
   $ docker compose -f deploy/compose/docker-compose-vectordb.yaml down
   ```

1. Stop and remove the application containers:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/rag-app-text-chatbot.yaml down
   ```

1. Stop the NIM for LLMs container and NeMo Retriever Embedding container by pressing Ctrl+C in each terminal.


## Next Steps

- Use the [](./using-sample-web-application.md).
- [](./vector-database.md)
