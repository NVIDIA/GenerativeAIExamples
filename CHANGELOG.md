## Changelog
All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.


## [2.0.0] - 2025-03-18

This release adds support for multimodal documents using [Nvidia Ingest](https://github.com/NVIDIA/nv-ingest) including support for parsing PDFs, Word and PowerPoint documents. It also significantly improves accuracy and perf considerations by refactoring the APIs, architecture as well as adds a new developer friendly UI.

### Added
- Integration with Nvingest for ingestion pipeline, the unstructured.io based pipeline is now deprecated.
- OTEL compatible [observability and telemetry support](./docs/observability.md).
- API refactoring. Updated schemas [here](./docs/api_reference/).
  - Support runtime configuration of all common parameters. 
  - Multimodal citation support.
  - New dedicated endpoints for deleting collection, creating collections and reingestion of documents
- [New react + nodeJS based UI](./frontend/) showcasing runtime configurations
- Added optional features to improve accuracy and reliability of the pipeline, turned off by default. Best practices [here](./docs/accuracy_perf.md)
  - [Self reflection support](./docs/self-reflection.md)
  - [NeMo Guardrails support](./docs/nemo-guardrails.md)
  - [Hybrid search support using Milvus](./docs/hybrid_search.md)
- [Brev dev](https://developer.nvidia.com/brev) compatible [notebook](./notebooks/launchable.ipynb)
- Security enhancements and stability improvements

### Changed
- - In **RAG v1.0.0**, a single server managed both **ingestion** and **retrieval/generation** APIs. In **RAG v2.0.0**, the architecture has evolved to utilize **two separate microservices**.
- [Helm charts](./deploy/helm/) are now modularized, seperate helm charts are provided for each distinct microservice.
- Default settings configured to achieve a balance between accuracy and perf.
  - [Default flow uses on-prem models](./docs/quickstart.md#deploy-with-docker-compose) with option to switch to API catalog endpoints for docker based flow.
  - [Query rewriting](./docs/query_rewriter.md) uses a smaller llama3.1-8b-instruct and is turned off by default.
  - Support to use conversation history during retrieval for low-latency  multiturn support.

### Known Issues
- The `rag-playground` container needs to be rebuild if the `APP_LLM_MODELNAME`, `APP_EMBEDDINGS_MODELNAME` or `APP_RANKING_MODELNAME` environment variable values are changed.
- Optional features reflection, nemoguardrails and image captioning are not available in helm based deployment.
- Uploading large files with .txt extension may fail during ingestion, we recommend splitting such files into smaller parts, to avoid this issue.

A detailed guide is available [here](./docs/migration_guide.md) for easing developers experience, while migrating from older versions.

## [1.0.0] - 2025-01-15

### Added

- First release.

