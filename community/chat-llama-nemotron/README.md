# Chat with Llama-3.1-Nemotron-Nano-4B-v1.1

A React-based chat interface for interacting with an LLM, featuring RAG (Retrieval-Augmented Generation) capabilities and NVIDIA Dynamo backend serving NVIDIA Llama-3.1-Nemotron-Nano-4B-v1.1.

## Project Structure

```
.
├── frontend/           # React frontend application
├── backend-rag/        # RAG service backend
└── backend-dynamo/     # NVIDIA Dynamo backend service
    └── llm-proxy/      # Proxy server for NVIDIA Dynamo
```

## Prerequisites

- Node.js 18 or higher
- Python 3.8 or higher
- NVIDIA GPU with CUDA support (for LLM serving with NVIDIA Dynamo)
- Docker (optional, for containerized deployment)
- Git

## Configuration

### Frontend

The frontend configuration is managed through YAML files in `frontend/public/config/`:

- `app_config.yaml`: Main application configuration:
  - API endpoints
  - UI settings
  - File upload settings

See [frontend/README.md](frontend/README.md)

### Backend

Each service has its own configuration files:

- RAG backend: see [backend-rag/README.md](backend-rag/README.md)
- LLM Proxy: see [backend-dynamo/llm-proxy/README.md](backend-dynamo/llm-proxy/README.md)
- DynamoDB backend: see [backend-dynamo/README.md](backend-dynamo/README.md)


## Setup

### Llama-3.1-Nemotron-Nano-4B-v1.1 running on a GPU Server

This step should be performed on a machine with a GPU.

Set NVIDIA Dynamo backend running Llama-3.1-Nemotron-Nano-4B-v1.1 following the instruction [backend-dynamo/README.md](backend-dynamo/README.md).

### Local client with a local RAG database

These steps can be performed locally and don't require a GPU.

1. Clone the repository:
   ```bash
   git clone <this-repository-url>
   cd react-llama-client
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Set up backend services:

   For Unix/macOS:
   ```bash
   # RAG Backend
   cd backend-rag
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # LLM Proxy
   cd backend-dynamo/llm-proxy
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

   For Windows:
   ```bash
   # RAG Backend
   cd backend-rag
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt

   # LLM Proxy
   cd backend-dynamo\llm-proxy
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Start the services (each in a new terminal):

   For Unix/macOS:
   ```bash
   # Start frontend (in frontend directory)
   cd frontend
   npm start

   # Start RAG backend (in backend-rag directory)
   cd backend-rag
   source venv/bin/activate
   python src/app.py

   # Start LLM proxy (in backend-dynamo/llm-proxy directory)
   cd backend-dynamo/llm-proxy
   source venv/bin/activate
   python proxy.py
   ```

   For Windows:
   ```bash
   # Start frontend (in frontend directory)
   cd frontend
   npm start

   # Start RAG backend (in backend-rag directory)
   cd backend-rag
   .\venv\Scripts\activate
   python src\app.py

   # Start LLM proxy (in backend-dynamo\llm-proxy directory)
   cd backend-dynamo\llm-proxy
   .\venv\Scripts\activate
   python proxy.py
   ```
