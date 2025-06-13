# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2023-2025, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from rag_service import RAGService
import os
from pathlib import Path
import PyPDF2
import io
import logging
import json
from fastapi.responses import StreamingResponse, FileResponse
from queue import Queue
import threading
import uuid
from datetime import datetime
import docx
from bs4 import BeautifulSoup
from config.config_loader import config_loader

# Load configurations
logger = logging.getLogger(__name__)
logger.info("Loading configurations for FastAPI app...")
app_config = config_loader.get_app_config()
rag_config = config_loader.get_rag_config()
logger.info(f"Loaded app config: {app_config}")
logger.info(f"Loaded RAG config: {rag_config}")

# Configure logging
logging.basicConfig(
    level=getattr(logging, rag_config['logging']['level']),
    format=rag_config['logging']['format']
)

app = FastAPI(
    title=app_config['app']['name'],
    version=app_config['app']['version']
)

logger.info(f"Initialized FastAPI app with title: {app_config['app']['name']}, version: {app_config['app']['version']}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config['cors']['allow_origins'],
    allow_credentials=app_config['cors']['allow_credentials'],
    allow_methods=app_config['cors']['allow_methods'],
    allow_headers=app_config['cors']['allow_headers'],
    expose_headers=app_config['cors']['expose_headers']
)

logger.info(f"Configured CORS with origins: {app_config['cors']['allow_origins']}")

# Initialize RAG service and index directory
INDEX_DIR = Path(app_config['storage']['index_dir'])
STORAGE_DIR = Path(app_config['storage']['documents_dir'])

# Create directories if they don't exist
INDEX_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize RAG service
rag_service = RAGService()

# Initialize job queues dictionary
job_queues: Dict[str, Queue] = {}

# Load or create RAG index
try:
    if INDEX_DIR.exists() and any(INDEX_DIR.iterdir()):
        rag_service.load_index(INDEX_DIR)
        logger.info("Loaded existing RAG index")
    else:
        rag_service.create_index()
        rag_service.save_index(INDEX_DIR)
        logger.info("Created new RAG index")
except Exception as e:
    logger.error(f"Error initializing RAG index: {str(e)}")
    rag_service.create_index()
    rag_service.save_index(INDEX_DIR)
    logger.info("Created new RAG index after error")

# Supported file types and their extensions
SUPPORTED_EXTENSIONS = app_config['supported_files']
logger.info(f"Configured supported file types: {SUPPORTED_EXTENSIONS}")

def get_file_extension(content_type: str) -> str:
    """Get file extension from content type"""
    return SUPPORTED_EXTENSIONS.get(content_type, '')

def is_supported_file(content_type: str) -> bool:
    """Check if file type is supported"""
    return content_type in SUPPORTED_EXTENSIONS

async def process_pdf(content: bytes) -> List[Dict[str, Any]]:
    """Process PDF file and extract text with metadata"""
    pdf_file = io.BytesIO(content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    
    return [{
        "text": text,
        "chunk_type": "pdf"
    }]

async def process_text(content: bytes) -> List[Dict[str, Any]]:
    """Process text file and extract content"""
    text = content.decode('utf-8')
    return [{
        "text": text,
        "chunk_type": "text_file"
    }]

async def process_markdown(content: bytes) -> List[Dict[str, Any]]:
    """Process markdown file and extract content"""
    text = content.decode('utf-8')
    return [{
        "text": text,
        "chunk_type": "markdown"
    }]

async def process_docx(content: bytes) -> List[Dict[str, Any]]:
    """Process Word document and extract content"""
    docx_file = io.BytesIO(content)
    doc = docx.Document(docx_file)
    text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    return [{
        "text": text,
        "chunk_type": "docx"
    }]

async def process_html(content: bytes) -> List[Dict[str, Any]]:
    """Process HTML file and extract content"""
    html = content.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    text = "\n".join(section.text.strip() for section in soup.find_all(['h1', 'h2', 'h3', 'p']) if section.text.strip())
    return [{
        "text": text,
        "chunk_type": "html"
    }]

async def process_file_content(content: bytes, content_type: str) -> List[Dict[str, Any]]:
    """Process file content based on its type"""
    processors = {
        'application/pdf': process_pdf,
        'text/plain': process_text,
        'text/markdown': process_markdown,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': process_docx,
        'text/html': process_html
    }
    
    processor = processors.get(content_type)
    if not processor:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
    
    return await processor(content)

def save_file_bytes(file_bytes: bytes, file_id: str, extension: str):
    file_path = os.path.join(STORAGE_DIR, f"{file_id}{extension}")
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)
    return file_path

@app.get("/")
async def root():
    return {"message": "Backend server is running"}

@app.get("/api/rag-status")
async def get_rag_status():
    """Get the current status of the RAG index"""
    try:
        count = rag_service.get_document_count()
        return {
            "document_count": count,
            "is_empty": count == 0
        }
    except Exception as e:
        logger.error(f"Error getting RAG status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clear-rag")
async def clear_rag():
    """Clear RAG index and remove all stored files"""
    try:
        # Get counts before clearing
        deleted_chunks = rag_service.get_document_count()
        deleted_documents = rag_service.get_unique_document_count()
        
        # Clear RAG index
        rag_service.clear()
        rag_service.save_index(INDEX_DIR)
        
        # Clear stored files
        if STORAGE_DIR.exists():
            for file in STORAGE_DIR.iterdir():
                if file.is_file():
                    file.unlink()
        
        logger.info(f"Successfully cleared RAG index. Deleted {deleted_chunks} chunks and {deleted_documents} documents.")
        return {
            "message": f"Successfully cleared RAG index. Deleted {deleted_chunks} chunks and {deleted_documents} documents.",
            "deleted_chunks": deleted_chunks,
            "deleted_documents": deleted_documents
        }
    except Exception as e:
        logger.error(f"Error clearing RAG index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    try:
        logger.info(f"Received upload request for {len(files)} files")
        job_id = str(uuid.uuid4())
        job_queue = Queue()
        job_queues[job_id] = job_queue

        processed_chunks = []
        saved_files = []
        chunks_metadata = []
        
        for file in files:
            logger.info(f"Processing file: {file.filename} (type: {file.content_type})")
            
            if not is_supported_file(file.content_type):
                logger.warning(f"Unsupported file type: {file.content_type}")
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
            
            file_id = None
            extension = None
            
            try:
                file_id = str(uuid.uuid4())
                extension = get_file_extension(file.content_type)
                file_bytes = await file.read()  # Read once

                # Save the file
                file_path = save_file_bytes(file_bytes, file_id, extension)
                saved_files.append((file_id, extension))
                logger.info(f"Saved file with ID: {file_id}")

                # Process file content
                chunks = await process_file_content(file_bytes, file.content_type)
                
                if not chunks:
                    logger.warning(f"No content extracted from file: {file.filename}")
                    # Remove the saved file if no content was extracted
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(status_code=400, detail=f"No content could be extracted from file: {file.filename}")
                
                # Process each chunk
                for chunk in chunks:
                    chunk_id = str(uuid.uuid4())
                    source_file = f"{file_id}{extension}"
                    chunk_metadata = {
                        "chunk_id": chunk_id,
                        "text": chunk["text"],
                        "source_file": source_file,
                        "chunk_type": chunk["chunk_type"],
                        "page_number": chunk.get("page_number", 1),
                        "upload_time": datetime.now().isoformat()
                    }
                    
                    chunks_metadata.append(chunk_metadata)
                    processed_chunks.append(chunk["text"])
                
                logger.info(f"Successfully processed file: {file.filename} with {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                # Remove the saved file if processing failed
                if file_id and extension:
                    file_path = os.path.join(STORAGE_DIR, f"{file_id}{extension}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                raise HTTPException(status_code=400, detail=f"Error processing file {file.filename}: {str(e)}")

        if not processed_chunks:
            raise HTTPException(status_code=400, detail="No valid content found in any of the uploaded files")

        logger.info(f"Starting background processing for {len(processed_chunks)} chunks from {len(saved_files)} files")
        # Start processing in a background thread
        thread = threading.Thread(target=process_documents, args=(processed_chunks, chunks_metadata, job_queue))
        thread.start()
        logger.info(f"Background processing started with job_id: {job_id}")

        return {
            "job_id": job_id,
            "saved_files": [f"{fid}{ext}" for fid, ext in saved_files],
            "message": f"Successfully saved {len(saved_files)} files and started processing"
        }
        
    except HTTPException as he:
        logger.error(f"HTTP error in upload endpoint: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/upload/progress/{job_id}")
async def upload_progress(job_id: str):
    return StreamingResponse(progress_generator(job_id), media_type="text/event-stream")

class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = None  # Will use rag_config['search']['default_k'] if not provided
    use_rag: bool = rag_config['search']['use_rag']

@app.post("/api/search")
async def search(request: SearchRequest):
    try:
        logger.info(f"Search request received: {request.query} (use_rag: {request.use_rag})")
        if request.use_rag:
            results = rag_service.search(request.query, request.k)
        else:
            # If RAG is disabled, return an empty result
            results = []
        return {"results": results}
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def progress_generator(job_id: str):
    """Generate progress updates for SSE"""
    job_queue = job_queues.get(job_id)
    if not job_queue:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid job id'})}\n\n"
        return
    
    try:
        while True:
            progress = job_queue.get()
            yield f"data: {json.dumps(progress)}\n\n"
            
            # Break the loop on completion or error
            if progress["type"] in ["complete", "error"]:
                # Clean up the job queue
                del job_queues[job_id]
                break
    except Exception as e:
        logger.error(f"Error in progress generator: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        if job_id in job_queues:
            del job_queues[job_id]

def process_documents(documents: List[str], metadata: List[Dict[str, Any]], job_queue: Queue):
    """Process documents in background with progress updates"""
    try:
        total_docs = len(documents)
        job_queue.put({
            "type": "processing",
            "stage": "start",
            "progress_percent": 0,
            "message": "Starting document processing..."
        })
        
        # Add documents with progress tracking
        for i, (doc, meta) in enumerate(zip(documents, metadata), 1):
            # Calculate progress percentage
            progress_percent = int((i - 1) / total_docs * 100)
            
            # Update progress before processing each document
            job_queue.put({
                "type": "processing",
                "stage": "progress",
                "progress_percent": progress_percent,
                "message": f"Processing document {i} of {total_docs}..."
            })
            
            # Process the document
            rag_service.add_documents([doc], [meta])
            
            # Update progress after processing
            progress_percent = int(i / total_docs * 100)
            job_queue.put({
                "type": "processing",
                "stage": "progress",
                "progress_percent": progress_percent,
                "message": f"Processed document {i} of {total_docs}"
            })
        
        # Save the index
        job_queue.put({
            "type": "processing",
            "stage": "progress",
            "progress_percent": 95,
            "message": "Saving index..."
        })
        rag_service.save_index(INDEX_DIR)
        
        # Send completion
        job_queue.put({
            "type": "complete",
            "message": "Processing complete",
            "progress_percent": 100,
            "stage": "complete"
        })
        
    except Exception as e:
        logger.error(f"Error in process_documents: {str(e)}")
        job_queue.put({
            "type": "error",
            "message": str(e)
        })
        # Ensure the queue is cleaned up even on error
        if job_id in job_queues:
            del job_queues[job_id]

@app.get("/api/document/{file_id}")
async def get_document(file_id: str):
    """Serve a stored document for viewing in browser"""
    try:
        # Validate file_id
        if not file_id or not file_id.strip():
            raise HTTPException(status_code=400, detail="Invalid file ID")
            
        # Check if file exists
        file_path = os.path.join(STORAGE_DIR, file_id)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Document not found: {file_id}")
            
        # Check if it's a file (not a directory)
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail="Invalid document path")
            
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Document is empty")
            
        # Determine content type based on file extension
        content_type = "application/pdf"  # Default to PDF
        if file_id.endswith('.txt'):
            content_type = "text/plain"
        elif file_id.endswith('.md'):
            content_type = "text/markdown"
        elif file_id.endswith('.docx'):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_id.endswith('.html'):
            content_type = "text/html"
            
        return FileResponse(
            file_path,
            media_type=content_type,
            filename=file_id,
            headers={
                "Content-Disposition": f"inline; filename={file_id}"
            }
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error serving document {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8001) 