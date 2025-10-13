
<h1><img align="center" src="https://github.com/user-attachments/assets/cbe0d62f-c856-4e0b-b3ee-6184b7c4d96f">AI vWS Sizing Advisor</h1>

## Introduction

AI vWS Sizing Advisor is designed explicitly for setting up the right Virtual Environment for diverse AI use cases - such as sizing NIMs, different LLMs, setting up environments for workloads such as inferencing, RAG, and fine-tuning. By leveraging a RAG architecture, the Advisor is able to take inputs on your AI workload and translate them into the exact tested vGPU configuration.

Please refer to this guide to verify that all required software and development tools are properly installed and configured prior to initiating the deployment process.

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
  - [Required Software](#required-software)
  - [Required Hardware](#required-hardware)
- [Deployment Guide](#deployment-guide)
  - [Virtual Machine Configuration](#virtual-machine-vm-configuration)
  - [Repository Setup](#repository-setup)
  - [NVIDIA Developer Program Setup](#nvidia-developer-program-setup)
  - [Deployment Steps](#deployment-steps)
  - [HuggingFace API Setup](#huggingface-api-setup)
- [Overview](#overview)
- [Key Features](#key-features)
- [Target Audience](#target-audience)
- [Software Components](#software-components)
- [Technical Diagram](#technical-diagram)
- [Available Customizations](#available-customizations)
- [Inviting the community to contribute](#inviting-the-community-to-contribute)
- [License](#license)
- [Terms of Use](#terms-of-use)

## Prerequisites

### Required Software

Running this toolkit on Linux-based virtual workstations:

- **NVIDIA vGPU Software**: vGPU version 17.4 or later
- **Hypervisor**: vGPU supported hypervisors
- **VM Operating System**: Ubuntu 24.04 or Ubuntu 22.04
- **Minimum system requirements**: 16 vCPU, 24 GB system memory, 96 GB storage 
- **Recommended vGPU profile**: 24Q
- [Download Docker for Ubuntu here](https://docs.docker.com/engine/install/ubuntu/) (v20.10+)
- [Download Docker Compose Plugin here](https://docs.docker.com/compose/install/)
- [Activate, download, and install your RTX Virtual Workstation licenses](https://docs.nvidia.com/grid/latest/grid-licensing-user-guide/)
- [Join the NVIDIA Developer Program](https://developer.nvidia.com/developer-program) to access NVIDIA NIM for Developers

> **Important**: Don't have an NVIDIA vGPU license yet? [Request a free 90-day evaluation license](https://www.nvidia.com/en-us/data-center/products/vgpu/vgpu-software-trial/)

### Required Hardware

NVIDIA Certified systems with any supported GPU with a 24Q profile

## Deployment Guide

> **Note**: Although this guide uses vCenter, NVIDIA AI vWS can be deployed on any NVIDIA vGPU-supported hypervisor. It's assumed that all vWS requirements, including licensing, are already configured.

### Virtual Machine (VM) Configuration

**Advisor Download**: Set up a Linux VM for creating the Advisor with the following configuration:
- vCPU - 16 CPU
- Memory - 96 GB
- vGPU Profile - 24Q

**Verification Step**: Set up a Linux VM based on the Advisor's Recommendation. To validate that this VM is properly configured run the following command:
```bash
nvidia-smi
```

At this point, the VM setup is complete. The installation guide for Ubuntu can be found [here](https://ubuntu.com/server/docs/install/step-by-step).

### Repository Setup

**GitHub Repository**: https://github.com/NVIDIA-AI-Blueprints/rag

1. Clone the repository onto your IDE's terminal:
   ```bash
   git clone https://github.com/anpandacoding/vws-sizing
   cd vws-sizing
   ```

2. Within the shell, run the following commands (make sure you are in the workspace top root):
   ```bash
   export NGC_API_KEY="nvapi-your-key-here"

   # Authenticate to NVIDIA NGC Registry
   echo "${NGC_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin

   source deploy/compose/.env

   # Start core service
   ./scripts/start_vgpu_rag.sh --skip-nims

   ℹ️  Access URLs:
   • RAG Playground: http://localhost:8090
   • RAG API: http://localhost:8081
   • Ingestor API: http://localhost:8082
   • Milvus Console: http://localhost:9011

   ℹ️  vGPU Knowledge Base:
   • Collection: vgpu_knowledge_base
   • Status: All PDFs from ./vgpu_docs are automatically loaded
   • No manual collection selection needed!

   ℹ️  To add more vGPU documentation:
   1. Place PDF files in: ./vgpu_docs
   2. Re-run bootstrap: docker compose -f /home/nvadmin/Desktop/ai-vws-sizing-tool/deploy/compose/docker-compose-bootstrap.yaml up

   ℹ️  To stop all services:
   /home/nvadmin/Desktop/ai-vws-sizing-tool/scripts/stop_vgpu_rag.sh

   - Local:        http://localhost:3000
   - Network:      http://10.185.118.27:3000
   ```

### NVIDIA Developer Program Setup

To Obtain NVIDIA Developer Program Membership and a Personal API Key:

1. Visit the [NVIDIA Developer Program page](https://developer.nvidia.com/developer-program), click on Join and sign up for an NVIDIA account.
2. Use the NVIDIA Developer Program credential to log into [NVIDIA NGC Catalog](https://catalog.ngc.nvidia.com/)
3. Click the account name at the top right. In the drop-down menu, select Setup.
4. Click on "Generate API Key" then click on "+ Generate Personal Key"
5. Enter the key name and expiration. Under Services Included, make sure NGC Catalog is selected.
6. Once your personal API key is generated, save the key that is required for accessing NVIDIA NIMs during the subsequent deployment phase.

### Easy VM Access - Automatic SSH Setup

**No manual setup required!** The tool automatically configures secure SSH keys for you.

#### How It Works

1. **First Time Connection:**
   - Enter your VM username and password in the UI
   - The tool automatically generates SSH keys `vgpu_sizing_advisor` (if needed)
   - Copies the public key to your VM
   - All done automatically in seconds!

2. **Subsequent Connections:**
   - Uses secure SSH key authentication (`~/.ssh/vgpu_sizing_advisor`)
   - No password needed anymore
   - Faster and more secure

#### Manual Setup (Optional)

If you prefer to set up SSH keys manually or if automatic setup fails:

```bash
# Generate custom SSH key pair for vGPU sizing tool
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vgpu_sizing_advisor -N ""

# Copy to your VM (requires password once)
ssh-copy-id -i ~/.ssh/vgpu_sizing_advisor.pub username@vm-ip-address

# Test connection (should work without password)
ssh -i ~/.ssh/vgpu_sizing_advisor username@vm-ip-address
```

**Note:** The tool automatically generates and copies SSH keys using pure Python (subprocess + tempfile) and bash with SSH_ASKPASS. **ZERO external dependencies, no GPL libraries (no sshpass, no pexpect), 100% Apache-compatible!**

### Deployment Steps

#### Launch the Local Server

1. Start the local web server:
   ```bash
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

2. Run the frontend in development mode:
   
   The web interface is built with React and Next.js. To run the frontend in development mode:
   
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   
   The frontend will be available at http://localhost:3000 and provides an intuitive interface for:
   - Configuring AI workload parameters
   - Receiving vGPU sizing recommendations
   - Viewing detailed capacity calculations and performance estimates
   - Exploring recommendation citations and sources


#### Configure Your Workload

1. In the UI, select the AI workload type (Inference, RAG, etc.)
2. Fill in model details and any other parameters needed
3. Once the build is completed, click on the Citations tab (bottom left). Expand any entry with "Click to view details" to see the exact docs or benchmarks the AI used for its recommendation.

#### What's in the Recommendation?

- **vGPU Profile**: Suggested vGPU (e.g., 48Q on L40S) based on model memory and concurrency
- **GPU Memory**: Required memory (including model, KV cache, overhead)
- **System RAM**: Calculated based on inference load and user count (rule of thumb: Model Memory × 2.5 + overhead)
- **vCPUs**: Computed from system RAM (e.g., 1 vCPU per 4 GB)
- **Expected TTFT**: Estimated Time to First Token
- **Latency**: Predicted performance metrics under your config

### HuggingFace API Setup

To Obtain HuggingFace API Key + Access Permissions:

1. You must select the first two options in the User Permissions Section: 
   - 'public gated repositories'
   - 'repos under your personal namespace'

2. In the 'Apply Configuration', locate the input field
3. Paste or enter your credentials
4. The VM IP Address must source a VM that must fit the recommendation
5. Start the Environment Container
6. Apply Configuration

This spins up the sandbox that runs your model microservice on the VM. Once the service container is started, you will receive a detailed log.

## Overview

This blueprint serves as a reference solution for a foundational Retrieval Augmented Generation (RAG) pipeline with an integrated AI vWS Sizing Advisor. It combines two key capabilities:

1. **Enterprise RAG Pipeline**: Enable users to ask questions and receive answers based on their enterprise data corpus.
2. **AI vWS Sizing Advisor**: Provide intelligent, validated recommendations for NVIDIA vGPU deployments, including profile validation, capacity calculations, and deployment strategies.

By default, this blueprint leverages locally-deployed NVIDIA NIM microservices to meet specific data governance and latency requirements.
However, you can replace these models with your NVIDIA-hosted models available in the [NVIDIA API Catalog](https://build.nvidia.com).

## Key Features

### Core RAG Features
- Multimodal data extraction support with text, tables, charts, and infographics
- Hybrid search with dense and sparse search
- Multilingual and cross-lingual retrieval
- Reranking to further improve accuracy
- GPU-accelerated Index creation and search
- Multi-turn conversations with opt-in query rewriting
- Multi-session support
- Telemetry and observability
- OpenAI-compatible APIs
- Decomposable and customizable

### vGPU Advisor Features
- Automatic validation of vGPU profiles against NVIDIA specifications
- Accurate VM capacity calculations based on GPU inventory
- Support for heterogeneous GPU configurations
- Intelligent recommendations for vGPU vs. passthrough modes
- Cost-efficiency and performance trade-off analysis
- Integration with official NVIDIA vGPU documentation
- Single pre-loaded knowledge base for simplified operation

## Target Audience

This blueprint is for:

- **IT System Administrators**: Looking for validated vGPU configuration recommendations
- **DevOps Engineers**: Deploying virtualized GPU environments
- **Solution Architects**: Designing GPU-accelerated infrastructure

## Software Components

The following are the default components included in this blueprint:

* NVIDIA NIM Microservices
   * Response Generation (Inference)
      * [nvcr.io/nim/meta/llama-3.1-8b-instruct:1.8.6](https://catalog.ngc.nvidia.com/orgs/nim/teams/meta/containers/llama-3.1-8b-instruct/tags) - The primary NIM microservice used for AI vWS Sizing Advisor
    * Retriever Models
      * [NIM of nvidia/llama-3_2-nv-embedqa-1b-v2]( https://build.nvidia.com/nvidia/llama-3_2-nv-embedqa-1b-v2)
      * [NIM of nvidia/llama-3_2-nv-rerankqa-1b-v2](https://build.nvidia.com/nvidia/llama-3_2-nv-rerankqa-1b-v2)
      * [NeMo Retriever Page Elements NIM](https://build.nvidia.com/nvidia/nemoretriever-page-elements-v2)
      * [NeMo Retriever Table Structure NIM](https://build.nvidia.com/nvidia/nemoretriever-table-structure-v1)
      * [NeMo Retriever Graphic Elements NIM](https://build.nvidia.com/nvidia/nemoretriever-graphic-elements-v1)
      * [PaddleOCR NIM](https://build.nvidia.com/baidu/paddleocr)

  * Optional NIMs

    * [Llama 3.1 NemoGuard 8B Content Safety NIM](https://build.nvidia.com/nvidia/llama-3_1-nemoguard-8b-content-safety)
    * [Llama 3.1 NemoGuard 8B Topic Control NIM](https://build.nvidia.com/nvidia/llama-3_1-nemoguard-8b-topic-control)
    * [Mixtral 8x22B Instruct 0.1](https://build.nvidia.com/mistralai/mixtral-8x22b-instruct)
    * [Llama 3.2 11B Vision Instruct NIM](https://build.nvidia.com/meta/llama-3.2-11b-vision-instruct)
    * [NeMo Retriever Parse NIM](https://build.nvidia.com/nvidia/nemoretriever-parse)

* RAG Orchestrator server - Langchain based
* Milvus Vector Database - accelerated with NVIDIA cuVS
* Ingestion - [Nvidia-Ingest](https://github.com/NVIDIA/nv-ingest/tree/main) is leveraged for ingestion of files. NVIDIA-Ingest is a scalable, performance-oriented document content and metadata extraction microservice. Including support for parsing PDFs, Word and PowerPoint documents, it uses specialized NVIDIA NIM microservices to find, contextualize, and extract text, tables, charts and images for use in downstream generative applications.
* File Types: File types supported by Nvidia-Ingest are supported by this blueprint. This includes `.pdf`, `.pptx`, `.docx` having images. Image captioning support is turned off by default to improve latency, so questions about images in documents will yield poor accuracy. Files with following extensions are supported:

- `bmp`
- `docx`
- `html` (treated as text)
- `jpeg`
- `json` (treated as text)
- `md` (treated as text)
- `pdf`
- `png`
- `pptx`
- `sh` (treated as text)
- `tiff`
- `txt`

We provide Docker Compose scripts that deploy the microservices on a single node.
When you are ready for a large-scale deployment,
you can use the included Helm charts to deploy the necessary microservices.
You use sample Jupyter notebooks with the JupyterLab service to interact with the code directly.

The Blueprint contains sample data from the [NVIDIA Developer Blog](https://github.com/NVIDIA-AI-Blueprints/rag/blob/main/data/dataset.zip) and also some [sample multimodal data](./data/multimodal/).
You can build on this blueprint by customizing the RAG application to your specific use case.

We also provide a sample user interface named `rag-playground`.


## Technical Diagram

  <p align="center">
  <img src="./docs/arch_diagram.png" width="750">
  </p>


The image represents the architecture and workflow. Here's a step-by-step explanation of the workflow from end-user perspective:

1. **User Interaction via RAG Playground or APIs**:
   - Users interact through the **RAG Playground** UI or APIs, sending queries about vGPU configurations or general knowledge base questions
   - For vGPU queries, the system automatically validates profiles and calculates capacities
   - The `POST /generate` API handles both RAG and vGPU advisor functionalities

2. **Query Processing with Enhanced vGPU Support**:
   - The **RAG Server** processes queries using LangChain
   - For vGPU queries, additional validation and calculation modules ensure accurate recommendations
   - Optional components like Query Rewriter and NeMoGuardrails enhance accuracy

3. **Intelligent Document Retrieval**:
   - The system maintains a unified `vgpu_knowledge_base` collection
   - For vGPU queries, it automatically includes baseline documentation and relevant specialized collections
   - The **Retriever** module identifies the most relevant information using the Milvus Vector Database

4. **Enhanced Response Generation**:
   - Responses are generated using NeMo LLM inference
   - For vGPU configurations, additional validation ensures only valid profiles are recommended
   - Capacity calculations and deployment recommendations are included where relevant

## Minimum System Requirements

### OS Requirements
Ubuntu 22.04 OS

### Deployment Options
- [Docker](./docs/quickstart.md#deploy-with-docker-compose)
- [Kubernetes](./docs/quickstart.md#deploy-with-helm-chart)

### Driver versions

- GPU Driver -  530.30.02 or later
- CUDA version - 12.6 or later

### Hardware Requirements
By default, this blueprint deploys the referenced NIM microservices locally. For this, you will require a minimum of:
 - 24Q profile
 
The blueprint can be also modified to use NIM microservices hosted by NVIDIA in [NVIDIA API Catalog](https://build.nvidia.com/explore/discover).

Following are the hardware requirements for each component.
The reference code in the solution (glue code) is referred to as as the "pipeline".

The overall hardware requirements depend on whether you
[Deploy With Docker Compose](./docs/quickstart.md#deploy-with-docker-compose) or [Deploy With Helm Chart](./docs/quickstart.md#deploy-with-helm-chart).


### Hardware requirements for self hosting all NVIDIA NIM microservices

**The NIM and hardware requirements only need to be met if you are self-hosting them with default settings of RAG.**
See [Using self-hosted NVIDIA NIM microservices](./docs/quickstart.md#deploy-with-docker-compose).

- **Pipeline operation**: 1x L40 GPU or similar recommended. It is needed for Milvus vector store database, as GPU acceleration is enabled by default.
- **LLM NIM**: [Nvidia llama-3.3-nemotron-super-49b-v1](https://docs.nvidia.com/nim/large-language-models/latest/supported-models.html#id83)
  - For improved paralleled performance, we recommend 8x or more H100s/A100s for LLM inference.
- **Embedding NIM**: [Llama-3.2-NV-EmbedQA-1B-v2 Support Matrix](https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/support-matrix.html#llama-3-2-nv-embedqa-1b-v2)
  - The pipeline can share the GPU with the Embedding NIM, but it is recommended to have a separate GPU for the Embedding NIM for optimal performance.
- **Reranking NIM**: [llama-3_2-nv-rerankqa-1b-v2 Support Matrix](https://docs.nvidia.com/nim/nemo-retriever/text-reranking/latest/support-matrix.html#llama-3-2-nv-rerankqa-1b-v2)
- **NVIDIA NIM for Image OCR**: [baidu/paddleocr](https://docs.nvidia.com/nim/ingestion/table-extraction/latest/support-matrix.html#supported-hardware)
- **NVIDIA NIMs for Object Detection**:
  - [NeMo Retriever Page Elements v2](https://docs.nvidia.com/nim/ingestion/object-detection/latest/support-matrix.html#nemo-retriever-page-elements-v2)
  - [NeMo Retriever Graphic Elements v1](https://docs.nvidia.com/nim/ingestion/object-detection/latest/support-matrix.html#nemo-retriever-graphic-elements-v1)
  - [NeMo Retriever Table Structure v1](https://docs.nvidia.com/nim/ingestion/object-detection/latest/support-matrix.html#nemo-retriever-table-structure-v1)

## Next Steps

- Follow the [Deployment Guide](#deployment-guide) to set up the AI vWS Sizing Advisor
- See the [OpenAPI Specifications](./docs/api_reference)
- Explore notebooks that demonstrate how to use the APIs [here](./notebooks/)
- Explore [observability support](./docs/observability.md)
- Explore [best practices for enhancing accuracy or latency](./docs/accuracy_perf.md)
- For detailed deployment options, see [Get Started](./docs/quickstart.md)

## Available Customizations

The following are some of the customizations that you can make after you complete the deployment:

- [Change the Inference or Embedding Model](docs/change-model.md)
- [Customize Prompts](docs/prompt-customization.md)
- [Customize LLM Parameters at Runtime](docs/llm-params.md)
- [Support Multi-Turn Conversations](docs/multiturn.md)
- [Enable Self-Reflection to improve accuracy](docs/self-reflection.md)
- [Enable Query rewriting to Improve accuracy of Multi-Turn Conversations](docs/query_rewriter.md)
- [Enable Image captioning support for ingested documents](docs/image_captioning.md)
- [Enable NeMo Guardrails for guardrails at input/output](docs/nemo-guardrails.md)
- [Enable hybrid search for milvus](docs/hybrid_search.md)
- [Enable text-only ingestion of files](docs/text_only_ingest.md)
- [Customize vGPU Advisor Settings](docs/VGPU_SIMPLIFIED_SETUP.md)


## NVIDIA NIM

NVIDIA NIM provides containers to self-host GPU-accelerated inferencing microservices for pretrained and customized AI models across clouds and data centers. NIM microservices expose industry-standard APIs for simple integration into AI applications, development frameworks, and workflows. Built on pre-optimized inference engines from NVIDIA and the community, including NVIDIA® TensorRT™ and TensorRT-LLM, NIM microservices optimize response latency and throughput for each combination of foundation model and GPU. NVIDIA NIM for Developer is the edition used in this toolkit.

The NIM microservices used in this toolkit:
- **Llama 3.1 8B Instruct** - Primary model for generating vGPU sizing recommendations

## Appendix

### Reference Documentation
- [NVIDIA vGPU Deployment Guides](https://docs.nvidia.com/grid/latest/)
- [NVIDIA vGPU Licensing Guide](https://docs.nvidia.com/grid/latest/grid-licensing-user-guide/)
- [AI Workbench Installation Guide](https://docs.nvidia.com/ai-workbench/)

## Inviting the community to contribute

We're posting these examples on GitHub to support the NVIDIA LLM community and facilitate feedback.
We invite contributions!
To open a GitHub issue or pull request, see the [contributing guidelines](./CONTRIBUTING.md).


## License

This NVIDIA NVIDIA AI BLUEPRINT is licensed under the [Apache License, Version 2.0.](./LICENSE) This project will download and install additional third-party open source software projects and containers. Review [the license terms of these open source projects](./LICENSE-3rd-party.txt) before use.

Use of the models in this blueprint is governed by the [NVIDIA AI Foundation Models Community License](https://docs.nvidia.com/ai-foundation-models-community-license.pdf).

## Terms of Use
This blueprint is governed by the [NVIDIA Agreements | Enterprise Software | NVIDIA Software License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and the [NVIDIA Agreements | Enterprise Software | Product Specific Terms for AI Product](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/). The models are governed by the [NVIDIA Agreements | Enterprise Software | NVIDIA Community Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-community-models-license/) and the [NVIDIA RAG dataset](https://github.com/NVIDIA-AI-Blueprints/rag/tree/v2.0.0/data/multimodal) which is governed by the [NVIDIA Asset License Agreement](https://github.com/NVIDIA-AI-Blueprints/rag/blob/main/data/LICENSE.DATA).

The following models that are built with Llama are governed by the [Llama 3.2 Community License Agreement](https://www.llama.com/llama3_2/license/): llama-3.3-nemotron-super-49b-v1, nvidia/llama-3.2-nv-embedqa-1b-v2, and nvidia/llama-3.2-nv-rerankqa-1b-v2.

