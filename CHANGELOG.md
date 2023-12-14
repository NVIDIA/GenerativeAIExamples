# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.2.0] - 2023-12-15

### Added

- Support for using [Nvidia AI Foundational LLM models](./docs/rag/aiplayground.md#using-nvdia-cloud-based-llms)
- Support for using [Nvidia AI Foundational embedding models](./docs/rag/aiplayground.md#using-nvidia-cloud-based-embedding-models)
- Support for [deploying and using quantized LLM models](./docs/rag/llm_inference_server.md#quantized-llama2-model-deployment)
- Support for [evaluating RAG pipeline](./evaluation/README.md)

### Changed

- Repository restructing to allow better open source contributions
- [Upgraded dependencies](./RetrievalAugmentedGeneration/Dockerfile) for chain server container
- [Upgraded NeMo Inference Framework container version](./RetrievalAugmentedGeneration/llm-inference-server/Dockerfile), no seperate sign up needed now for access.
- Main [README](./README.md) now provides more details.
- Documentation improvements.
- Better error handling and reporting mechanism for corner cases.
- Renamed `triton-inference-server` container and service to `llm-inference-server`

### Fixed

- [Fixed issue #13](https://github.com/NVIDIA/GenerativeAIExamples/issues/13) of pipeline not able to answer questions unrelated to knowledge base
- [Fixed issue #12](https://github.com/NVIDIA/GenerativeAIExamples/issues/12) typechecking while uploading PDF files