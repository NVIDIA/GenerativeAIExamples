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

# Software Component Configuration

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Configuration with the Docker Compose Environment File

The following sections identify the environment variables and parameters that are used in the `rag-app-text-chatbot.yaml` Docker Compose file in the `deploy/compose` directory of the repository.

You can set environment variables in the `deploy/compose/compose.env` file.

### LLM Server Configuration

LLM Inference server hosts the Large Language Model (LLM) with Triton Inference Server backend.

You can configure the server using the following environment variables:

:MODEL_DIRECTORY: Specifies the path to the model directory where model checkpoints are stored.
:MODEL_ARCHITECTURE: Defines the architecture of the model used for deployment.
:MODEL_MAX_INPUT_LENGTH: Maximum allowed input length, with a default value of 3000.
:QUANTIZATION: Specifies to enable activation-aware quantization for the LLM. By default, quantization is not enabled.
:INFERENCE_GPU_COUNT: Specifies the GPUs to be used by Triton for model deployment, with the default setting being "all."

### Milvus

Milvus is the default vector database server.
You can configure Milvus using the following environment variable:

:DOCKER_VOLUME_DIRECTORY: Specifies the location of the volume mount on the host for the vector database files.
  The default value is `./volumes/milvus` in the current working directory.

### Pgvector

Pgvector is an alternative vector database server.
You can configure pgvector using the following environment variables:

:DOCKER_VOLUME_DIRECTORY: Specifies the location of the volume mount on the host for the vector database files.
  The default value is `./volumes/data` in the current working directory.
:POSTGRES_PASSWORD: Specifies the password for authenticating to pgvector.
  The default value is `password`.
:POSTGRES_USER: Specifies the user name for authenticating to pgvector.
  The default value is `postgres`.
:POSTGRES_DB: Specifies the name of the database instance.
  The default value is `api`.


### Chain Server

The chain server is the core component that interacts with the LLM Inference Server and the Milvus server to obtain responses.
You can configure the server using the following environment variable:

:APP_VECTORSTORE_URL: Specifies the URL of the vector database server.
:APP_VECTORSTORE_NAME: Specifies the vendor name of the vector database. Values are `milvus` or `pgvector`.
:COLLECTION_NAME: Specifies the example-specific collection in the vector database.
:APP_LLM_SERVERURL: Specifies the URL of Triton Inference Server.
:APP_LLM_MODELNAME: The model name used by the Triton server.
:APP_LLM_MODELENGINE: An enum that specifies the backend name hosting the model. Supported values are as follows:

  `triton-trt-llm` to use locally deployed LLM models.

  `nv-ai-foundation` to use models hosted from NVIDIA AI Endpoints.

  `nv-api-catalog` to use models hosted from NVIDIA API Catalog.
:APP_RETRIEVER_TOPK: Number of relevant results to retrieve. The default value is `4`.
:APP_RETRIEVER_SCORETHRESHOLD: The minimum confidence score for the retrieved values to be considered. The default value is `0.25`.
:APP_PROMPTS_CHATTEMPLATE: Specifies the instructions to provide to the model.
  The prompt is combined with the user-supplied query and then presented to the model.
  The chain server uses this prompt when the query does not use a knowledge base.
:APP_PROMPTS_RAGTEMPLATE: Specifies the instructions to provide to the model.
  The prompt is combined with the user-supplied query and then presented to the model.
  The chain server uses this prompt when the query uses a knowledge base.


### RAG Playground

The RAG playground component is the user interface web application that interacts with the chain server to retrieve responses and provide a user interface to upload documents.
You can configure the server using the following environment variables:

:APP_SERVERURL: Specifies the URL for the chain server.
:APP_SERVERPORT: Specifies the network port number for the chain server.
:APP_MODELNAME: Specifies the name of the large language model used in the deployment.
  This information is for display purposes only and does not affect the inference process.
:RIVA_API_URI: Specifies the host name and port of the NVIDIA Riva server.
  This field is optional and provides automatic speech recognition (ASR) and text-to-speech (TTS) functionality.
:RIVA_API_KEY: Specifies a key to access the Riva API.
  This field is optional.
:RIVA_FUNCTION_ID: Specifies the function ID to access the Riva API.
  This field is optional.
:TTS_SAMPLE_RATE: Specifies the sample rate in hertz (Hz).
  The default value is `48000`.
