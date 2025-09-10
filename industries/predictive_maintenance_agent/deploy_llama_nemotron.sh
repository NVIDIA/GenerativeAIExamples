#!/bin/bash

# Deploy Llama 3.3 Nemotron Super 49B V1 with FP8 precision on 2 GPUs
# Port: 9000

echo "Deploying Llama 3.3 Nemotron Super 49B V1..."
echo "Configuration: FP8 precision, 2 GPUs (0,1), Port 9000"

# Set environment variables
export NGC_API_KEY="${NGC_API_KEY:-<PASTE_API_KEY_HERE>}"
export LOCAL_NIM_CACHE="${LOCAL_NIM_CACHE:-$HOME/.cache/nim/llama-nemotron}"

# Create cache directory
mkdir -p "$LOCAL_NIM_CACHE"

# Check if NGC_API_KEY is set
if [ "$NGC_API_KEY" = "<PASTE_API_KEY_HERE>" ]; then
    echo "ERROR: Please set your NGC_API_KEY environment variable"
    echo "Run: export NGC_API_KEY=your_actual_api_key"
    exit 1
fi

echo "Using cache directory: $LOCAL_NIM_CACHE"
echo "Starting deployment on port 9000..."

# Deploy with FP8 precision on 2 GPUs (0,1)
CUDA_VISIBLE_DEVICES=0,1 docker run -it --rm \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
    -u $(id -u) \
    -p 9000:8000 \
    -e NIM_TENSOR_PARALLEL_SIZE=2 \
    -e NIM_PRECISION=fp8 \
    nvcr.io/nim/nvidia/llama-3.3-nemotron-super-49b-v1:latest

echo "Llama 3.3 Nemotron deployment completed."
