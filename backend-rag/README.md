# Backend RAG (Jetson FAISS)

## Overview
Lightweight FAISS-based RAG backend running on Jetson with Docker.
Single active service on port **8001**.

## Key Changes
- Removed duplicate picture-index APIs
- Single backend service (8001 only)
- Host-mounted storage
- Cleaned project structure

## Storage
- Active FAISS data dir: `faiss-general/`
- Optional future dir: `faiss-pictures/`

## Directory Structure
```text
.
./backend-rag-jetson-faiss.tar.gz
./docker-compose.yml
./Dockerfile.jetson
./.gitignore
./index
./index/documents.json
./index/faiss.index
./projects.cfg
./README.md
./requirements.txt
./src
./src/app.py
./src/config
./src/__pycache__
./src/rag_service.py
./src/requirements.txt
./storage
./storage/documents
./.venv
./.venv/bin
./.venv/Dockerfile.jetson
./.venv-gpu
./.venv-gpu/bin
./.venv-gpu/lib
./.venv-gpu/lib64
./.venv-gpu/pyvenv.cfg
./.venv-gpu/share
./.venv/include
./.venv/lib
./.venv/lib64
./.venv/pyvenv.cfg
./.venv/share
```

## Docker Run
```bash
docker run -d \
  --name backend-rag \
  --restart unless-stopped \
  --runtime nvidia \
  -p 8001:8001 \
  -v /home/hp/projects/chat-llama-nemotron/backend-rag:/home/hp/projects/chat-llama-nemotron/backend-rag \
  backend-rag:jetson-faiss-host
```

## API
- `GET /api/rag-status`
- `POST /api/upload`

## Notes
- Persistence uses host bind mount
- Focused on single backend on 8001
