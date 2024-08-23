<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

![](docs/images/apps-catalog-promo-web-banner-laptop-300@2x.jpg)

# NVIDIA Generative AI Examples
This repository serves as a starting point for generative AI developers looking to integrate with the NVIDIA software ecosystem to accelerate their generateive AI systems.
Whether you are building RAG pipelines, agentic workflows, or finetuning models, this repository will help you integrate NVIDIA, seamlesly and natively, with your development stack.

## What's new?

#### Knowledge Graph RAG
The example implements a GPU-accelerated pipeline for creating and querying knowledge graphs using RAG by leveraging NIM microservices and the RAPIDS ecosystem for efficient processing of large-scale datasets.
- [Knowledge Graphs for RAG with NVIDIA AI Foundation Models and Endpoints](community/knowledge_graph_rag)

#### Agentic Workflows with Llama 3.1
- Build an Agentic RAG Pipeline with Llama 3.1 and NVIDIA NeMo Retriever NIM microservices [[Blog](https://developer.nvidia.com/blog/build-an-agentic-rag-pipeline-with-llama-3-1-and-nvidia-nemo-retriever-nims/), [notebook](RAG/notebooks/langchain/agentic_rag_with_nemo_retriever_nim.ipynb)]
- [NVIDIA Morpheus, NIM microservices, and RAG pipelines integrated to create LLM-based agent pipelines](https://github.com/NVIDIA/GenerativeAIExamples/blob/v0.7.0/experimental/event-driven-rag-cve-analysis)

#### RAG with local NIM deployment and Langchain
- Tips for Building a RAG Pipeline with NVIDIA AI LangChain AI Endpoints by Amit Bleiweiss. [[Blog](https://developer.nvidia.com/blog/tips-for-building-a-rag-pipeline-with-nvidia-ai-langchain-ai-endpoints/), [notebook](https://github.com/NVIDIA/GenerativeAIExamples/blob/v0.7.0/notebooks/08_RAG_Langchain_with_Local_NIM.ipynb)]

#### NeMo Guardrails with RAG
- Notebook for demonstrating how to integrate NeMo Guardrails with a basic RAG pipeline in LangChain to ensure safe and accurate LLM responses using NVIDIA NIM microservices. [[Blog](https://developer.nvidia.com/blog/securing-generative-ai-deployments-with-nvidia-nim-and-nvidia-nemo-guardrails/), [notebook](RAG/notebooks/langchain/NeMo_Guardrails_with_LangChain_RAG/using_nemo_guardrails_with_LangChain_RAG.ipynb)]




For more details view the [releases](https://github.com/NVIDIA/GenerativeAIExamples/releases/).

## Try it now!

Experience NVIDIA RAG Pipelines with just a few steps!

1. Get your NVIDIA API key.

   Visit the [NVIDIA API Catalog](https://build.ngc.nvidia.com/explore/), select on any model, then click on `Get API Key`

   Afterward, run `export NVIDIA_API_KEY=nvapi-...`.

1. Clone the repository and then build and run the basic RAG pipeline:

   ```console
   git clone https://github.com/nvidia/GenerativeAIExamples.git
   cd GenerativeAIExamples/RAG/examples/basic_rag/langchain/
   docker compose up -d --build
   ```

Open a browser to <https://localhost:8090/> and submit queries to the sample RAG Playground.

When done, stop containers by running `docker compose down`.


## End to end RAG Examples and Notebooks
NVIDIA has first class support for popular generative AI developer frameworks like [LangChain](https://python.langchain.com/v0.2/docs/integrations/chat/nvidia_ai_endpoints/), [LlamaIndex](https://docs.llamaindex.ai/en/stable/examples/llm/nvidia/) and [Haystack](https://haystack.deepset.ai/integrations/nvidia). These notebooks will show you how to integrate NIM microservices using your preferred generative AI development framework.

### Notebooks
Use the [notebooks](./RAG/notebooks/README.md) to learn about the LangChain and LlamaIndex connectors.

#### LangChain Notebooks
- RAG
  - [Basic RAG with CHATNVIDIA Langchain Integration](./RAG/notebooks/langchain/langchain_basic_RAG.ipynb)
  - [RAG using local NIM microservices for LLMs and Retrieval](./RAG/notebooks/langchain/RAG_Langchain_with_Local_NIM.ipynb)
  - [RAG for HTML Documents](./RAG/notebooks/langchain/RAG_for_HTML_docs_with_Langchain_NVIDIA_AI_Endpoints.ipynb)
  - [Chat with NVIDIA Financial Reports](./RAG/notebooks/langchain/Chat_with_nvidia_financial_reports.ipynb)
- Agents
  - [NIM Tool Calling 101](https://github.com/langchain-ai/langchain-nvidia/blob/main/cookbook/nvidia_nim_agents_llama3.1.ipynb)
  - [Agentic RAG with NeMo Retriever](./RAG/notebooks/langchain/agentic_rag_with_nemo_retriever_nim.ipynb)
  - [Agents with Human in the Loop](./RAG/notebooks/langchain/LangGraph_HandlingAgent_IntermediateSteps.ipynb)


#### LlamaIndex Notebooks
- [Basic RAG with LlamaIndex Integration](./RAG/notebooks/llamaindex/llamaindex_basic_RAG.ipynb)

### End to end RAG Examples
By default, the [examples](RAG/examples/README.md) use preview NIM endpoints on [NVIDIA API Catalog](https://catalog.ngc.nvidia.com).
  Alternatively, you can run any of the examples [on premises](./RAG/examples/local_deploy/).

#### Basic RAG Examples
  - [LangChain example](./RAG/examples/basic_rag/langchain/README.md)
  - [LlamaIndex example](./RAG/examples/basic_rag/llamaindex/README.md)

#### Advanced RAG Examples
  - [Multi-Turn](./RAG/examples/advanced_rag/multi_turn_rag/README.md)
  - [Multimodal Data](./RAG/examples/advanced_rag/multimodal_rag/README.md)
  - [Structured Data](./RAG/examples/advanced_rag/structured_data_rag/README.md) (CSV)
  - [Query Decomposition](./RAG/examples/advanced_rag/query_decomposition_rag/README.md)

### How To Guides

- [Change the inference or embedding model](./docs/change-model.md)
- [Customize the vector database](./docs/vector-database.md)
- Customize the chain server:
  - [Chunking strategy](./docs/text-splitter.md)
  - [Prompt template engineering](./docs/prompt-customization.md)
- [Support multiturn conversations](./docs/multiturn.md)
- [Configure LLM parameters at runtime](./docs/llm-params.md)
- [Speak queries and listen to responses with NVIDIA Riva](./docs/riva-asr-tts.md).

## Tools

Example tools and tutorials to enhance LLM development and productivity when using NVIDIA RAG pipelines.

- [Evaluation](./RAG/tools/evaluation/README.md)
- [Observability](./RAG/tools/observability/README.md)

## Community
We're posting these examples on GitHub to support the NVIDIA LLM community and facilitate feedback.
We invite contributions! Open a GitHub issue or pull request!

Check out the [community](./community/README.md) examples and notebooks.

## Related NVIDIA RAG Projects

- [NVIDIA Tokkio LLM-RAG](https://docs.nvidia.com/ace/latest/workflows/tokkio/text/Tokkio_LLM_RAG_Bot.html): Use Tokkio to add avatar animation for RAG responses.

- [Hybrid RAG Project on AI Workbench](https://github.com/NVIDIA/workbench-example-hybrid-rag): Run an NVIDIA AI Workbench example project for RAG.
