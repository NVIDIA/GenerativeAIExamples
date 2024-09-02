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

# Community Examples

## What is an Community Example?

Community examples are sample code and deployments for RAG pipelines that are not tested by NVIDIA personnel.

## Inventory

* [NVIDIA RAG in 5 minutes](./5_mins_rag_no_gpu/)

  This is a simple standalone implementation showing rag pipeline using Nvidia API Catalog models. It uses a simple Streamlit UI and one file implementation of a minimalistic RAG pipeline.

* [NVIDIA RAG Streaming Document Ingestion Pipeline](./streaming_ingest_rag)

  This example demonstrate the construction of a performance-oriented pipeline that accepts a stream of heterogenous documents, divides the documents into smaller segments or chunks, computes the embedding vector for each of these chunks, and uploads the text chunks along with their associated embeddings to a Vector Database. This pipeline builds on the [Morpheus SDK](https://docs.nvidia.com/morpheus/index.html) to take advantage of end-to-end asynchronous processing. This pipeline showcases pipeline parallelism (including CPU and GPU-accelerated nodes), as well as, a mechanism to horizontally scale out data ingestion workers.

* [NVIDIA Live FM Radio ASR RAG](./fm-asr-streaming-rag)

  This example is a demonstration of a RAG workflow that ingests streaming text derived from live FM radio signals. An SDR signal processing pipeline built with [NVIDIA Holoscan](https://developer.nvidia.com/holoscan-sdk) is used to process I/Q samples sent over UDP. ASR is performed on the processed audio data using [NVIDIA Riva](https://www.nvidia.com/en-us/ai-data-science/products/riva/) and stored in a time-informed FAISS database. Uses LangChain connectors to [NVIDIA AI Foundation Models Endpoint](https://www.nvidia.com/en-us/ai-data-science/foundation-models/) or models running on-prem with [NVIDIA NIM](https://developer.nvidia.com/docs/nemo-microservices/inference/overview.html).

* [NVIDIA ORAN chatbot multimodal Assistant](./oran-chatbot-multimodal/)

  This example is designed to make it extremely easy to set up your own retrieval-augmented generation chatbot for ORAN techncial specifications and processes. The backend here calls the NVIDIA NeMo Service, which makes it very easy to deploy on a thin client or Virtual Machine (ie, without a GPU setup).

* [NVIDIA Retrieval Customization](./synthetic-data-retriever-customization/)

  This example is a sample demonstration on how Large Language Models (LLMs) could be used to synthetically generate training data, which can then be used to adapt retriever models.

* [NVIDIA Multimodal RAG Assistant](./multimodal_assistant)

  This example is able to ingest PDFs, PowerPoint slides, Word and other documents with complex data formats including text, images, slides and tables. It allows users to ask questions through a text interface and optionally with an image query, and it can respond with text and reference images, slides and tables in its response, along with source links and downloads. Refer to this [example](./multimodal-rag) for the LlamaIndex version that uses [integration](https://docs.llamaindex.ai/en/stable/examples/llm/nvidia_nim/) with NIM microservices of the Multimodal RAG Assistant.

* [NVIDIA Developer RAG Chatbot](./rag-developer-chatbot)

  This example shows how to create a developer-focused RAG chatbot using RAPIDS cuDF source code and API documentation as a representative example of a typical codebase.

* [NVIDIA Event Driven RAG for CVE Analysis with NVIDIA Morpheus](./event-driven-rag-cve-analysis/)

  This example demonstrates how NVIDIA Morpheus, NIM microservices, and RAG pipelines can be integrated to create LLM-based agent pipelines. These pipelines will be used to automatically and scalably traige and detect Common Vulnerabilities and Exposures (CVEs) in Docker containers using references to source code, dependencies, and information about the CVEs.

* [Digital Human Security Analyst with NVIDIA Morpheus](./digital-human-security-analyst/)

  In this example, we create a RAG enabled co-pilot for Security Operation Center analysts, with speech and facial animation. This tutorial can be applied to any use case where data retrieval and synthesis can be simple but tedious (ie. writing reports from multiple numerical datasources, or customer service requiring data lookup). We cover data ingestion, multi-step agentic reasoning, RAG, speech input/output, and digital human face animation using the [Morpheus cybersecurity SDK](https://developer.nvidia.com/morpheus-cybersecurity), [LLM NIMs](https://build.nvidia.com/meta/llama-3_1-8b-instruct), [NeMo Retriever](https://www.nvidia.com/en-us/ai-data-science/products/nemo/), [Riva Speech Services](https://developer.nvidia.com/riva), and [ACE Audio2Face](https://build.nvidia.com/nvidia/audio2face) respectively.


* [NVIDIA Knowledge Graph RAG](./knowledge_graph_rag)

  This example implements a GPU-accelerated pipeline for creating and querying knowledge graphs using Retrieval-Augmented Generation (RAG). The approach leverages NVIDIA's AI technologies and RAPIDS ecosystem to process large-scale datasets efficiently. It allows users to interact through a chat interface and also visualize the corresponding knowledge graph, and perform evaluations against synthetic data generated with NVIDIA's Nemotron-4 340B model.

* [LLM Prompt Design Helper using NIM](./llm-prompt-design-helper/)

  This tool demonstrates how to utilize a user-friendly interface to interact with NVIDIA NIMs, including those available in the API catalog, self-deployed NIM endpoints, and NIMs hosted on Hugging Face. It also provides settings to integrate RAG pipelines with either local and temporary vector stores or self-hosted search engines. Developers can use this tool to design system prompts, few-shot prompts, and configure LLM settings.