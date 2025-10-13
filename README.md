
<h1><img align="center" src="https://github.com/user-attachments/assets/cbe0d62f-c856-4e0b-b3ee-6184b7c4d96f">AI vWS Sizing Advisor</h1>

## Purpose

AI vWS Sizing Advisor helps you determine the optimal NVIDIA vGPU configuration for your AI workloads. Enter your workload requirements (model size, concurrent users, performance needs) and receive validated vGPU profile recommendations including:

- **vGPU Profile** - Recommended profile (e.g., L40S-24Q) based on your workload
- **Resource Requirements** - vCPUs, GPU memory, system RAM needed
- **Performance Estimates** - Expected latency, throughput, and time to first token
- **Live Testing** - Automatically deploy and test your configuration on a VM

## Prerequisites

### Hardware Requirements
- **NVIDIA Certified Server** with supported GPU (L40S, H100, A100, etc.)
- **Hypervisor** supporting NVIDIA vGPU (vSphere, KVM, etc.)
- **vGPU License** (v17.4 or later) - [Get 90-day trial](https://www.nvidia.com/en-us/data-center/products/vgpu/vgpu-software-trial/)

### Advisor Host VM
- **OS:** Ubuntu 22.04 or 24.04
- **vGPU Profile:** 24Q
- **vCPUs:** 16
- **Memory:** 96 GB
- **Storage:** 96 GB

### Test VM (for validation)
- **OS:** Ubuntu 22.04 or 24.04  
- **vGPU Profile:** As recommended by the tool
- **SSH Enabled:** For automatic deployment

### Software Requirements
- **Docker** (v20.10+) - [Install guide](https://docs.docker.com/engine/install/ubuntu/)
- **Docker Compose Plugin** - [Install guide](https://docs.docker.com/compose/install/)
- **Node.js** (v18+) and **npm** - [Install guide](https://nodejs.org/)
- **NGC API Key** - [Join NVIDIA Developer Program](https://developer.nvidia.com/developer-program)
- **HuggingFace Token** - For model access ([Get token](https://huggingface.co/settings/tokens))

## Deployment

### 1. Clone Repository

```bash
git clone https://github.com/anpandacoding/vws-sizing
cd vws-sizing
```

### 2. Set Up NGC Authentication

```bash
export NGC_API_KEY="nvapi-your-key-here"
echo "${NGC_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin
```

### 3. Start RAG Infrastructure

```bash
source deploy/compose/.env
./scripts/start_vgpu_rag.sh --skip-nims
```

This starts:
- Vector database (Milvus)
- vGPU knowledge base (auto-loaded from `./vgpu_docs`)

### 4. Start RAG Server

```bash
docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
```

This starts the RAG API server at http://localhost:8081

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Access the UI at **http://localhost:3000**

### 6. Configure Your Workload

1. **Select Workload Type** - Inference, RAG, Fine-tuning, etc.
2. **Enter Model Details** - Model name, size, quantization
3. **Specify Requirements** - Concurrent users, latency targets, throughput needs
4. **Get Recommendation** - View suggested vGPU profile and resource allocation

### 7. Test Configuration (Optional)

To validate the recommendation on a real VM:

1. Click **"Apply Configuration"**
2. Enter VM credentials:
   - VM IP Address
   - Username
   - Password (used once for SSH key setup)
   - HuggingFace Token
3. Click **"Apply Configuration"**

The tool will:
- Auto-generate SSH keys (`vgpu_sizing_advisor`) if needed
- Deploy vLLM server on your VM
- Run inference tests
- Report actual performance metrics

**Note:** SSH keys are configured automatically. Just enter your password once - the tool handles the rest!

## What You Get

### Sizing Recommendation
- vGPU profile matched to your workload
- CPU, memory, and storage requirements
- Validated against NVIDIA specifications

### Performance Estimates
- Time to First Token (TTFT)
- End-to-end latency
- Throughput (tokens/second)
- Concurrent user support

### Live Validation
- Automated deployment to test VM
- Real performance measurements
- Configuration verification
- Detailed logs for troubleshooting

## Quick Start Example

1. Open http://localhost:3000
2. Select "Inference" workload
3. Enter "meta-llama/Llama-3.1-8B-Instruct"
4. Set "10 concurrent users"
5. Click "Get Recommendation"

The advisor analyzes your requirements and suggests an optimal vGPU configuration with performance estimates.

## Stopping Services

```bash
./scripts/stop_vgpu_rag.sh
```

## Documentation

- **Deployment Logs:** Check debug output in the UI
- **RAG API Docs:** http://localhost:8081/docs
- **Add More Docs:** Place PDFs in `./vgpu_docs` directory

## Troubleshooting

### Backend Issues
```bash
# Restart backend
docker compose -f deploy/compose/docker-compose-rag-server.yaml restart

# View logs
docker logs rag-server
```

### Frontend Issues
```bash
# Restart frontend
cd frontend
npm run dev
```

### SSH Connection Issues
- Ensure VM is accessible on the network
- Check SSH is enabled: `ssh username@vm-ip`
- Verify password is correct

## Coming Soon

We're actively developing new features to enhance the AI vWS Sizing Advisor:

- 🎯 **Fine-Tuning Workload Support** - Sizing recommendations for model fine-tuning scenarios
- 🧪 **Local vLLM Testing** - Test configurations on your local machine before VM deployment
- 🎥 **Demo Video** - Watch a complete walkthrough of the advisor in action


## License

Licensed under the [Apache License, Version 2.0](./LICENSE).

Models governed by [NVIDIA AI Foundation Models Community License](https://docs.nvidia.com/ai-foundation-models-community-license.pdf) and [Llama 3.2 Community License](https://www.llama.com/llama3_2/license/).