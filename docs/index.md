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

# NVIDIA Generative AI Examples

Generative AI enables users to quickly generate new content based on a variety of inputs and is a powerful tool for streamlining the workflow of creatives, engineers, researchers, scientists, and more.
The use cases and possibilities span all industries and individuals.
Generative AI models can produce novel content like stories, emails, music, images, and videos.

Generative AI starts with foundational models trained on vast quantities of unlabeled data.
Large language models (LLMs) are trained on an extensive range of textual data online.
These LLMs can understand prompts and generate novel, human-like responses.
Businesses can build applications to leverage this capability of LLMs.
Some uses are creative writing assistants for marketing, document summarization for legal teams, and code writing for software development.

The NVIDIA Generative AI Examples use Docker Compose
run Retrieval Augmented Generation (RAG) Large Language Model (LLM) pipelines.

All the example pipelines deploy a sample chat bot application for question and answering that is enhanced with RAG.
The chat bot also supports uploading documents to create a knowledge base.

## Developer RAG Examples

```{eval-rst}
.. list-table::
   :header-rows: 1

   * - | Model
     - | Embedding
     - | Framework
     - | Description
     - | Multi-GPU
     - | TensorRT-LLM
     - | Model
       | Location
     - | Triton
       | Inference
       | Server
     - | Vector
       | Database

   * - ai-mixtral-8x7b-instruct
     - nvolveqa_40k
     - LangChain
     - :doc:`api-catalog`
     - NO
     - NO
     - API Catalog
     - NO
     - Milvus or pgvector

   * - llama-2
     - e5-large-v2
     - LlamaIndex
     - :doc:`local-gpu`
     - NO
     - YES
     - Local Model
     - YES
     - Milvus or pgvector

   * - llama-2
     - e5-large-v2
     - LlamaIndex
     - :doc:`multi-gpu`
     - YES
     - YES
     - Local Model
     - YES
     - Milvus or pgvector

   * - ai-llama2-70b
     - nvolveqa_40k
     - LangChain
     - :doc:`query-decomposition`
     - NO
     - NO
     - API Catalog
     - NO
     - Milvus or pgvector

   * - llama2-7b
     - e5-large-v2
     - LlamaIndex
     - :doc:`quantized-llm-model`
     - NO
     - YES
     - Local Model
     - YES
     - Milvus or pgvector

   * - ai-mixtral-8x7b-instruct for response generation

       ai-mixtral-8x7b-instruct for PandasAI
     - Not Applicable
     - PandasAI
     - :doc:`structured-data`
     - NO
     - NO
     - API Catalog
     - NO
     - Not Applicable

   * - ai-mixtral-8x7b-instruct for response generation

       ai-google-Deplot for graph to text conversion

       ai-Neva-22B for image to text conversion
     - nvolveqa_40k
     - Custom Python
     - :doc:`multimodal-data`
     - NO
     - NO
     - API Catalog
     - NO
     - Milvus or pgvector

   * - ai-llama2-70b
     - nvolveqa_40k
     - LangChain
     - :doc:`multi-turn`
     - NO
     - NO
     - API Catalog
     - NO
     - Milvus or pgvector

```

## Open Source Connectors

```{include} ../README.md
:start-after: '## Open Source Integrations'
:end-before: '## NVIDIA support'
```

```{toctree}
:caption: RAG Pipelines for Developers
:titlesonly:
:hidden:

About the RAG Pipelines <self>
support-matrix
API Catalog Models <api-catalog>
Local GPUs <local-gpu>
Multi-GPU for Inference <multi-gpu>
Query Decomposition <query-decomposition>
Quantized Model <quantized-llm-model>
Structured Data <structured-data>
Multimodal Data <multimodal-data>
Multi-turn <multi-turn>
Sample Chat Application <using-sample-web-application>
Alternative Vector Database <vector-database>
```

```{toctree}
:caption: Tools
:titlesonly:
:hidden:

Evaluation <evaluation>
Observability <observability>
```

```{toctree}
:caption: Jupyter Notebooks
:titlesonly:
:hidden:
:glob:

notebooks/*
```

```{toctree}
:caption: Software Components
:titlesonly:
:hidden:

architecture
llm-inference-server
frontend
jupyter-server
chain-server
configuration
```
