#!/bin/bash

# Deploy Qwen2.5 Coder 32B Instruct with BF16 precision on 2 GPUs
# Port: 9001 (to avoid conflict with Llama on 9000)
# Note: This model only supports BF16 precision, not FP8

echo "Deploying Qwen2.5 Coder 32B Instruct..."
echo "Configuration: BF16 precision, 4 GPUs (2,3,4,5), Port 9001"
echo "Note: This model only supports BF16 precision (FP8 not available)"

# Set environment variables
export NGC_API_KEY="${NGC_API_KEY:-<PASTE_API_KEY_HERE>}"
export LOCAL_NIM_CACHE="${LOCAL_NIM_CACHE:-$HOME/.cache/nim/qwen-coder}"

# Create cache directory
mkdir -p "$LOCAL_NIM_CACHE"

# Check if NGC_API_KEY is set
if [ "$NGC_API_KEY" = "<PASTE_API_KEY_HERE>" ]; then
    echo "ERROR: Please set your NGC_API_KEY environment variable"
    echo "Run: export NGC_API_KEY=your_actual_api_key"
    exit 1
fi

echo "Using cache directory: $LOCAL_NIM_CACHE"
echo "Starting deployment on port 9001..."

# Deploy with BF16 precision on 4 GPUs (2,3,4,5)
docker run -it --rm \
    --gpus '"device=2,3,4,5"' \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -e CUDA_VISIBLE_DEVICES=2,3,4,5 \
    -e NIM_TENSOR_PARALLEL_SIZE=4 \
    -e NIM_PRECISION=bf16 \
    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
    -u $(id -u) \
    -p 9001:8000 \
    nvcr.io/nim/qwen/qwen2.5-coder-32b-instruct:latest

echo "Qwen2.5 Coder deployment completed."
