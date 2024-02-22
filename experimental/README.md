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

# Experimental Examples

## What is an Experimental Example?

Experimental examples are sample code and deployments for RAG pipelines that are not tested by NVIDIA personnel.

## Inventory

* [NVIDIA RAG Streaming Document Ingestion Pipeline](./streaming_ingest_rag)

  This example demonstrate the construction of a performance-oriented pipeline that accepts a stream of heterogenous documents, divides the documents into smaller segments or chunks, computes the embedding vector for each of these chunks, and uploads the text chunks along with their associated embeddings to a Vector Database. This pipeline builds on the [Morpheus SDK](https://docs.nvidia.com/morpheus/index.html) to take advantage of end-to-end asynchronous processing. This pipeline showcases pipeline parallelism (including CPU and GPU-accelerated nodes), as well as, a mechanism to horizontally scale out data ingestion workers.

* [NVIDIA Multimodal RAG Assistant](./multimodal_assistant)

  This example is able to ingest PDFs, PowerPoint slides, Word and other documents with complex data formats including text, images, slides and tables. It allows users to ask questions through a text interface and optionally with an image query, and it can respond with text and reference images, slides and tables in its response, along with source links and downloads.

* [Run RAG-LLM in Azure Machine Learning](./AzureML)

  This example shows the configuration changes to using Docker containers and local GPUs that are required
  to run the RAG-LLM pipelines in Azure Machine Learning.
