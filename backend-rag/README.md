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

# RAG Backend Service (Jetson FAISS GPU)

This service is the Retrieval-Augmented Generation backend for the chat application.

It is deployed on **NVIDIA Jetson Orin Nano 8GB** and runs as a **Dockerized FastAPI service** with:

- **JetPack 6.x / Ubuntu 22.04**
- **CUDA 12.6**
- **Docker + NVIDIA runtime**
- **FAISS GPU** built from source inside the container
- **Sentence Transformers** for embeddings
- **FastAPI** on port `8001`
- **systemd** for boot-time startup

## Architecture

### High-level flow

1. Documents are uploaded to the backend
2. Text is chunked and embedded
3. Embeddings are stored in a **FAISS index**
4. Queries are embedded and searched against the index
5. Retrieved context is returned to the frontend / LLM stack

### Jetson deployment structure

The Jetson hosts:

- `backend-rag` source repo
- Docker image: `backend-rag:jetson-faiss`
- systemd service: `backend-rag.service`

### Container responsibilities

The Docker image is responsible for:

- installing Python runtime dependencies
- installing a modern CMake version required by FAISS
- building **FAISS GPU** from source
- installing backend Python requirements
- starting the backend with:

```bash
python3 src/app.py

Runtime ports
8001 → backend-rag FastAPI service
8002 → LLM proxy
11434 → Ollama

Repository structure
backend-rag/
├── Dockerfile.jetson
├── README.md
├── requirements.txt
├── index/
├── storage/
└── src/
    ├── app.py
    ├── rag_service.py
    └── config/

Build
docker build --no-cache -f Dockerfile.jetson -t backend-rag:jetson-faiss .

Run
docker build --no-cache -f Dockerfile.jetson -t backend-rag:jetson-faiss .

