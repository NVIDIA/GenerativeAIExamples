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
     - | Model
       | Location
     - | NIM
       | for
       | LLMs
     - | Vector
       | Database

   * - ai-llama3-70b
     - snowflake-arctic-embed-l
     - LangChain
     - :doc:`api-catalog`
     - API Catalog
     - No
     - Milvus or pgvector

   * - ai-llama3-70b
     - snowflake-arctic-embed-l
     - LangChain
     - :doc:`query-decomposition`
     - API Catalog
     - No
     - Milvus or pgvector

   * - meta/llama3-70b-instruct for response generation

       meta/llama3-70b-instruct for PandasAI
     - Not Applicable
     - PandasAI
     - :doc:`structured-data`
     - API Catalog
     - No
     - Not Applicable

   * - ai-llama3-8b for response generation

       ai-google-Deplot for graph to text conversion

       ai-Neva-22B for image to text conversion
     - snowflake-arctic-embed-l
     - Custom Python
     - :doc:`multimodal-data`
     - API Catalog
     - No
     - Milvus or pgvector

   * - ai-llama3-8b
     - snowflake-arctic-embed-l
     - LangChain
     - :doc:`multi-turn`
     - API Catalog
     - No
     - Milvus or pgvector

   * - meta-llama3-8b-instruct
     - nv-embed-qa:4
     - LangChain
     - :doc:`nim-llms`
     - Local LLM
     - Yes
     - Milvus or pgvector

```

## Open Source Connectors

```{include} ../README.md
:start-after: '## Open Source Integrations'
:end-before: '## Related NVIDIA Projects'
```

```{toctree}
:caption: RAG Pipelines for Developers
:titlesonly:
:hidden:

About the RAG Pipelines <self>
support-matrix
API Catalog Models <api-catalog>
Query Decomposition <query-decomposition>
Structured Data <structured-data>
Multimodal Data <multimodal-data>
Multi-turn <multi-turn>
Sample Chat Application <using-sample-web-application>
Alternative Vector Database <vector-database>
NIM for LLMs <nim-llms>
Developing Simple Examples <simple-examples>
```

```{toctree}
:caption: Tools
:titlesonly:
:hidden:

Evaluation <tools/evaluation/index.md>
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
frontend
jupyter-server
chain-server
configuration
```
