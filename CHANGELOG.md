# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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