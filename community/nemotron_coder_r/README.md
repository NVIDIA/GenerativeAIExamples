# Nemotron Coder-R

Nemotron Coder-R is a demonstration of a coding agen for reasoning-aware code generation powered by the open-source [NVIDIA Nemotron Nano 9B v2 model](https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2). The agent combines the strengths of large language model coding capabilities with a reasoning budget control mechanism, enabling more transparent and efficient problem-solving. 

It is designed to showcase how developers can integrate self-hosted vLLM deployments to run advanced code assistants locally or on their own infrastructure. The demo highlights how NVIDIA Nemotron Nano 9B v2 reasoning features can be applied to software development workflows, making it easier to experiment with streaming, non-streaming, and reasoning-driven code generation in a reproducible environment.

## Features

- **Reasoning Budget Control**: Toggle reasoning on/off and control token budget
- **Streaming Support**: Real-time streaming of responses
- **Code Generation**: AI-powered code generation for various programming languages
- **File Upload Context**: Upload files to provide context for better code generation

## Requirements

- **vLLM server** running with Nemotron Nano 9B v2 model
- **Hugging Face token** to download the model. Get one [here](https://huggingface.co/settings/tokens).
- **Python 3.8+** environment
- **Docker** (optional)

## vLLM Server Setup

### Basic vLLM Installation
```bash
pip install -U "vllm>=0.10.1"
```

Alternativly, you can use Docker to launch a vLLM server. See the instructions below.

## Quick Start

### 1. Start your vLLM server

```bash
vllm serve nvidia/NVIDIA-Nemotron-Nano-9B-v2 \
    --trust-remote-code \
    --mamba_ssm_cache_dtype float32 \
    --max-num-seqs 64 \
    --max-model-len 131072 \
    --host 0.0.0.0 \
    --port 8888
```

Or, if you are using Docker:

```bash
export HF_CACHE_DIR=<your_local_HF_directory>
export HF_TOKEN=<your_HF_token>
export TP_SIZE=1

docker run --runtime nvidia --gpus all --ipc=host \
  -v "$HF_CACHE_DIR":/hf_cache \
  -e HF_HOME=/hf_cache \
  -e "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  -p 8888:8888 \
  vllm/vllm-openai:v0.10.1 \
    --model nvidia/NVIDIA-Nemotron-Nano-9B-v2 \
    --tensor-parallel-size ${TP_SIZE} \
    --trust-remote-code \
    --mamba_ssm_cache_dtype float32 \
    --max-num-seqs 64 \
    --max-model-len 131072 \
    --host 0.0.0.0 \
    --port 8888
```

#### Customize Endpoint
If you're running vLLM on a different port or host, update the `DEFAULT_LOCAL_API` constant in `nemotron_coder_r.py`.


### 2. Setup the Coding Client

Clone this repository

```bash
git clone https://github.com/NVIDIA/GenerativeAIExamples.git
cd GenerativeAIExamples/community/nemotron-coder-r
```

Activate virtual environment and install dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Demo
```bash
streamlit run nemotron_coder_r.py
```

The UI should open in the browser under http://localhost:8501/.

## Example Prompts

Try these built-in examples:
- "Write a Python function to find the longest palindromic substring in a string"
- "Create a recursive function to solve the Tower of Hanoi puzzle"
- "Implement a binary search tree with insertion and search operations"
- "Write a function to validate email addresses using regex"
- "Create a simple web scraper using Python requests and BeautifulSoup"

