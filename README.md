<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

![](docs/images/apps-catalog-promo-web-banner-laptop-300@2x.jpg)

# NVIDIA Generative AI Examples

This repository is a starting point for developers looking to integrate with the NVIDIA software ecosystem to speed up their generative AI systems. Whether you are building RAG pipelines, agentic workflows, or fine-tuning models, this repository will help you integrate NVIDIA, seamlessly and natively, with your development stack.

## Table of Contents
<!-- TOC -->

* [What's New?](#whats-new)
  * [Knowledge Graph RAG](#knowledge-graph-rag)
  * [Agentic Workflows with Llama 3.1](#agentic-workflows-with-llama-31)
  * [RAG with Local NIM Deployment and LangChain](#rag-with-local-nim-deployment-and-langchain)
  * [Vision NIM Workflows](#vision-nim-workflows)
* [Try it Now!](#try-it-now)
* [RAG](#rag)
  * [RAG Notebooks](#rag-notebooks)
  * [RAG Examples](#rag-examples)
  * [RAG Tools](#rag-tools)
  * [RAG Projects](#rag-projects)
* [Documentation](#documentation)
  * [Getting Started](#getting-started)
  * [How To's](#how-tos)
  * [Reference](#reference)
* [Community](#community)

<!-- /TOC -->

## What's New?

### Knowledge Graph RAG

This example implements a GPU-accelerated pipeline for creating and querying knowledge graphs using RAG by leveraging NIM microservices and the RAPIDS ecosystem to process large-scale datasets efficiently.

- [Knowledge Graphs for RAG with NVIDIA AI Foundation Models and Endpoints](community/knowledge_graph_rag)

### Agentic Workflows with Llama 3.1

- Build an Agentic RAG Pipeline with Llama 3.1 and NVIDIA NeMo Retriever NIM microservices [[Blog](https://developer.nvidia.com/blog/build-an-agentic-rag-pipeline-with-llama-3-1-and-nvidia-nemo-retriever-nims/), [Notebook](RAG/notebooks/langchain/agentic_rag_with_nemo_retriever_nim.ipynb)]
- [NVIDIA Morpheus, NIM microservices, and RAG pipelines integrated to create LLM-based agent pipelines](https://github.com/NVIDIA/GenerativeAIExamples/blob/v0.7.0/experimental/event-driven-rag-cve-analysis)


### RAG with Local NIM Deployment and LangChain

- Tips for Building a RAG Pipeline with NVIDIA AI LangChain AI Endpoints by Amit Bleiweiss. [[Blog](https://developer.nvidia.com/blog/tips-for-building-a-rag-pipeline-with-nvidia-ai-langchain-ai-endpoints/), [Notebook](https://github.com/NVIDIA/GenerativeAIExamples/blob/v0.7.0/notebooks/08_RAG_Langchain_with_Local_NIM.ipynb)]

For more information, refer to the [Generative AI Example releases](https://github.com/NVIDIA/GenerativeAIExamples/releases/).

### Vision NIM Workflows
A collection of Jupyter notebooks, sample code and reference applications built with Vision NIMs.

To pull the vision NIM workflows, clone this repository recursively:
```
git clone https://github.com/nvidia/GenerativeAIExamples --recurse-submodules
```

The workflows will then be located at [GenerativeAIExamples/vision_workflows](vision_workflows/README.md)

Follow the links below to learn more:
- [Learn how to use VLMs to automatically monitor a video stream for custom events.](nim_workflows/vlm_alerts/README.md)
- [Learn how to search images with natural language using NV-CLIP.](nim_workflows/nvclip_multimodal_search/README.md)
- [Learn how to combine VLMs, LLMs and CV models to build a robust text extraction pipeline.](nim_workflows/vision_text_extraction/README.md)
- [Learn how to use embeddings with NVDINOv2 and a Milvus VectorDB to build a few shot classification model.](nim_workflows/nvdinov2_few_shot/README.md)


## Try it Now!

Experience NVIDIA RAG Pipelines with just a few steps!

1. Get your NVIDIA API key.
   1. Go to the [NVIDIA API Catalog](https://build.ngc.nvidia.com/explore/).
   1. Select any model.
   1. Click **Get API Key**.
   1. Run:
      ```console
      export NVIDIA_API_KEY=nvapi-...
      ``` 

1. Clone the repository.

   ```console
   git clone https://github.com/nvidia/GenerativeAIExamples.git
   ```

1. Build and run the basic RAG pipeline.

   ```console
   cd GenerativeAIExamples/RAG/examples/basic_rag/langchain/
   docker compose up -d --build
   ```

1. Go to <https://localhost:8090/> and submit queries to the sample RAG Playground.

1. Stop containers when done. 
  
   ```console
   docker compose down
   ``` 
      


## RAG

### RAG Notebooks

NVIDIA has first-class support for popular generative AI developer frameworks like [LangChain](https://python.langchain.com/v0.2/docs/integrations/chat/nvidia_ai_endpoints/), [LlamaIndex](https://docs.llamaindex.ai/en/stable/examples/llm/nvidia/), and [Haystack](https://haystack.deepset.ai/integrations/nvidia). These end-to-end notebooks show how to integrate NIM microservices using your preferred generative AI development framework.

Use these [notebooks](./RAG/notebooks/README.md) to learn about the LangChain and LlamaIndex connectors.

#### LangChain Notebooks

- RAG
  - [Basic RAG with CHATNVIDIA LangChain Integration](./RAG/notebooks/langchain/langchain_basic_RAG.ipynb)
  - [RAG using local NIM microservices for LLMs and Retrieval](./RAG/notebooks/langchain/RAG_Langchain_with_Local_NIM.ipynb)
  - [RAG for HTML Documents](./RAG/notebooks/langchain/RAG_for_HTML_docs_with_Langchain_NVIDIA_AI_Endpoints.ipynb)
  - [Chat with NVIDIA Financial Reports](./RAG/notebooks/langchain/Chat_with_nvidia_financial_reports.ipynb)
- Agents
  - [NIM Tool Calling 101](https://github.com/langchain-ai/langchain-nvidia/blob/main/cookbook/nvidia_nim_agents_llama3.1.ipynb)
  - [Agentic RAG with NeMo Retriever](./RAG/notebooks/langchain/agentic_rag_with_nemo_retriever_nim.ipynb)
  - [Agents with Human in the Loop](./RAG/notebooks/langchain/LangGraph_HandlingAgent_IntermediateSteps.ipynb)


#### LlamaIndex Notebooks

- [Basic RAG with LlamaIndex Integration](./RAG/notebooks/llamaindex/llamaindex_basic_RAG.ipynb)

### RAG Examples

By default, these end-to-end [examples](RAG/examples/README.md) use preview NIM endpoints on [NVIDIA API Catalog](https://catalog.ngc.nvidia.com). Alternatively, you can run any of the examples [on premises](./RAG/examples/local_deploy/).

#### Basic RAG Examples

  - [LangChain example](./RAG/examples/basic_rag/langchain/README.md)
  - [LlamaIndex example](./RAG/examples/basic_rag/llamaindex/README.md)

#### Advanced RAG Examples

  - [Multi-Turn](./RAG/examples/advanced_rag/multi_turn_rag/README.md)
  - [Multimodal Data](./RAG/examples/advanced_rag/multimodal_rag/README.md)
  - [Structured Data](./RAG/examples/advanced_rag/structured_data_rag/README.md) (CSV)
  - [Query Decomposition](./RAG/examples/advanced_rag/query_decomposition_rag/README.md)

### RAG Tools

Example tools and tutorials to enhance LLM development and productivity when using NVIDIA RAG pipelines.

- [Evaluation](./RAG/tools/evaluation/README.md)
- [Observability](./RAG/tools/observability/README.md)

### RAG Projects

- [NVIDIA Tokkio LLM-RAG](https://docs.nvidia.com/ace/latest/workflows/tokkio/text/Tokkio_LLM_RAG_Bot.html): Use Tokkio to add avatar animation for RAG responses.
- [Hybrid RAG Project on AI Workbench](https://github.com/NVIDIA/workbench-example-hybrid-rag): Run an NVIDIA AI Workbench example project for RAG.

## Documentation

### Getting Started

- [Prerequisites](./docs/common-prerequisites.md)

### How To's

- [Changing the Inference or Embedded Model](./docs/change-model.md)
- [Customizing the Vector Database](./docs/vector-database.md)
- [Customizing the Chain Server](./docs/chain-server.md):
  - [Chunking Strategy](./docs/text-splitter.md)
  - [Prompting Template Engineering](./docs/prompt-customization.md)
- [Configuring LLM Parameters at Runtime](./docs/llm-params.md)
- [Supporting Multi-Turn Conversations](./docs/multiturn.md)
- [Speaking Queries and Listening to Responses with NVIDIA Riva](./docs/riva-asr-tts.md)

### Reference

- [Support Matrix](./docs/support-matrix.md)
- [Architecture](./docs/architecture.md)
- [Using the Sample Chat Web Application](./docs/using-sample-web-application.md)
- [RAG Playground Web Application](./docs/frontend.md)
- [Software Component Configuration](./docs/configuration.md)


## Community
We're posting these examples on GitHub to support the NVIDIA LLM community and facilitate feedback.
We invite contributions! Open a GitHub issue or pull request! See [contributing](docs/contributing.md) Check out the [community](./community/README.md) examples and notebooks.
