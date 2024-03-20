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

# NeMo Framework Inference Server

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## About the Inference Server

The generative AI examples use [NeMo Framework Inference Server](https://docs.nvidia.com/nemo-framework/user-guide/latest/index.html) container.
NeMo can create optimized LLM using TensorRT-LLM and can deploy models using NVIDIA Triton Inference Server for high-performance, cost-effective, and low-latency inference.
Many examples use Llama 2 models and LLM Inference Server container contains modules and scripts that are required for TRT-LLM conversion of the Llama 2 models and deployment using NVIDIA Triton Inference Server.

The inference server is used with examples that deploy a model on-premises.
The examples that use [NVIDIA AI foundation models](https://www.nvidia.com/en-in/ai-data-science/foundation-models/) or NVIDIA AI Endpoints do not use this component.


## Running the Inference Server Individually

The following steps describe how a Llama 2 model deployment.

- Download Llama 2 Chat Model Weights from [Meta](https://ai.meta.com/resources/models-and-libraries/llama-downloads/) or [HuggingFace](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf/). You can check [support matrix](support-matrix.md) for GPU requirements for the deployment.

- Update the `deploy/compose/compose.env` file with `MODEL_DIRECTORY` as the downloaded Llama 2 model path and other model parameters as needed.

- Build the LLM inference server container from source:

  ```console
  $ source deploy/compose/compose.env
  $ docker compose -f deploy/compose/rag-app-text-chatbot.yaml build llm
  ```

- Run the container. The container starts Triton Inference Server with TRT-LLM optimized Llama 2 model:

  ```console
  $ source deploy/compose/compose.env
  $ docker compose -f deploy/compose/rag-app-text-chatbot.yaml up llm
  ```

After the optimized Llama 2 model is deployed in Triton Inference Server, clients can send HTTP/REST or gRPC requests directly to the server.
A sample implementation of a client can be found in the `triton_trt_llm.py` file of GitHub repository at [integrations/langchain/llms/](https://github.com/NVIDIA/GenerativeAIExamples/tree/main/integrations/langchain/llms).
