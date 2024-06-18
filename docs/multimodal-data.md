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

# Multimodal Data

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Example Features

This example deploys a developer RAG pipeline for chat Q&A and serves inferencing from NVIDIA API Catalog endpoints
instead of a local inference server, a local LLM, or local GPUs.

Developers get free credits for 10K requests to any of the available models.

The key difference from the [](./api-catalog.md) example is that this example demonstrates how work with multimodal data.
The model works with any kind of image in PDF or PPTX, such as graphs and plots, as well as text and tables.

This example uses models from the NVIDIA API Catalog.

```{list-table}
:header-rows: 1
:widths: 30 10 10 10 10 10 10 10 10

* - Model
  - Embedding
  - Framework
  - Description
  - Multi-GPU
  - TRT-LLM
  - Model Location
  - NIM for LLMs
  - Vector Database

* - meta/llama3-8b-instruct for response generation

    ai-google-Deplot for graph to text conversion

    ai-Neva-22B for image to text conversion
  - snowflake-arctic-embed-l
  - Custom Python
  - QA chatbot
  - NO
  - NO
  - API Catalog
  - NO
  - Milvus
```

The following figure shows the sample topology:

- The sample chat bot web application communicates with the chain server.
  The chain server sends inference requests to NVIDIA API Catalog endpoints.
- Optionally, you can deploy NVIDIA Riva. Riva can use automatic speech recognition to transcribe
  your questions and use text-to-speech to speak the answers aloud.

![Using NVIDIA API Catalog endpoints for inference instead of local components.](./images/catalog-and-vector-db.png)


## Limitations

Although the AI Foundation Models endpoint uses the Neva_22B model for processing images, this example
supports uploading images that are part of PDF and PPTX files only.
For example, after deploying the services, you cannot upload a PNG, JPEG, TIFF, or any other image format file.


## Prerequisites

- Clone the Generative AI examples Git repository using Git LFS:

  ```console
  $ sudo apt -y install git-lfs
  $ git clone git@github.com:NVIDIA/GenerativeAIExamples.git
  $ cd GenerativeAIExamples/
  $ git lfs pull
  ```

- Install Docker Engine and Docker Compose.
  Refer to the instructions for [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

- Login to Nvidia's docker registry. Please refer to [instructions](https://docs.nvidia.com/ngc/gpu-cloud/ngc-overview/index.html) to create account and generate NGC API key. This is needed for pulling in the secure base container used by all the examples.

  ```console
  $ docker login nvcr.io
  Username: $oauthtoken
  Password: <ngc-api-key>
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

## Get an API Key for the Meta Llama 3 8B Instruct API Endpoint

% api-key-start

Perform the following steps if you do not already have an API key.
You can use different model API endpoints with the same API key.

1. Navigate to <https://build.nvidia.com/explore/discover>.

2. Find the **Llama 3 8B Instruct** card and click the card.

   ![Llama 3 8B Instruct model card](./images/llama3-8b-instruct-model-card.png)

3. Click **Get API Key**.

   ![API section of the model page.](./images/llama3-8b-instruct-get-api-key.png)

4. Click **Generate Key**.

   ![Generate key window.](./images/api-catalog-generate-api-key.png)

5. Click **Copy Key** and then save the API key.
   The key begins with the letters nvapi-.

   ![Key Generated window.](./images/key-generated.png)

% api-key-end

## Build and Start the Containers

1. In the Generative AI examples repository, edit the `deploy/compose/compose.env` file.

   Add the API key for the model endpoint:

   ```text
   export NVIDIA_API_KEY="nvapi-..."
   ```

1. From the root of the repository, build the containers:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/rag-app-multimodal-chatbot.yaml build
   ```

1. Start the containers:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/rag-app-multimodal-chatbot.yaml up -d
   ```

   *Example Output*

   ```output
    ✔ Network nvidia-rag         Created
    ✔ Container chain-server     Started
    ✔ Container rag-playground   Started
   ```

1. Start the Milvus vector database:

   ```console
   $ docker compose \
       --env-file deploy/compose/compose.env \
       -f deploy/compose/docker-compose-vectordb.yaml \
       --profile llm-embedding \
       up -d milvus
   ```

   *Example Output*

   ```output
   ✔ Container milvus-minio       Started
   ✔ Container milvus-etcd        Started
   ✔ Container milvus-standalone  Started
   ```

1. Confirm the containers are running:

   ```console
   $ docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   CONTAINER ID   NAMES               STATUS
   37dcdb4ffcb0   rag-playground      Up 3 minutes
   39718f6a2a06   chain-server        Up 3 minutes
   68af1e4dfb44   milvus-standalone   Up 2 minutes
   522b12ec17f0   milvus-minio        Up 2 minutes (healthy)
   ed48988c5657   milvus-etcd         Up 2 minutes (healthy)
   ```

## Next Steps

- Access the web interface for the chat server.
  Refer to [](./using-sample-web-application.md) for information about using the web interface.
- Upload one or more PDF and PPTX files with graphics, plots, and tables.
- Enable the **Use knowledge base** checkbox when you submit a question.
- Stop the containers by running `docker compose -f deploy/compose/rag-app-multimodal-chatbot.yaml down` and
  `docker compose -f deploy/compose/docker-compose-vectordb.yaml --profile llm-embedding down`.
