## Changelog
All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [2.4] - 2026-01-13
Added the architecture diagram to the readme.

## [2.3] - 2026-01-08

This release focuses on improved sizing recommendations, enhanced Nemotron model integration, and comprehensive documentation updates.

### Added
- **Demo Screenshots** — Added visual examples showcasing the Configuration Wizard, RAG-powered sizing recommendations, and Local Deployment verification
- **Official Documentation Link** — Added link to [NVIDIA vGPU Docs Hub](https://docs.nvidia.com/vgpu/toolkits/sizing-advisor/latest/intro.html) in README

### Changed
- **README Overhaul** — Reorganized documentation to highlight NVIDIA Nemotron models
  - Llama-3.3-Nemotron-Super-49B powers the RAG backend
  - Nemotron-3 Nano 30B (FP8) as default for workload sizing
  - New Demo section with screenshots demonstrating key features

- **Sizing Recommendation Improvements**
  - Enhanced 95% usable capacity rule for profile selection (5% reserved for system overhead)
  - Improved profile selection logic: picks smallest profile where (profile × 0.95) >= workload
  - Better handling of edge cases near profile boundaries

- **GPU Passthrough Logic**
  - Automatic passthrough recommendation when workload exceeds max single vGPU profile
  - Clearer passthrough examples in RAG context (e.g., 92GB on BSE → 2× BSE GPU passthrough)
  - Calculator now returns `vgpu_profile: null` with multi-GPU passthrough recommendation

- **vLLM Local Deployment**
  - Updated to vLLM v0.12.0 for proper NemotronH (hybrid Mamba-Transformer) architecture support
  - Improved GPU memory utilization calculations for local testing
  - Better max-model-len auto-detection (only set when explicitly specified)

- **Chat Improvements**
  - Enhanced conversational mode with vGPU configuration context
  - Better model extraction from sizing responses for follow-up questions
  - Improved context handling for RAG vs inference workload discussions

### Improved
- **Nemotron Model Integration**
  - Default model changed to Nemotron-3 Nano 30B FP8 in configuration wizard
  - Nemotron thinking prompt support for enhanced reasoning
  - Better model matching for Nemotron variants in calculator

## [2.2] - 2025-11-04

### Changed
- Updated branding from "vGPU Sizing Advisor" to "AI vWS Sizing Advisor" throughout UI and documentation
- Improved user-facing verbiage for better clarity and consistency

## [2.1] - 2025-10-20

This release focuses on local deployment improvements, enhanced workload differentiation, and improved user experience with advanced configuration options.

### Added
- **Advanced Configuration Tabs**
  - Enhanced UI with additional configuration options
  - Info buttons and hover tooltips for parameter explanations
  - Contextual guidance to help users understand parameter meanings

- **Workload Safety Validations**
  - Token validation to prevent misconfigured deployments
  - GPU compatibility checks for local deployments
  - Protection against running jobs with incorrect configurations

- **Document Citation References**
  - Fixed ingestion document citation tracking
  - Improved reference accuracy in RAG responses

- **Enhanced Docker Cleanup**
  - Automatic cleanup of stopped containers
  - Prunes unused volumes and networks
  - Optional Docker image and build cache cleanup
  - Improved disk space management

### Changed
- **Local Deployment Architecture**
  - Migrated to vLLM container-based deployment
  - Streamlined local inference setup

- **Calculator Intelligence**
  - GPU passthrough recommendations for workloads exceeding vGPU profile limits
  - Improved sizing suggestions for large-scale deployments

- **Workload Differentiation**
  - Enhanced RAG vs inference workload calculations
  - Embedding vector storage considerations
  - Database overhead factoring for RAG workloads

- **SSH Removal**
  - Completely removed SSH dependency
  - Simplified deployment workflow

### Improved
- **User Interface**
  - Modernized UI components
  - Better visual feedback and status indicators
  - Improved configuration wizard flow

## [2.0] - 2025-10-13

This release focuses on the AI vWS Sizing Advisor with enhanced deployment capabilities, improved user experience, and zero external dependencies for SSH operations.

### Added
- **Dynamic HuggingFace Model Integration**
  - Dynamically populated model list from HuggingFace API
  - Support for any HuggingFace model in vLLM deployment
  - Real-time model validation and availability checking

- **Adjustable Workload Calculation Parameters**
  - Configurable overhead parameters for workload calculations
  - Dynamic GPU utilization settings based on vGPU profile
  - Customizable memory overhead and KV cache calculations
  - User-controllable performance vs resource trade-offs

- **Backend Management Scripts**
  - New `restart_backend.sh` script for container management
  - Automated health checking and verification
  - Clean restart workflow with status reporting

- **Enhanced Debugging Output**
  - Clear, structured deployment logs
  - Real-time progress updates during vLLM deployment
  - SSH key generation path logging
  - Detailed error messages with automatic cleanup
  - Separate debug and deployment result views in UI

- **Comprehensive GPU Performance Metrics**
  - GPU memory utilization reporting
  - Actual vs estimated memory usage comparison
  - Real-time GPU saturation monitoring
  - Time-to-first-token (TTFT) measurements
  - Throughput and latency metrics
  - Inference test results with sample outputs

### Changed
- **SSH Implementation (Zero External Dependencies)**
  - Removed `paramiko` library (LGPL) dependency
  - Removed `sshpass` (GPL) dependency
  - Implemented pure Python solution using built-in `subprocess`, `tempfile`, and `os` modules
  - Auto-generates SSH keys (`vgpu_sizing_advisor`) on first use
  - Automatic SSH key copying to remote VMs using bash with `SSH_ASKPASS`
  - 100% Apache-compatible implementation

- **HuggingFace Token Management**
  - Clear cached tokens before authentication
  - Explicit `huggingface-cli logout` before login
  - Automatic token file cleanup (`~/.huggingface/token`, `~/.cache/huggingface/token`)
  - Immediate deployment failure on invalid tokens
  - Clean error messages without SSH warnings or tracebacks

- **UI/UX Improvements**
  - Updated configuration wizard with better flow
  - Dynamic status indicators (success/failure)
  - Prominent error display with red alert boxes
  - Hover tooltips for SSH key configuration
  - Separate tabs for deployment logs and debug output
  - Copy buttons for log export
  - Cleaner deployment result formatting

### Improved
- **Error Handling**
  - Structured error messages with context
  - Automatic error message cleanup (removes SSH warnings, tracebacks)
  - Better error propagation from backend to frontend
  - Explicit failure states in UI

- **Deployment Process**
  - Automatic SSH key setup on first connection
  - Faster subsequent deployments (key-based auth)
  - More reliable vLLM server startup detection
  - Better cleanup on deployment failure

### Technical Improvements
- Pure Python SSH implementation (no GPL dependencies)
- Apache 2.0 license compliance verified
- Cleaner repository structure
- Comprehensive .gitignore for production readiness
- Removed unnecessary notebooks and demo files

### Security
- SSH key-based authentication (more secure than passwords)
- Automatic key generation with proper permissions (700/600)

## [1.2] - 2025-05-13

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

## [1.1] - 2025-03-18

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

## [1.0] - 2025-01-15

### Added

- First release.