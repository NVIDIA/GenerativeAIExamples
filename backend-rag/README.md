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
