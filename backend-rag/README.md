# Backend RAG (Jetson FAISS)

## Overview
Lightweight FAISS-based RAG backend running on Jetson with Docker (GPU enabled).
Single active service on port **8001**.

## Key Changes
- Removed duplicate picture-index APIs
- Single backend service (8001 only)
- Host-mounted storage (persistent across restarts)
- Cleaned project structure

## Storage
- Active FAISS data dir: `faiss-general/`
- Optional future dir: `faiss-pictures/`

## Docker Run (Jetson)

docker run -d \
  --name backend-rag \
  --restart unless-stopped \
  --runtime nvidia \
  -p 8001:8001 \
  -v /home/hp/projects/chat-llama-nemotron/backend-rag:/home/hp/projects/chat-llama-nemotron/backend-rag \
  backend-rag:jetson-faiss-host

## Docker Compose
Docker Compose up -d

# RAG Backend Service

This is the RAG (Retrieval-Augmented Generation) backend service for the chat application. It provides APIs for document processing, search, and chat functionality using FAISS for vector similarity search and Sentence Transformers for text embeddings.


## Prerequisites

- Python 3.8 or higher
- NVIDIA GPU with CUDA support (optional, for faster processing)
- Sufficient disk space for document storage and vector indices

## Setup

For Unix/macOS:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

For Windows:
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The service can be configured through the configuration files: 

- `src/config/app_config.yaml`
- `src/config/rag_config.yaml`


## Running the Service

For Unix/macOS:
```bash
# Make sure you're in the backend-rag directory
cd backend-rag

# Activate the virtual environment if not already activated
source venv/bin/activate

# Start the server
python src/app.py
```

For Windows:
```bash
# Make sure you're in the backend-rag directory
cd backend-rag

# Activate the virtual environment if not already activated
.\venv\Scripts\activate

# Start the server
python src\app.py
```

## Architecture

This service implements a RAG (Retrieval-Augmented Generation) system that:
1. Processes and chunks documents
2. Generates embeddings 
3. Stores vectors in a FAISS index
4. Provides semantic search capabilities