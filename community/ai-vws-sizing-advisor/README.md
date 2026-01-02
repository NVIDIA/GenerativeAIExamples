# AI vWS Sizing Advisor

## Overview

AI vWS Sizing Advisor is a RAG-powered tool that helps you determine the optimal NVIDIA vGPU sizing configuration for AI workloads on NVIDIA AI Virtual Workstation (AI vWS). Using NVIDIA vGPU documentation and best practices, it provides tailored recommendations for optimal performance and resource efficiency.

Enter your workload requirements and receive validated recommendations including:

- **vGPU Profile** - Recommended profile (e.g., L40S-24Q) based on your workload
- **Resource Requirements** - vCPUs, GPU memory, system RAM needed
- **Performance Estimates** - Expected latency, throughput, and time to first token
- **Live Testing** - Instantly deploy and validate your configuration locally using vLLM containers

The tool differentiates between RAG and inference workloads by accounting for embedding vectors and database overhead. It intelligently suggests GPU passthrough when jobs exceed standard vGPU profile limits.

## Prerequisites

### Hardware
- **GPU:** NVIDIA RTX Pro 6000 Blackwell Server Edition, L40S, L40, L4, or A40
- **GPU Memory:** 24 GB minimum
- **System RAM:** 32 GB recommended
- **Storage:** 50 GB free space

### Software
- **OS:** Ubuntu 22.04 LTS
- **NVIDIA GPU Drivers:** Version 535+

**Quick Install:**
```bash
# Install Docker and npm
sudo apt update && sudo apt install -y docker.io npm

# Add user to docker group (recommended) OR set socket permissions
sudo usermod -aG docker $USER && newgrp docker
# OR: sudo chmod 666 /var/run/docker.sock

# Verify installations
git --version && docker --version && npm --version && curl --version

# Test GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

> **Note:** Docker must be at `/usr/bin/docker` (verified in `deploy/compose/docker-compose-rag-server.yaml`). User must be in docker group or have socket permissions.

### API Keys
- **NVIDIA Build API Key** (Required) - [Get your key](https://build.nvidia.com/settings/api-keys)
- **HuggingFace Token** (Optional) - [Create token](https://huggingface.co/settings/tokens) for gated models

## Deployment

**1. Clone and navigate:**
```bash
git clone https://github.com/NVIDIA/GenerativeAIExamples.git
cd GenerativeAIExamples/community/ai-vws-sizing-advisor
```

**2. Set NGC API key:**
```bash
export NGC_API_KEY="nvapi-your-key-here"
echo "${NGC_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin
```

**3. Start backend services:**
```bash
./scripts/start_app.sh
```
This automatically starts all backend services (Milvus, ingestion, RAG server). First startup takes 3-5 minutes.

**4. Start frontend (in new terminal):**
```bash
cd frontend
npm install
npm run dev
```

## Usage

2. **Select Workload Type:** RAG or Inference

3. **Enter Parameters:**
   - Model name (e.g., `meta-llama/Llama-2-7b-chat-hf`)
   - GPU type
   - Prompt size (input tokens)
   - Response size (output tokens)
   - Quantization (FP16, INT8, INT4)
   - For RAG: Embedding model and vector dimensions

4. **View Recommendations:**
   - Recommended vGPU profiles
   - Resource requirements (vCPUs, RAM, GPU memory)
   - Performance estimates

5. **Test Locally** (optional):
   - Run local inference with a containerized vLLM server
   - View performance metrics
   - Compare actual results versus suggested profile configuration

## Management Commands

```bash
# Service Management
./scripts/status.sh           # Check status of all services
./scripts/restart_app.sh      # Restart RAG backend
./scripts/stop_app.sh         # Stop all services (with Docker cleanup)
./scripts/stop_app.sh --volumes     # Stop services and remove all data
./scripts/stop_app.sh --cleanup-images  # Stop services and clean Docker cache

# Logs
docker logs -f rag-server      # View RAG server logs
docker logs -f ingestor-server # View ingestion logs
```

### Stop Script Options

The stop script automatically performs Docker cleanup operations:
- Removes stopped containers
- Prunes unused volumes
- Cleans up unused networks
- Optionally removes dangling images (`--cleanup-images`)
- Optionally removes all data volumes (`--volumes`)

## Adding Documents to RAG Context

The tool includes NVIDIA vGPU documentation by default. To add your own:

```bash
# Copy document to docs directory
cp your-document.pdf ./vgpu_docs/

# Trigger ingestion
curl -X POST -F "file=@./vgpu_docs/your-document.pdf" http://localhost:8082/v1/ingest
```

**Supported formats:** PDF, TXT, DOCX, HTML, PPTX




## License

Licensed under the Apache License, Version 2.0.

Models governed by [NVIDIA AI Foundation Models Community License](https://docs.nvidia.com/ai-foundation-models-community-license.pdf) and [Llama 3.2 Community License](https://www.llama.com/llama3_2/license/).

---

**Version:** 2.2 (November 2025) - See [CHANGELOG.md](./CHANGELOG.md)

**Support:** [GitHub Issues](https://github.com/NVIDIA/GenerativeAIExamples/issues) | [NVIDIA Forums](https://forums.developer.nvidia.com/)