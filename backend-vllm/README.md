# NVIDIA Dynamo Backend Service

This is the [NVIDIA Dynamo](https://github.com/ai-dynamo/dynamo) backend service for the chat application. It provides the core LLM capabilities using [NVIDIA Llama-3.1-Nemotron-Nano-4B-v1.1](https://huggingface.co/nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1).

**NVIDIA Dynamo** is an open-source high-throughput low-latency inference framework designed for serving generative AI and reasoning models in multi-node distributed environments. Dynamo is designed to be inference engine agnostic (supports TRT-LLM, vLLM, SGLang or others).

**NVIDIA Llama-3.1-Nemotron-Nano-4B-v1.1** is a large language model (LLM) which is a derivative of [nvidia/Llama-3.1-Minitron-4B-Width-Base](https://huggingface.co/nvidia/Llama-3.1-Minitron-4B-Width-Base), which is created from Llama 3.1 8B using the [LLM compression technique](https://arxiv.org/abs/2408.11796) by NVIDIA and offers improvements in model accuracy and efficiency. It is a reasoning model that is post trained for reasoning, human chat preferences, and tasks, such as RAG and tool calling.

## Prerequisites

The LLM Llama-3.1-Nemotron-Nano-4B-v1.1 requires a GPU. Make sure to execute this server application on either a local or a remote workstation featuring an NVIDIA GPU instance. It does not have to be on the same device as the the rag-backedn and the frontend.

- Ubuntu 24.02 (preferred)
- Python 3.12 or higher
- CUDA 12.8 or higher
- CUDA driver 545.23.08 or higher
- Docker 23.x or higher
- Rust 1.86.0

## Setup

Building the Dynamo Base Image.

```bash
# Assuming you have alreday cloned this demo repository. Make sure you're in the backend-dynamo directory
cd backend-dynamo

# Get the source code for Dynamo.
git clone https://github.com/ai-dynamo/dynamo.git

# Switch to the specific state to ensure compatibility
git checkout 14e1d446323266ebc1f14f7569a9b7cddb52d36c

cd dynamo

# Build container for Dynamo serve with VLLM support

# On an x86 machine
./container/build.sh --framework vllm

# On an ARM machine (ex: GB200)
# ./container/build.sh --framework vllm --platform linux/arm64
```

## Configuration

Model configuration for NVIDIA Dymano can be found in `backend-dynamo/config`.

## Running the Service

Firstly, check that no other containers are running. We want to make sure that there is no resiurce concurency.

```bash
docker ps

# Close any running containers
docker stop <container_id>
```

After that, we need to run the services (etcd and NATS) using Docker Compose.

```bash
docker compose -f deploy/metrics/docker-compose.yml up -d
```

Then, let's execute the container which we have built.

```bash
# Allow port so that remote client can discover it. Dynamo will be using port 8000
sudo ufw allow 8000

# Execute the container
./container/run.sh --gpus all -it --framework vllm -v "$(pwd)/../config:/workspace/examples/llm/configs"
```

Once the container has started, inside the container, let's start our server.

```bash
# Navigate to the directory with example scripts
cd examples/llm

# Start the service
dynamo serve graphs.agg:Frontend -f configs/agg_llama_nemotron_4b.yaml
```

## NVIDIA Dynamo API Endpoints

NVIDIA Dynamo supports the following API endpoints:

- **POST `/v1/completions`** — Generate text completions from a prompt.
- **POST `/v1/embeddings`** — Get vector embeddings for input text.
- **POST `/v1/models`** — Manage or load models (implementation-dependent).
- **GET `/v1/models`** — List available models.
- **POST `/v1/tokenizer`** — Tokenize or detokenize text.
- **POST `/v1/images/generations`** — Generate images from text prompts.
- **POST `/v1/audio/transcriptions`** — Transcribe audio to text.
- **POST `/v1/audio/translations`** — Translate audio to text in another language.

In this demo we are using **POST `/v1/completions`**.

## Troubleshooting

Common issues and solutions:

1. CUDA/GPU issues:
   - Verify CUDA installation: `nvidia-smi`
   - Check GPU memory availability
   - Ensure correct CUDA version is installed

2. Model loading issues:
   - Verify model files are present
   - Check model path configuration
   - Ensure sufficient disk space

3. Performance issues:
   - Monitor GPU utilization
   - Check batch size settings
   - Verify memory allocation
