## Changelog
All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.


## [2.1.0] - 2025-05-13

This release reduces overall GPU requirement for the deployment of the blueprint. It also improves the performance and stability for both docker and helm based deployments.

### Added
- Added non-blocking async support to upload documents API
  - Added a new field `blocking: bool` to control this behaviour from client side. Default is set to `true`
  - Added a new API `/status` to monitor state or completion status of uploaded docs
- Helm chart is published on NGC Public registry.
- Helm chart customization guide is now available for all optional features under [documentation](./README.md#available-customizations).
- Issues with very large file upload has been fixed.
- Security enhancements and stability improvements.

### Changed
- Overall GPU requirement reduced to 2xH100/3xA100.
  - Changed default LLM model to [llama-3_3-nemotron-super-49b-v1](https://build.nvidia.com/nvidia/llama-3_3-nemotron-super-49b-v1). This reduces overall GPU needed to deploy LLM model to 1xH100/2xA100
  - Changed default GPU needed for all other NIMs (ingestion and reranker NIMs) to 1xH100/1xA100
- Changed default chunk size to 512 in order to reduce LLM context size and in turn reduce RAG server response latency.
- Exposed config to split PDFs post chunking. Controlled using `APP_NVINGEST_ENABLEPDFSPLITTER` environment variable in ingestor-server. Default value is set to `True`.
- Added batch-based ingestion which can help manage memory usage of `ingestor-server` more effectively. Controlled using `ENABLE_NV_INGEST_BATCH_MODE` and `NV_INGEST_FILES_PER_BATCH` variables. Default value is `True` and `100` respectively.
- Removed `extract_options` from API level of `ingestor-server`.
- Resolved an issue during bulk ingestion, where ingestion job failed if ingestion of a single file fails.

### Known Issues
- The `rag-playground` container needs to be rebuild if the `APP_LLM_MODELNAME`, `APP_EMBEDDINGS_MODELNAME` or `APP_RANKING_MODELNAME` environment variable values are changed.
- While trying to upload multiple files at the same time, there may be a timeout error `Error uploading documents: [Error: aborted] { code: 'ECONNRESET' }`. Developers are encouraged to use API's directly for bulk uploading, instead of using the sample rag-playground. The default timeout is set to 1 hour from UI side, while uploading.
- In case of failure while uploading files, error messages may not be shown in the user interface of rag-playground. Developers are encouraged to check the `ingestor-server` logs for details.

A detailed guide is available [here](./docs/migration_guide.md) for easing developers experience, while migrating from older versions.

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

