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
  * [Data Flywheel](#data-flywheel)
  * [Safer Agentic AI](#safer-agentic-ai)
  * [Knowledge Graph RAG](#knowledge-graph-rag)
  * [Agentic Workflows with Llama 3.1](#agentic-workflows-with-llama-31)
  * [RAG with Local NIM Deployment and LangChain](#rag-with-local-nim-deployment-and-langchain)
  * [Vision NIM Workflows](#vision-nim-workflows)
* [Data Flywheel](#data-flywheel)
  * [Tool-Calling Notebooks](#tool-calling-notebooks)
* [RAG](#rag)
  * [RAG Projects](#rag-projects)
* [Documentation](#documentation)
  * [Getting Started](#getting-started)
  * [How To's](#how-tos)
  * [Reference](#reference)
* [Community](#community)

<!-- /TOC -->

## What's New?

### Data Flywheel

These tutorials demonstrate Data Flywheel workflows that use NVIDIA NeMo Microservices. They include components such as NVIDIA NeMo Datastore, NeMo Entity Store, NeMo Customizer, NeMo Evaluator, NeMo Guardrails microservices, and NVIDIA NIMs.

- [Tool Calling Fine-tuning, Inference, Evaluation, and Guardrailing with NVIDIA NeMo Microservices and NIMs](./nemo/data-flywheel/tool-calling)
- [Embedding Fine-tuning, Inference, and Evaluation with NVIDIA NeMo Microservices and NIMs](./nemo/data-flywheel/embedding-finetuning/)

### Safer Agentic AI

The following tutorials illustrate how to audit your large language models with NeMo Auditor to identify vulnerabilities to unsafe prompts, and how to run inference with multiple rails in parallel to reduce latency and improve throughput. 

- [Audit your LLMs](./nemo/NeMo-Auditor/Getting_Started_With_NeMo_Auditor.ipynb)
- [Inference with Parallel Rails](./nemo/NeMo-Guardrails/Parallel_Rails_Tutorial.ipynb)

### Knowledge Graph RAG

This example implements a GPU-accelerated pipeline for creating and querying knowledge graphs using RAG by leveraging NIM microservices and the RAPIDS ecosystem to process large-scale datasets efficiently.

- [Knowledge Graphs for RAG with NVIDIA AI Foundation Models and Endpoints](community/knowledge_graph_rag)

### Agentic Workflows with Llama 3.1

- Build an Agentic RAG Pipeline with Llama 3.1 and NVIDIA NeMo Retriever NIM microservices [[Blog](https://developer.nvidia.com/blog/build-an-agentic-rag-pipeline-with-llama-3-1-and-nvidia-nemo-retriever-nims/), [Notebook](https://github.com/NVIDIA/GenerativeAIExamples/tree/203b0de48d1142124842d56d4b40f3733888f5ee/RAG/notebooks/langchain/agentic_rag_with_nemo_retriever_nim.ipynb)]
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


## Data Flywheel

A [Data Flywheel](https://www.nvidia.com/en-us/glossary/data-flywheel/) is a self-reinforcing cycle where user interactions generate data that improves AI models or products, leading to better outcomes that attract more users and further enhance data quality. This feedback loop relies on continuous data processing, model refinement, and guardrails to ensure accuracy and compliance while compounding value over time. Real-world applications range from personalized customer experiences to operational systems like inventory management, where improved predictions drive efficiency and growth.

### Tool-Calling Notebooks

Tool calling empowers Large Language Models (LLMs) to integrate with external APIs, execute dynamic workflows, and retrieve real-time data beyond their training scope. The NVIDIA NeMo microservices platform offers a modular infrastructure for deploying AI pipelines that includes fine-tuning, evaluation, inference, and guardrail enforcement—across Kubernetes clusters in cloud or on-premises environments.

This end-to-end [tutorial](./nemo/data-flywheel/tool-calling) demonstrates how to leverage NeMo Microservices to customize [Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) by using the [xLAM](https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k) function-calling dataset, assess its accuracy, and implement safety constraints to govern its behavior.

## RAG

The former `RAG/` examples, notebooks, and tools have been removed. They remain available in the [repository history](https://github.com/NVIDIA/GenerativeAIExamples/tree/203b0de48d1142124842d56d4b40f3733888f5ee/RAG).

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

