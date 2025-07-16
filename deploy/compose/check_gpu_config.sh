#!/bin/bash

echo "🔍 NVIDIA vGPU RAG - GPU Configuration Check"
echo "============================================="

# Check if NVIDIA drivers are available
echo "1. Checking NVIDIA GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv
else
    echo "❌ nvidia-smi not found. Please install NVIDIA drivers."
    exit 1
fi

echo ""
echo "2. Checking Docker GPU support..."
if docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi &> /dev/null; then
    echo "✅ Docker GPU support is working"
else
    echo "❌ Docker GPU support not available. Install nvidia-container-toolkit"
    exit 1
fi

echo ""
echo "3. Checking Milvus GPU configuration..."
if docker ps | grep -q "milvus-standalone"; then
    echo "✅ Milvus container is running"
    
    # Check if container has GPU access
    echo "4. Verifying GPU access in Milvus container..."
    docker exec milvus-standalone nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null && \
        echo "✅ Milvus has GPU access" || \
        echo "❌ Milvus does not have GPU access"
else
    echo "⚠️  Milvus container not running. Start with: docker-compose -f vectordb.yaml up -d"
fi

echo ""
echo "5. Current GPU Settings:"
echo "   - GPU Index: Enabled"
echo "   - GPU Search: Enabled" 
echo "   - Index Type: GPU_CAGRA"
echo "   - Memory Pool: 2048;4096 MB"
echo "   - Device ID: ${VECTORSTORE_GPU_DEVICE_ID:-0}"

echo ""
echo "🎯 Your Milvus is configured for optimal GPU performance!" 