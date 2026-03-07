# Chat with Llama-3.1-Nemotron-Nano-4B-v1.1

A React-based chat interface for interacting with an LLM, featuring RAG (Retrieval-Augmented Generation) capabilities and NVIDIA Dynamo backend serving NVIDIA Llama-3.1-Nemotron-Nano-4B-v1.1.

---

# Project Structure

```
.
├── frontend/           # React frontend application
├── backend-rag/        # RAG service backend
└── backend-dynamo/     # NVIDIA Dynamo backend service
    └── llm-proxy/      # Proxy server for NVIDIA Dynamo
```

---

# Project Knowledge Dashboard (Docling RAG Explorer)

The frontend now includes a **Project Knowledge dashboard** for exploring RAG results and rendering structured **DoclingDocument** content extracted from PDFs.

Location:

```
frontend/src/pages/ProjectKnowledge.js
```

This page allows inspection of FAISS search results and visualization of structured document data extracted with **Docling**.

## Features

### FAISS Search Explorer

Search the RAG vector index directly.

Results display:

- extracted chunk content
- source document name
- page number
- similarity score

Example:

```
Relevance: score 0.564
```

### DoclingDocument Rendering

Structured rendering of:

- section headers
- grouped text blocks
- tables
- pictures with captions

All rendered results are styled using the existing frontend UI layout.

### Query Highlighting

Search terms are highlighted inside rendered results for easier inspection.

### Picture Rendering

Images extracted by Docling are rendered inline with captions.

Supported fields:

```
DoclingDocument.pictures
```

Each picture card displays:

- image
- caption text
- page number

### Clickable Links

URLs appearing inside rendered content are automatically converted into clickable hyperlinks.

Links open in a new tab.

### Source Document Access

Each rendered result includes a button:

```
View Source Document
```

This opens the original document served by the RAG backend.

### Renderer Architecture

The renderer logic is derived from:

```
docling-chunk-renderer/apps/gradio_docling_renderer
```

but implemented in React for integration with the dashboard UI.

---

# RAG Document Pipeline

```
PDF
  ↓
Docling extraction
  ↓
DoclingDocument JSON
  ↓
FAISS vector indexing
  ↓
RAG retrieval
  ↓
React dashboard renderer
```

---

# Prerequisites

- Node.js 18 or higher
- Python 3.8 or higher
- NVIDIA GPU with CUDA support (for LLM serving with NVIDIA Dynamo)
- Docker (optional, for containerized deployment)
- Git

---

# Configuration

## Frontend

Frontend configuration files are located in:

```
frontend/public/config/
```

Main configuration:

```
app_config.yaml
```

Controls:

- API endpoints
- UI settings
- file upload settings

See:

```
frontend/README.md
```

---

## Backend

Each backend service has its own configuration.

### RAG Backend

```
backend-rag/
```

Documentation:

```
backend-rag/README.md
```

### LLM Proxy

```
backend-dynamo/llm-proxy/
```

Documentation:

```
backend-dynamo/llm-proxy/README.md
```

### Dynamo Backend

```
backend-dynamo/
```

Documentation:

```
backend-dynamo/README.md
```

---

# Setup

## Llama-3.1-Nemotron-Nano-4B-v1.1 running on a GPU Server

This step must be performed on a machine with a GPU.

Start the NVIDIA Dynamo backend serving the model by following:

```
backend-dynamo/README.md
```

---

# Local Client with Local RAG Database

These steps can run locally without a GPU.

---

## 1 Clone Repository

```
git clone <this-repository-url>
cd react-llama-client
```

---

## 2 Install Frontend Dependencies

```
cd frontend
npm install
```

---

## 3 Setup Backend Services

### Unix / macOS

```
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

### Windows

```
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

---

# 4 Start Services

Start each component in a separate terminal.

### Unix / macOS

```
# Frontend
cd frontend
npm start

# RAG backend
cd backend-rag
source venv/bin/activate
python src/app.py

# LLM proxy
cd backend-dynamo/llm-proxy
source venv/bin/activate
python proxy.py
```

### Windows

```
# Frontend
cd frontend
npm start

# RAG backend
cd backend-rag
.\venv\Scripts\activate
python src\app.py

# LLM proxy
cd backend-dynamo\llm-proxy
.\venv\Scripts\activate
python proxy.py
```

---

# Notes

- The Project Knowledge dashboard is intended for **debugging and inspecting RAG document structure**.
- It is useful for validating **Docling extraction quality and chunk segmentation**.
- FAISS search results and rendered document sections can be compared directly inside the UI.

