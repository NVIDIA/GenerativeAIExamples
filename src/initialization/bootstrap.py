#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Bootstrap script for automatic vGPU RAG system initialization.
Creates collections and ingests pre-loaded vGPU documentation on startup.
"""

import os
import sys
import asyncio
import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables with defaults
MILVUS_URL = os.getenv("APP_VECTORSTORE_URL", "http://milvus:19530")
INGESTOR_URL = os.getenv("INGESTOR_BASE_URL", "http://ingestor-server:8082")
VGPU_DOCS_PATH = os.getenv("VGPU_DOCS_PATH", "/app/vgpu_docs")
ENABLE_VGPU_BOOTSTRAP = os.getenv("ENABLE_VGPU_BOOTSTRAP", "true").lower() == "true"
BOOTSTRAP_TIMEOUT = int(os.getenv("BOOTSTRAP_TIMEOUT", "300"))  # 5 minutes
MAX_RETRIES = int(os.getenv("BOOTSTRAP_MAX_RETRIES", "10"))
RETRY_DELAY = int(os.getenv("BOOTSTRAP_RETRY_DELAY", "30"))  # 30 seconds

# Single collection configuration - ALL vGPU docs go here
MAIN_COLLECTION = {
    "name": "vgpu_knowledge_base",
    "description": "Complete NVIDIA vGPU documentation knowledge base",
    "docs_path": VGPU_DOCS_PATH  # Will ingest ALL PDFs from vgpu_docs folder
}

class BootstrapError(Exception):
    """Custom exception for bootstrap errors"""
    pass

class VGPUBootstrap:
    """Handles automatic initialization of vGPU RAG system"""
    
    def __init__(self):
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],  # Updated for newer urllib3
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    async def wait_for_services(self):
        """Wait for required services to be healthy"""
        logger.info("Waiting for services to be ready...")
        
        # Wait for Milvus
        await self._wait_for_service(
            f"{MILVUS_URL.replace(':19530', ':9091')}/healthz",
            "Milvus"
        )
        
        # Wait for Ingestor Server
        await self._wait_for_service(
            f"{INGESTOR_URL}/v1/health",
            "Ingestor Server"
        )
        
        logger.info("All services are ready!")
    
    async def _wait_for_service(self, url: str, service_name: str):
        """Wait for a specific service to be healthy"""
        start_time = time.time()
        retries = 0
        
        while retries < MAX_RETRIES:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} is healthy")
                    return
                else:
                    logger.warning(f"❌ {service_name} returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"❌ {service_name} health check failed: {e}")
            
            if time.time() - start_time > BOOTSTRAP_TIMEOUT:
                raise BootstrapError(f"Timeout waiting for {service_name}")
            
            retries += 1
            logger.info(f"Retrying {service_name} health check in {RETRY_DELAY}s... ({retries}/{MAX_RETRIES})")
            await asyncio.sleep(RETRY_DELAY)
        
        raise BootstrapError(f"Failed to connect to {service_name} after {MAX_RETRIES} retries")
    
    async def create_collections(self):
        """Create the single vGPU knowledge base collection"""
        logger.info("Creating vGPU knowledge base collection...")
        
        await self._create_single_collection(MAIN_COLLECTION)
    
    async def _create_single_collection(self, collection_config: Dict[str, Any]):
        """Create a single collection"""
        collection_name = collection_config["name"]
        
        try:
            # Check if collection already exists
            response = self.session.get(f"{INGESTOR_URL}/v1/collections")
            if response.status_code == 200:
                existing_collections = response.json().get("collections", [])
                if any(c.get("collection_name") == collection_name for c in existing_collections):
                    logger.info(f"✅ Collection '{collection_name}' already exists")
                    return
            
            # Create collection - API expects collection names as JSON array in body
            # and other parameters as query parameters
            params = {
                "embedding_dimension": 2048,  # Updated to match actual NVIDIA embedding model dimensions
                "collection_type": "text",
                "search_type": "dense"  # Explicitly set search type to match APP_VECTORSTORE_SEARCHTYPE
            }
            
            response = self.session.post(
                f"{INGESTOR_URL}/v1/collections",
                params=params,
                json=[collection_name],  # Send as JSON array
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Created collection '{collection_name}'")
            else:
                logger.error(f"❌ Failed to create collection '{collection_name}': {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error creating collection '{collection_name}': {e}")
    
    async def ingest_vgpu_documentation(self):
        """Ingest ALL vGPU documentation into the single knowledge base"""
        logger.info("Ingesting all vGPU documentation...")
        
        docs_path = Path(VGPU_DOCS_PATH)
        if not docs_path.exists():
            logger.warning(f"vGPU documentation path {VGPU_DOCS_PATH} does not exist. Skipping documentation ingestion.")
            return
        
        # Debug: List all files in the directory
        logger.info(f"Contents of {docs_path}:")
        for item in docs_path.iterdir():
            logger.info(f"  - {item.name} ({'directory' if item.is_dir() else 'file'})")
        
        # Find ALL PDF files recursively in the vgpu_docs directory
        pdf_files = list(docs_path.rglob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {docs_path}. Skipping ingestion.")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to ingest:")
        for pdf in pdf_files:
            logger.info(f"  - {pdf.name}")
        
        # Check if collection already has documents
        try:
            response = self.session.get(
                f"{INGESTOR_URL}/v1/documents",
                params={"collection_name": MAIN_COLLECTION["name"]}
            )
            
            if response.status_code == 200:
                existing_docs = response.json().get("documents", [])
                if existing_docs:
                    logger.info(f"✅ Collection '{MAIN_COLLECTION['name']}' already has {len(existing_docs)} documents")
                    return
        except Exception as e:
            logger.warning(f"Could not check existing documents: {e}")
        
        # Ingest all PDFs in batches
        batch_size = 10
        for i in range(0, len(pdf_files), batch_size):
            batch_files = pdf_files[i:i+batch_size]
            await self._ingest_pdf_batch(batch_files, MAIN_COLLECTION["name"])
    
    async def _ingest_pdf_batch(self, pdf_files: List[Path], collection_name: str):
        """Ingest a batch of PDF files into the collection"""
        try:
            # Prepare multipart form data
            files = []
            for pdf_file in pdf_files:
                files.append(('documents', (pdf_file.name, open(pdf_file, 'rb'), 'application/pdf')))
            
            metadata = {
                "collection_name": collection_name,
                "blocking": True,
                "split_options": {
                    "chunk_size": 1024,
                    "chunk_overlap": 150
                },
                "embedding_config": {
                    "dimensions": 2048,
                    "model_name": "nvidia/llama-3.2-nv-embedqa-1b-v2"
                }
            }
            
            data = {'data': json.dumps(metadata)}
            
            # Upload documents
            response = self.session.post(
                f"{INGESTOR_URL}/v1/documents",
                files=files,
                data=data,
                timeout=600  # 10 minutes for large documents
            )
            
            # Close file handles
            for _, file_tuple in files:
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()
            
            if response.status_code == 200:
                result = response.json()
                doc_count = result.get("total_documents", 0)
                logger.info(f"✅ Ingested {doc_count} documents into collection '{collection_name}'")
                
                # Wait for embeddings to be generated and documents to be indexed
                logger.info("Waiting for document embeddings to be generated...")
                await asyncio.sleep(10)  # Give extra time for embedding generation
                
                # Verify documents are actually in the collection
                verify_response = self.session.get(
                    f"{INGESTOR_URL}/v1/documents",
                    params={"collection_name": collection_name}
                )
                
                if verify_response.status_code == 200:
                    docs = verify_response.json().get("documents", [])
                    logger.info(f"✅ Verified {len(docs)} documents are now in collection '{collection_name}'")
                else:
                    logger.warning(f"Could not verify document ingestion: {verify_response.text}")
            else:
                logger.error(f"❌ Failed to ingest documents: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error ingesting documents: {e}")
    
    async def _ingest_collection_docs(self, collection_config: Dict[str, Any], docs_base_path: Path):
        """Ingest documentation for a specific collection"""
        collection_name = collection_config["name"]
        docs_subdir = collection_config["docs_subdir"]
        
        docs_path = docs_base_path / docs_subdir
        if not docs_path.exists():
            logger.warning(f"Documentation path {docs_path} does not exist for collection '{collection_name}'. Skipping.")
            return
        
        # Find PDF files in the directory
        pdf_files = list(docs_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {docs_path} for collection '{collection_name}'. Skipping.")
            return
        
        try:
            # Check if collection already has documents
            response = self.session.get(
                f"{INGESTOR_URL}/v1/documents",
                params={"collection_name": collection_name}
            )
            
            if response.status_code == 200:
                existing_docs = response.json().get("documents", [])
                if existing_docs:
                    logger.info(f"✅ Collection '{collection_name}' already has {len(existing_docs)} documents")
                    return
            
            # Prepare multipart form data
            files = []
            for pdf_file in pdf_files:
                files.append(('documents', (pdf_file.name, open(pdf_file, 'rb'), 'application/pdf')))
            
            metadata = {
                "collection_name": collection_name,
                "blocking": True,
                "split_options": {
                    "chunk_size": 1024,
                    "chunk_overlap": 150
                },
                "embedding_config": {
                    "dimensions": 2048,
                    "model_name": "nvidia/llama-3.2-nv-embedqa-1b-v2"
                }
            }
            
            data = {'data': json.dumps(metadata)}
            
            # Upload documents
            response = self.session.post(
                f"{INGESTOR_URL}/v1/documents",
                files=files,
                data=data,
                timeout=600  # 10 minutes for large documents
            )
            
            # Close file handles
            for _, file_tuple in files:
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()
            
            if response.status_code == 200:
                result = response.json()
                doc_count = result.get("total_documents", 0)
                logger.info(f"✅ Ingested {doc_count} documents into collection '{collection_name}'")
            else:
                logger.error(f"❌ Failed to ingest documents into '{collection_name}': {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error ingesting documents into '{collection_name}': {e}")
    
    async def verify_setup(self):
        """Verify that the vGPU RAG system is properly initialized"""
        logger.info("Verifying vGPU RAG system setup...")
        
        try:
            # Check collections
            response = self.session.get(f"{INGESTOR_URL}/v1/collections")
            if response.status_code == 200:
                collections = response.json().get("collections", [])
                collection_names = [c.get("collection_name") for c in collections]
                
                logger.info(f"Available collections: {collection_names}")
                
                # Verify main collection exists
                if MAIN_COLLECTION["name"] not in collection_names:
                    logger.warning(f"❌ Main collection '{MAIN_COLLECTION['name']}' not found!")
                else:
                    logger.info(f"✅ Main collection '{MAIN_COLLECTION['name']}' is available")
                
                    # Check document count using the documents endpoint instead
                    # This is more reliable than checking num_entities which might not be updated yet
                    logger.info("Waiting for document processing to complete...")
                    await asyncio.sleep(5)  # Give time for embeddings to be generated
                    
                    doc_response = self.session.get(
                        f"{INGESTOR_URL}/v1/documents",
                        params={"collection_name": MAIN_COLLECTION["name"]}
                    )
                    
                    if doc_response.status_code == 200:
                        documents = doc_response.json().get("documents", [])
                        logger.info(f"📚 Collection has {len(documents)} documents")
                        
                        # Also check the collection metadata
                        for collection in collections:
                            if collection.get("collection_name") == MAIN_COLLECTION["name"]:
                                entities = collection.get("num_entities", 0)
                                logger.info(f"📊 Collection metadata shows {entities} entities")
                                break
                    else:
                        logger.error(f"Failed to check documents: {doc_response.text}")
                
            else:
                logger.error(f"Failed to verify collections: {response.text}")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")
    
    def create_sample_docs_structure(self):
        """Create vGPU documentation directory"""
        docs_path = Path(VGPU_DOCS_PATH)
        
        if docs_path.exists():
            logger.info("vGPU documentation directory already exists")
            return
        
        logger.info(f"Creating vGPU documentation directory at {docs_path}")
        docs_path.mkdir(parents=True, exist_ok=True)
        
        # Create simple README
        readme_path = docs_path / "README.md"
        readme_content = """# NVIDIA vGPU Documentation

This directory contains ALL NVIDIA vGPU documentation PDFs that will be automatically loaded into the RAG system.

## How to Use

1. **Add PDFs**: Simply place ALL your NVIDIA vGPU documentation PDFs in this directory
   - User guides
   - Installation manuals
   - Hardware specifications
   - Performance guides
   - Best practices
   - ANY vGPU-related PDFs

2. **Automatic Loading**: When the system starts, it will:
   - Create a single knowledge base collection
   - Automatically ingest ALL PDFs found in this directory
   - Make them searchable through the chat interface

3. **No Manual Steps**: You don't need to:
   - Select collections
   - Upload through the UI
   - Configure anything

Just drop your PDFs here and restart the system!

## Supported Files
- *.pdf files (all PDFs in this directory and subdirectories will be loaded)

## Example PDFs to Add
- nvidia_vgpu_software_user_guide.pdf
- vgpu_profile_specifications.pdf
- a40_datasheet.pdf
- l40s_specifications.pdf
- esxi_vgpu_deployment_guide.pdf
- vgpu_sizing_guide.pdf
"""
        readme_path.write_text(readme_content)
        logger.info(f"✅ Created vGPU documentation directory at {docs_path}")

async def main():
    """Main bootstrap function"""
    logger.info("🚀 Starting vGPU RAG System Bootstrap")
    
    if not ENABLE_VGPU_BOOTSTRAP:
        logger.info("Bootstrap disabled via ENABLE_VGPU_BOOTSTRAP=false. Exiting.")
        return
    
    bootstrap = VGPUBootstrap()
    
    try:
        # Create sample documentation structure
        bootstrap.create_sample_docs_structure()
        
        # Wait for services to be ready
        await bootstrap.wait_for_services()
        
        # Create collections
        await bootstrap.create_collections()
        
        # Ingest documentation
        await bootstrap.ingest_vgpu_documentation()
        
        # Verify setup
        await bootstrap.verify_setup()
        
        logger.info("🎉 vGPU RAG System Bootstrap completed successfully!")
        
    except BootstrapError as e:
        logger.error(f"💥 Bootstrap failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error during bootstrap: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 