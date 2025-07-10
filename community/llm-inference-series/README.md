# LLM Inference Series: Performance, Optimization & Deployment with LLMs

This repository supports a video + notebook series exploring how to run, optimize, and serve Large Language Models (LLMs) with a focus on latency, throughput, user experience (UX), and NVIDIA GPU acceleration.

All notebooks run in a shared container environment based on NVIDIA's TensorRT-LLM stack with a PyTorch backend.

## Getting started

Clone this project

```bash
git clone <this-repository-url>
cd <this-repository-directory>
```

Assuming, you are in your working directory, save the current path

```bash
export ROOT_DIR=$(pwd)
```

Now execute the container:

```bash
export PROJECT_DIR=$ROOT_DIR/community/llm-inference-series
export HF_CACHE_DIR=$ROOT_DIR/community/huggingface

mkdir -p "$HF_CACHE_DIR"

# Run container
docker run --gpus all -it --ipc=host \
  -v "$PROJECT_DIR":/workspace \
  -v "$HF_CACHE_DIR":/hf_cache \
  -p 8888:8888 \
  -e HF_HOME=/hf_cache \
  -e LOCAL_UID=$(id -u) \
  -e LOCAL_GID=$(id -g) \
  nvcr.io/nvidia/tensorrt-llm/release:0.21.0rc1 \
  bash -c '
    groupadd -g $LOCAL_GID hostgrp 2>/dev/null || true
    useradd -u $LOCAL_UID -g $LOCAL_GID -M -d /workspace hostusr 2>/dev/null || true

    pip install --no-cache-dir -r /workspace/requirements.txt

    su hostusr -c "cd /workspace && HOME=/workspace HF_HOME=/hf_cache \
      jupyter lab --ip=0.0.0.0 --port=8888 --no-browser"
  '
```

Open Jupyter in your browser: http://localhost:8888 and use the token shown in the container logs. In the opened Jupyter Lab environment, navigate to a corresponding episode.

## 🎥 Episode Guide

✅ Episode 1: Inference 101 – Latency, Throughput & UX

Folder: `01_inference_101/`

What you'll learn:

- What LLM inference means
- Latency vs tokens/sec vs p99: how and why they differ
- When latency matters and how to measure it
- How to visualize and interpret performance metrics

👉 Watch Episode 1 (YouTube link coming soon)

🔜 Stay tuned for updates as each episode is released!