<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Architecture

<!-- TOC -->

* [Overview of Software Components](#overview-of-software-components)
* [NVIDIA AI Components](#nvidia-ai-components)
    * [NVIDIA TensorRT-LLM Optimization](#nvidia-tensorrt-llm-optimization)
    * [NVIDIA NIM for LLMs Container](#nvidia-nim-for-llms-container)
* [Inference Pipeline](#inference-pipeline)
* [Document Ingestion and Retrieval](#document-ingestion-and-retrieval)
* [User Query and Response Generation](#user-query-and-response-generation)
* [LLM Inference Server](#llm-inference-server)
* [Vector DB](#vector-db)

<!-- /TOC -->


## Overview of Software Components

The default sample deployment contains:

- Inference and embedding are performed by accessing model endpoints running on NVIDIA API Catalog.

  Most examples use the [Meta Llama 3 70B Instruct](https://build.ngc.nvidia.com/meta/llama3-70b) model
  for inference and the [Snowflake Arctic Embed L](https://build.ngc.nvidia.com/snowflake/arctic-embed-l)
  model for embedding.

  Alternatively, you can deploy NVIDIA NIM for LLMs and NVIDIA NeMo Retriever Embedding microservice
  to use local models and local GPUs.
  Refer to the [](nim-llms.md) example for more information.

- A Chain Server uses [LangChain](https://github.com/langchain-ai/langchain/) and [LlamaIndex](https://www.llamaindex.ai/) for combining language model components and easily constructing question-answering from a company's database.

- [Sample Jupyter Notebooks](jupyter-server.md) and [](./frontend.md) so that you can test the chat system in an interactive manner.

- [Milvus](https://milvus.io/docs/install_standalone-docker.md) or [pgvector](https://github.com/pgvector/pgvector) - Embeddings are stored in a vector database. Milvus is an open-source vector database capable of NVIDIA GPU-accelerated vector searches.

The sample deployment is a reference for you to build your own enterprise AI solution with minimal effort.

## NVIDIA AI Components

The sample deployment uses a variety of NVIDIA AI components to customize and deploy the RAG-based chat bot example.

- [NVIDIA TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM)
- [NVIDIA NIM for LLMs](https://docs.nvidia.com/nim/large-language-models/latest/index.html)

### NVIDIA TensorRT-LLM Optimization

An LLM can be optimized using TensorRT-LLM.
NVIDIA NIM for LLMs uses TensorRT for LLMs (TensorRT-LLM) to accelerate and maximize inference performance on the latest LLMs.
The sample deployment deploys a Llama 3 8B parameter chat model that TensorRT-LLM optimizes for inference.

### NVIDIA NIM for LLMs Container

The NVIDIA NIM for LLMs container simplifies deployment and provides high-performance, cost-effective, and low-latency inference.
Software in the container determines your GPU hardware and determines whether to use the TensorRT-LLM backend or the vLLM backend.

## Inference Pipeline

To get started with the inferencing pipeline, we connect the LLM to a sample vector database.
You can upload documents and embeddings of the documents are stored in the vector database to augment the responses to your queries.
The knowledge in the vector database can come in many forms: product specifications, HR documents, or finance spreadsheets.
Enhancing the model’s capabilities with this knowledge can be done with RAG.

Because foundational LLMs are not trained on your proprietary enterprise data and are only trained up to a fixed point in time, they need to be augmented with additional data.
RAG consists of two processes.
First, *retrieval* of data from document repositories, databases, or APIs that are all outside of the foundational model’s knowledge.
Second, *generation* of responses via inference.

## Document Ingestion and Retrieval

RAG begins with a knowledge base of relevant up-to-date information.
Because data within an enterprise is frequently updated, the ingestion of documents into a knowledge base is a recurring process and could be scheduled as a job.
Next, content from the knowledge base is passed to an embedding model such as Snowflake Arctic Embedding L that the sample deployment uses.
The embedding model converts the content to vectors, referred to as *embeddings*.
Generating embeddings is a critical step in RAG.
The embeddings provide dense numerical representations of textual information.
These embeddings are stored in a vector database.
The default database is Milvus, which is [RAFT accelerated](https://developer.nvidia.com/blog/accelerating-vector-search-using-gpu-powered-indexes-with-rapids-raft).
An alternative vector database is pgvector.

## User Query and Response Generation

When a user query is sent to the inference server, it is converted to an embedding using the embedding model.
This is the same embedding model that is used to convert the documents in the knowledge base.
The database performs a similarity/semantic search to find the vectors that most closely resemble the user’s intent and provides them to the LLM as enhanced context.
Because Milvus is RAFT accelerated, the similarity search is optimized on the GPU.
Lastly, the LLM generates a full answer that is streamed to the user.
This is all done with ease using [LangChain](https://github.com/langchain-ai/langchain/) and [LlamaIndex](https://www.llamaindex.ai).

The following diagram illustrates the ingestion of documents and generation of responses.

![Diagram](images/image2.png)

LangChain enables you to write LLM wrappers for your own custom LLMs.
NVIDIA provides a sample wrapper for streaming responses from an LLM running in NVIDIA NIM for LLMs.
This wrapper enables us to leverage LangChain’s standard interface for interacting with LLMs while still achieving vast performance speedup from TensorRT-LLM and scalable and flexible inference from NIM for LLMs.

A sample chat bot web application is provided in the sample deployment so that you can test the chat system in an interactive manner.
Requests to the chat system are wrapped in API calls, so these can be abstracted to other applications.

An additional method of customization in the inference pipeline is possible with a prompt template.
A prompt template is a pre-defined recipe for generating prompts for language models.
The prompts can contain instructions, few-shot examples, and context that is appropriate for a given task.
In our sample deployment, we prompt our model to generate safe and polite responses.


## LLM Inference Server

The NVIDIA NIM for LLMs container downloads a model that is cached in a model repository.
This repository is available locally to serve inference requests.
After the container downloads the model, inference requests are sent from a client application.
Python and C++ libraries provide APIs to simplify communication.
Clients send HTTP/REST requests to NIM for LLMs using HTTP/REST or gRPC protocols.

## Vector DB

Milvus is an open-source vector database built to power embedding similarity search and AI applications.
The database makes unstructured data from API calls, PDFs, and other documents more accessible by storing them as embeddings.

When content from the knowledge base is passed to an embedding model, the model converts the content to vectors--referred to as *embeddings*.
These embeddings are stored in the vector database.
The sample deployment uses Milvus as the vector database.
Milvus is an open-source vector database capable of NVIDIA GPU-accelerated vector searches.
