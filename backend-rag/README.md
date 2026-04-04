# Backend RAG (Jetson FAISS)

## Overview
Lightweight FAISS-based RAG backend running on Jetson with Docker (GPU enabled).
Single active service on port **8001**.

## High-Level Architecture

```text
Frontend/UI
    ↓
FastAPI backend (`src/app.py`) on :8001
    ↓
RAG service (`src/rag_service.py`)
    ↓
FAISS index + document metadata
    ↓
Host-backed storage via Docker bind mount
```

## Key Changes
- Removed duplicate picture-index APIs
- Single backend service on **8001**
- Host-mounted storage for persistence
- Cleaned project structure
- Jetson Docker workflow is the active path

## Storage
- Active FAISS data dir: `faiss-general/`
- Optional future dir: `faiss-pictures/`
- Legacy dirs `index/` and `storage/` may still exist during transition

## Directory Structure

```text
backend-rag/
├── Dockerfile.jetson
├── docker-compose.yml
├── projects.cfg
├── README.md
├── requirements.txt
├── faiss-general/
├── faiss-pictures/
├── index/
├── storage/
│   └── documents/
├── scripts/
└── src/
    ├── app.py
    ├── rag_service.py
    └── config/
```

## Docker Run (Jetson)

```bash
docker run -d \
  --name backend-rag \
  --restart unless-stopped \
  --runtime nvidia \
  -p 8001:8001 \
  -v /home/hp/projects/chat-llama-nemotron/backend-rag:/home/hp/projects/chat-llama-nemotron/backend-rag \
  backend-rag:jetson-faiss-host
```

## Docker Compose

```bash
docker compose up -d
```

## API
- `GET /api/rag-status`
- `POST /api/upload`

## Notes
- Requires NVIDIA runtime on Jetson
- Uses host bind mount for persistence
- Avoid container-only data for FAISS/index files
- Current focus is the single backend on **8001**
# Backend RAG (Jetson FAISS)

## Overview
Lightweight FAISS-based RAG backend running on Jetson with Docker (GPU enabled).
Single active service on port **8001**.

## Key Changes
- Removed duplicate picture-index APIs
- Single backend service (8001 only)
- Host-mounted storage (persistent)
- Cleaned project structure

## Storage
- Active FAISS data dir: `faiss-general/`
- Optional: `faiss-pictures/`
- Legacy dirs (`index/`, `storage/`) still supported

## Docker Run (Jetson)
docker run -d \
  --name backend-rag \
  --restart unless-stopped \
  --runtime nvidia \
  -p 8001:8001 \
  -v /home/hp/projects/chat-llama-nemotron/backend-rag:/home/hp/projects/chat-llama-nemotron/backend-rag \
  backend-rag:jetson-faiss-host

## API
- GET /api/rag-status
- POST /api/upload

## Notes
- Requires NVIDIA runtime
- Uses host bind mount
- No container-only data
