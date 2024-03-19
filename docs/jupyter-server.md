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

- [LLM Streaming Client](../../notebooks/01-llm-streaming-client.ipynb)

  This notebook demonstrates how to use a client to stream responses from an LLM deployed to NVIDIA Triton Inference Server with NVIDIA TensorRT-LLM (TRT-LLM). This deployment format optimizes the model for low latency and high throughput inference.

- [Document Question-Answering with LangChain](../../notebooks/02_langchain_simple.ipynb)

  This notebook demonstrates how to use LangChain to build a chat bot that references a custom knowledge base. LangChain provides a simple framework for connecting LLMs to your own data sources. It shows how to integrate a TensorRT-LLM to LangChain using a custom wrapper.

- [Document Question-Answering with LlamaIndex](../../notebooks/03_llama_index_simple.ipynb)

  This notebook demonstrates how to use LlamaIndex to build a chat bot that references a custom knowledge base. It contains the same functionality as the preceding notebook, but uses some LlamaIndex components instead of LangChain components. It also shows how the two frameworks can be used together.

- [Advanced Document Question-Answering with LlamaIndex](../../notebooks/04_llamaindex_hier_node_parser.ipynb)

  This notebook demonstrates how to use LlamaIndex to build a more complex retrieval for a chat bot. The retrieval method shown in this notebook works well for code documentation. The method retrieves more contiguous document blocks that preserve both code snippets and explanations of code.

- [Upload Press Releases and Interact with REST FastAPI Server](../../notebooks/05_dataloader.ipynb)

  This notebook demonstrates how to use the REST FastAPI server to upload the knowledge base and then ask a question without and with the knowledge base.

- [NVIDIA AI Endpoint Integration with LangChain](../../notebooks/07_Option(1)_NVIDIA_AI_endpoint_simple.ipynb)

  This notebook demonstrates how to build a Retrieval Augmented Generation (RAG) example using the NVIDIA AI endpoint integrated with Langchain, with FAISS as the vector store.

- [RAG with LangChain and local LLM model](../../notebooks/07_Option(2)_minimalistic_RAG_with_langchain_local_HF_LLM.ipynb)

  This notebook demonstrates how to plug in a local LLM from Hugging Face Hub and build a simple RAG app using LangChain.

- [NVIDIA AI Endpoint with LlamaIndex and LangChain](../../notebooks/08_Option(1)_llama_index_with_NVIDIA_AI_endpoint.ipynb)

  This notebook demonstrates how to plug in an NVIDIA AI Endpoint mixtral_8x7b and embedding nvolveqa_40k, bind these into LlamaIndex with these customizations.

- [Locally deployed model from Hugging Face integration with LlamaIndex and LangChain](../../notebooks/08_Option(2)_llama_index_with_HF_local_LLM.ipynb)

  This notebook demonstrates how to plug in a local LLM from Hugging Face Hub Llama-2-13b-chat-hf and all-MiniLM-L6-v2 embedding from Hugging Face, bind these to into LlamaIndex with these customizations.

- [LangChain agent with tools plug in multiple models from  NVIDIA AI Endpoints](../../notebooks/09_Agent_use_tools_leveraging_NVIDIA_AI_endpoints.ipynb)

  This notebook demonstrates how to use multiple NVIDIA AI Endpoint models such as mixtral_8x7b, Deplot, and Neva.

- [LangChain with HTML documents and NVIDIA AI Endpoints](../../notebooks/10_RAG_for_HTML_docs_with_Langchain_NVIDIA_AI_Endpoints.html)

  This notebook demonstrates how to build a RAG using NVIDIA AI Endpoints for LangChain.
  The notebook creates a vector store by downloading web pages and generating their embeddings using FAISS.
  The notebook shows two different chat chains for querying the vector store.



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
