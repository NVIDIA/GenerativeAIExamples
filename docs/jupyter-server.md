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

# Jupyter Notebook Server

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## About the Notebooks

The Jupyter notebooks provide guidance to building knowledge-augmented chat bots.

The following Jupyter notebooks are provided with the AI workflow for the default canonical RAG example:

- [Upload Press Releases and Interact with REST FastAPI Server](../../notebooks/01_dataloader.ipynb)

  This notebook demonstrates how to use the REST FastAPI server to upload the knowledge base and then ask a question without and with the knowledge base.

- [NVIDIA AI Endpoint Integration with LangChain](../../notebooks/02_Option(1)_NVIDIA_AI_endpoint_simple.ipynb)

  This notebook demonstrates how to build a Retrieval Augmented Generation (RAG) example using the NVIDIA AI endpoint integrated with Langchain, with FAISS as the vector store.

- [RAG with LangChain and local LLM model](../../notebooks/02_Option(2)_minimalistic_RAG_with_langchain_local_HF_LLM.ipynb)

  This notebook demonstrates how to plug in a local LLM from Hugging Face Hub and build a simple RAG app using LangChain.

- [NVIDIA AI Endpoint with LlamaIndex and LangChain](../../notebooks/03_Option(1)_llama_index_with_NVIDIA_AI_endpoint.ipynb)

  This notebook demonstrates how to plug in an NVIDIA AI Endpoint ai-mixtral-8x7b-instruct and embedding ai-embed-qa-4, bind these into LlamaIndex with these customizations.

- [Locally deployed model from Hugging Face integration with LlamaIndex and LangChain](../../notebooks/03_Option(2)_llama_index_with_HF_local_LLM.ipynb)

  This notebook demonstrates how to plug in a local LLM from Hugging Face Hub Llama-2-13b-chat-hf and all-MiniLM-L6-v2 embedding from Hugging Face, bind these to into LlamaIndex with these customizations.

- [LangChain agent with tools plug in multiple models from  NVIDIA AI Endpoints](../../notebooks/04_Agent_use_tools_leveraging_NVIDIA_AI_endpoints.ipynb)

  This notebook demonstrates how to use multiple NVIDIA AI Endpoint models such as ai-mixtral-8x7b-instruct, Deplot, and Neva.

- [LangChain with HTML documents and NVIDIA AI Endpoints](../../notebooks/05_RAG_for_HTML_docs_with_Langchain_NVIDIA_AI_Endpoints.ipynb)

  This notebook demonstrates how to build a RAG using NVIDIA AI Endpoints for LangChain.
  The notebook creates a vector store by downloading web pages and generating their embeddings using FAISS.
  The notebook shows two different chat chains for querying the vector store.

- [LangChain with HTML documents and NVIDIA AI Endpoints](../../notebooks/06_LangGraph_HandlingAgent_IntermediateSteps.ipynb)

  This notebook guides you through creating a basic agent executor using LangGraph. We demonstrate how to handle the logic of the intermediate steps from the agent leveraging different provided tools within langGraph.


- [LangChain with HTML documents and NVIDIA AI Endpoints](../../notebooks/07_Chat_with_nvidia_financial_reports.ipynb)

  In this notebook, we are going to use milvus as vectorstore, the ai-mixtral-8x7b-instruct as LLM and ai-embed-qa-4 embedding provided by NVIDIA_AI_Endpoint as LLM and embedding model, and build a simply RAG example for chatting with NVIDIA Financial Reports.

- [RAG with locally deployed models using NIMS](../../notebooks/08_RAG_Langchain_with_Local_NIM.ipynb)

  In this notebook we demonstrate how to build a RAG using [NVIDIA Inference Microservices (NIM)](https://build.nvidia.com/explore/discover). We locally host a `Llama3-8b-instruct` using the NIM LLM container and deploy it using [ NVIDIA AI Endpoints for LangChain](https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints/).
  In order to run this notebook in a virtual environment, you need to launch the NIM Docker container in the background outside of the notebook environment prior to running the LangChain code in the notebook cells. Run the commands in the first 3 cells from a terminal then begin with the 4th cell (curl inference command) within the notebook environment.


## Running JupyterLab Server Individually

To run the JupyterLab server for development purposes, run the following commands:

- Optional: Notebooks 7 to 9 require GPUs.
  If you have a GPU and want to run one of these notebooks, update the jupyter-server service in the Docker Compose file to use `./notebooks/Dockerfile.gpu_notebook` as the Dockerfile:

  ```yaml
  jupyter-server:
    container_name: notebook-server
    image: notebook-server:latest
    build:
      context: ../../
      dockerfile: ./notebooks/Dockerfile.gpu_notebook
  ```

  These notebooks can use more than one GPU.
  To use more than one, specify the GPU IDs in the `device_ids` field or specify `count: all`

  ```yaml
  jupyter-server:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0', '1']
              capabilities: [gpu]
  ```

- Build the container from source:

  ```console
  $ source deploy/compose/compose.env
  $ docker compose -f deploy/compose/rag-app-text-chatbot.yaml build jupyter-server
  ```

- Start the container which starts the notebook server:

  ```console
  $ source deploy/compose/compose.env
  $ docker compose -f deploy/compose/rag-app-text-chatbot.yaml up jupyter-server
  ```

- Open the JupyterLab server at ``http://host-ip:8888``
