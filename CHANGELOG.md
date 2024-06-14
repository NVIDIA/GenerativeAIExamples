# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.7.0] - 2024-06-18

This release switches all examples to use cloud hosted GPU accelerated LLM and embedding models from [Nvidia API Catalog](https://build.nvidia.com) as default. It also deprecates support to deploy on-prem models using NeMo Inference Framework Container and adds support to deploy accelerated generative AI models across the cloud, data center, and workstation using [latest Nvidia NIM-LLM](https://docs.nvidia.com/nim/large-language-models/latest/introduction.html).

### Added
- Added model [auto download and caching support for `nemo-retriever-embedding-microservice` and `nemo-retriever-reranking-microservice`](./deploy/compose/docker-compose-nim-ms.yaml). Updated steps to deploy the services can be found [here](https://nvidia.github.io/GenerativeAIExamples/latest/nim-llms.html).
- [Multimodal RAG Example enhancements](https://nvidia.github.io/GenerativeAIExamples/latest/multimodal-data.html)
  - Moved to the [PDF Plumber library](https://pypi.org/project/pdfplumber/) for parsing text and images.
  - Added `pgvector` vector DB support.
  - Added support to ingest files with .pptx extension
  - Improved accuracy of image parsing by using [tesseract-ocr](https://pypi.org/project/tesseract-ocr/)
- Added a [new notebook showcasing RAG usecase using accelerated NIM based on-prem deployed models](./notebooks/08_RAG_Langchain_with_Local_NIM.ipynb)
- Added a [new experimental example](./experimental/rag-developer-chatbot/) showcasing how to create a developer-focused RAG chatbot using RAPIDS cuDF source code and API documentation.
- Added a [new experimental example](./experimental/event-driven-rag-cve-analysis/) demonstrating how NVIDIA Morpheus, NIMs, and RAG pipelines can be integrated to create LLM-based agent pipelines.

### Changed
- All examples now use llama3 models from [Nvidia API Catalog](https://build.nvidia.com/search?term=llama3) as default. Summary of updated examples and the model it uses is available [here](https://nvidia.github.io/GenerativeAIExamples/latest/index.html#developer-rag-examples).
- Switched default embedding model of all examples to [Snowflake arctic-embed-I model](https://build.nvidia.com/snowflake/arctic-embed-l)
- Added more verbose logs and support to configure [log level for chain server using LOG_LEVEL enviroment variable](https://nvidia.github.io/GenerativeAIExamples/latest/configuration.html#chain-server).
- Bumped up version of `langchain-nvidia-ai-endpoints`, `sentence-transformers` package and `milvus` containers
- Updated base containers to use ubuntu 22.04 image `nvcr.io/nvidia/base/ubuntu:22.04_20240212`
- Added `llama-index-readers-file` as dependency to avoid runtime package installation within chain server.


### Deprecated
- Deprecated support of on-prem LLM model deployment using [NeMo Inference Framework Container](https://github.com/NVIDIA/GenerativeAIExamples/blob/v0.6.0/deploy/compose/rag-app-text-chatbot.yaml#L2). Developers can use [Nvidia NIM-LLM to deploy TensorRT optimized models on-prem and plug them in with existing examples](https://nvidia.github.io/GenerativeAIExamples/latest/nim-llms.html).
- Deprecated [kubernetes operator support](https://github.com/NVIDIA/GenerativeAIExamples/tree/v0.6.0/deploy/k8s-operator/kube-trailblazer).
- `nvolveqa_40k` embedding model was deprecated from [Nvidia API Catalog](https://build.nvidia.com). Updated all [notebooks](./notebooks/) and [experimental artifacts](./experimental/) to use [Nvidia embed-qa-4 model](https://build.nvidia.com/nvidia/embed-qa-4) instead.
- Removed [notebooks numbered 00-04](https://github.com/NVIDIA/GenerativeAIExamples/tree/v0.6.0/notebooks), which used on-prem LLM model deployment using deprecated [NeMo Inference Framework Container](https://github.com/NVIDIA/GenerativeAIExamples/blob/v0.6.0/deploy/compose/rag-app-text-chatbot.yaml#L2).


## [0.6.0] - 2024-05-07

### Added
- Ability to switch between [API Catalog](https://build.nvidia.com/explore/discover) models to on-prem models using [NIM-LLM](https://docs.nvidia.com/ai-enterprise/nim-llm/latest/index.html).
- New API endpoint
  - `/health` - Provides a health check for the chain server.
- Containerized [evaluation application](./tools/evaluation/) for RAG pipeline accuracy measurement.
- Observability support for langchain based examples.
- New Notebooks
  - Added [Chat with NVIDIA financial data](./notebooks/12_Chat_wtih_nvidia_financial_reports.ipynb) notebook.
  - Added notebook showcasing [langgraph agent handling](./notebooks/11_LangGraph_HandlingAgent_IntermediateSteps.ipynb).
- A [simple rag example template](https://nvidia.github.io/GenerativeAIExamples/latest/simple-examples.html) showcasing how to build an example from scratch.

### Changed
- Renamed example `csv_rag` to [structured_data_rag](./RetrievalAugmentedGeneration/examples/structured_data_rag/)
- Model Engine name update
  - `nv-ai-foundation` and `nv-api-catalog` llm engine are renamed to `nvidia-ai-endpoints`
  - `nv-ai-foundation` embedding engine is renamed to `nvidia-ai-endpoints`
- Embedding model update
  - `developer_rag` example uses [UAE-Large-V1](https://huggingface.co/WhereIsAI/UAE-Large-V1) embedding model.
  - Using `ai-embed-qa-4` for api catalog examples instead of `nvolveqa_40k` as embedding model
- Ingested data now persists across multiple sessions.
- Updated langchain-nvidia-endpoints to version 0.0.11, enabling support for models like llama3.
- File extension based validation to throw error for unsupported files.
- The default output token length in the UI has been increased from 250 to 1024 for more comprehensive responses.
- Stricter chain-server API validation support to enhance API security
- Updated version of llama-index, pymilvus.
- Updated pgvector container to `pgvector/pgvector:pg16`
- LLM Model Updates
  - [Multiturn Chatbot](./RetrievalAugmentedGeneration/examples/multi_turn_rag/) now uses `ai-mixtral-8x7b-instruct` model for response generation.
  - [Structured data rag](./RetrievalAugmentedGeneration/examples/structured_data_rag/) now uses `ai-llama3-70b` for response and code generation.


## [0.5.0] - 2024-03-19

This release adds new dedicated RAG examples showcasing state of the art usecases, switches to the latest [API catalog endpoints from NVIDIA](https://build.nvidia.com/explore/discover) and also refactors the API interface of chain-server. This release also improves the developer experience by adding github pages based documentation and streamlining the example deployment flow using dedicated compose files.

### Added

- Github pages based documentation.
- New examples showcasing
  - [Multi-turn RAG](./RetrievalAugmentedGeneration/examples/multi_turn_rag/)
  - [Multi-modal RAG](./RetrievalAugmentedGeneration//examples/multimodal_rag/)
  - [Structured data CSV RAG](./RetrievalAugmentedGeneration/examples/csv_rag/)
- Support for [delete and list APIs](./docs/api_reference/openapi_schema.json) in chain-server component
- Streamlined RAG example deployment
  - Dedicated new [docker compose files](./deploy/compose/) for every examples.
  - Dedicated [docker compose files](./deploy/compose/docker-compose-vectordb.yaml) for launching vector DB solutions.
- New configurations to control top k and confidence score of retrieval pipeline.
- Added [a notebook](./models/NeMo/slm/README.md) which covers how to train SLMs with various techniques using NeMo Framework.
- Added more [experimental examples](./experimental/README.md) showcasing new usecases.
  - [NVIDIA ORAN chatbot multimodal Assistant](./experimental/oran-chatbot-multimodal/)
  - [NVIDIA Retrieval Customization](./experimental/synthetic-data-retriever-customization/)
  - [NVIDIA RAG Streaming Document Ingestion Pipeline](./experimental/streaming_ingest_rag/)
  - [NVIDIA Live FM Radio ASR RAG](./experimental/fm-asr-streaming-rag/)
- [New dedicated notebook](./notebooks/10_RAG_for_HTML_docs_with_Langchain_NVIDIA_AI_Endpoints.ipynb) showcasing a RAG pipeline using web pages.


### Changed

- Switched from NVIDIA AI Foundation to [NVIDIA API Catalog endpoints](https://build.nvidia.com/explore/discover) for accessing cloud hosted LLM models.
- Refactored [API schema of chain-server component](./docs/api_reference/openapi_schema.json) to support runtime allocation of llm parameters like temperature, max tokens, chat history etc.
- Renamed `llm-playground` service in compose files to `rag-playground`.
- Switched base containers for all components to ubuntu instead of pytorch and optimized container build time as well as container size.
- Deprecated yaml based configuration to avoid confusion, all configurations are now environment variable based.
- Removed requirement of hardcoding `NVIDIA_API_KEY` in `compose.env` file.
- Upgraded all python dependencies for chain-server and rag-playground services.

### Fixed

- Fixed a bug causing hallucinated answer when retriever fails to return any documents.
- Fixed some accuracy issues for all the examples.


## [0.4.0] - 2024-02-23

### Added

- [New dedicated notebooks](./docs/rag/jupyter_server.md) showcasing usage of cloud based Nvidia AI Playground based models using Langchain connectors as well as local model deployment using Huggingface.
- Upgraded milvus container version to enable GPU accelerated vector search.
- Added support to interact with models behind NeMo Inference Microservices using new model engines `nemo-embed` and `nemo-infer`.
- Added support to provide example specific collection name for vector databases using an environment variable named `COLLECTION_NAME`.
- Added `faiss` as a generic vector database solution behind `utils.py`.

### Changed

- Upgraded and changed base containers for all components to pytorch `23.12-py3`.
- Added langchain specific vector database connector in `utils.py`.
- Changed speech support to use single channel for Riva ASR and TTS.
- Changed `get_llm` utility in `utils.py` to return Langchain wrapper instead of Llmaindex wrappers.

### Fixed

- Fixed a bug causing empty rating in evaluation notebook
- Fixed document search implementation of query decomposition example.

## [0.3.0] - 2024-01-22

### Added

- [New dedicated example](./docs/rag/aiplayground.md) showcasing Nvidia AI Playground based models using Langchain connectors.
- [New example](./RetrievalAugmentedGeneration/README.md#5-qa-chatbot-with-task-decomposition-example----a100h100l40s) demonstrating query decomposition.
- Support for using [PG Vector as a vector database in the developer rag canonical example.](./RetrievalAugmentedGeneration/README.md#deploying-with-pgvector-vector-store)
- Support for using Speech-in Speech-out interface in the sample frontend leveraging RIVA Skills.
- New tool showcasing [RAG observability support.](./tools/observability/)
- Support for on-prem deployment of [TRTLLM based nemotron models.](./RetrievalAugmentedGeneration/README.md#6-qa-chatbot----nemotron-model)

### Changed

- Upgraded Langchain and llamaindex dependencies for all container.
- Restructured [README](./README.md) files for better intuitiveness.
- Added provision to plug in multiple examples using [a common base class](./RetrievalAugmentedGeneration/common/base.py).
- Changed `minio` service's port to `9010`from `9000` in docker based deployment.
- Moved `evaluation` directory from top level to under `tools` and created a [dedicated compose file](./deploy/compose/docker-compose-evaluation.yaml).
- Added an [experimental directory](./experimental/) for plugging in experimental features.
- Modified notebooks to use TRTLLM and Nvidia AI foundation based connectors from langchain.
- Changed `ai-playground` model engine name to `nv-ai-foundation` in configurations.

### Fixed

- [Fixed issue #19](https://github.com/NVIDIA/GenerativeAIExamples/issues/19)


## [0.2.0] - 2023-12-15

### Added

- Support for using [Nvidia AI Playground based LLM models](./docs/rag/aiplayground.md)
- Support for using [Nvidia AI Playground based embedding models](./docs/rag/aiplayground.md)
- Support for [deploying and using quantized LLM models](./docs/rag/llm_inference_server.md#quantized-llama2-model-deployment)
- Support for Kubernetes deployment support using helm charts
- Support for [evaluating RAG pipeline](./tools/evaluation/README.md)

### Changed

- Repository restructing to allow better open source contributions
- [Upgraded dependencies](./RetrievalAugmentedGeneration/Dockerfile) for chain server container
- [Upgraded NeMo Inference Framework container version](./RetrievalAugmentedGeneration/llm-inference-server/Dockerfile), no seperate sign up needed for access.
- Main [README](./README.md) now provides more details.
- Documentation improvements.
- Better error handling and reporting mechanism for corner cases
- Renamed `triton-inference-server` container to `llm-inference-server`

### Fixed

- [Fixed issue #13](https://github.com/NVIDIA/GenerativeAIExamples/issues/13) of pipeline not able to answer questions unrelated to knowledge base
- [Fixed issue #12](https://github.com/NVIDIA/GenerativeAIExamples/issues/12) typechecking while uploading PDF files