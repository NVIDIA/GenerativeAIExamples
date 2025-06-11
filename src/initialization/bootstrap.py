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

# vGPU Collections Configuration
VGPU_COLLECTIONS = [
    {
        "name": "vgpu_baseline",
        "description": "Core NVIDIA vGPU documentation and fundamentals",
        "docs_subdir": "baseline"
    },
    {
        "name": "vgpu_hypervisor", 
        "description": "ESXi, VMware, Citrix hypervisor documentation",
        "docs_subdir": "hypervisor"
    },
    {
        "name": "vgpu_cost_efficiency",
        "description": "Cost optimization and efficiency guides",
        "docs_subdir": "cost_efficiency"
    },
    {
        "name": "vgpu_performance",
        "description": "Performance benchmarks and sizing guides",
        "docs_subdir": "performance"
    },
    {
        "name": "vgpu_a40",
        "description": "NVIDIA A40 GPU-specific documentation",
        "docs_subdir": "gpu_specific/a40"
    },
    {
        "name": "vgpu_l40s",
        "description": "NVIDIA L40S GPU-specific documentation", 
        "docs_subdir": "gpu_specific/l40s"
    },
    {
        "name": "vgpu_l4",
        "description": "NVIDIA L4 GPU-specific documentation",
        "docs_subdir": "gpu_specific/l4"
    },
    {
        "name": "vgpu_sizing",
        "description": "VM sizing and capacity planning guides",
        "docs_subdir": "sizing"
    }
]

# Default collection for backward compatibility
DEFAULT_COLLECTION = {
    "name": "multimodal_data",
    "description": "Default multimodal data collection",
    "docs_subdir": None  # No automatic docs ingestion for this one
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
            method_whitelist=["HEAD", "GET", "POST"],
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
        """Create all required vGPU collections"""
        logger.info("Creating vGPU collections...")
        
        # Include default collection for backward compatibility
        all_collections = [DEFAULT_COLLECTION] + VGPU_COLLECTIONS
        
        for collection_config in all_collections:
            await self._create_single_collection(collection_config)
    
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
            
            # Create collection
            create_data = {
                "collection_names": [collection_name],
                "embedding_dimension": 1024,  # Default for NVIDIA embeddings
                "collection_type": "text"
            }
            
            response = self.session.post(
                f"{INGESTOR_URL}/v1/collections",
                json=create_data,
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Created collection '{collection_name}'")
            else:
                logger.error(f"❌ Failed to create collection '{collection_name}': {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error creating collection '{collection_name}': {e}")
    
    async def ingest_vgpu_documentation(self):
        """Ingest pre-loaded vGPU documentation into collections"""
        logger.info("Ingesting vGPU documentation...")
        
        docs_base_path = Path(VGPU_DOCS_PATH)
        if not docs_base_path.exists():
            logger.warning(f"vGPU documentation path {VGPU_DOCS_PATH} does not exist. Skipping documentation ingestion.")
            return
        
        for collection_config in VGPU_COLLECTIONS:
            if collection_config["docs_subdir"]:
                await self._ingest_collection_docs(collection_config, docs_base_path)
    
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
                
                # Verify vGPU collections exist
                missing_collections = []
                for collection_config in VGPU_COLLECTIONS:
                    if collection_config["name"] not in collection_names:
                        missing_collections.append(collection_config["name"])
                
                if missing_collections:
                    logger.warning(f"Missing vGPU collections: {missing_collections}")
                else:
                    logger.info("✅ All vGPU collections are available")
                
                # Check document counts
                for collection in collections:
                    name = collection.get("collection_name")
                    count = collection.get("num_entities", 0)
                    if name.startswith("vgpu_"):
                        logger.info(f"Collection '{name}': {count} documents")
                
            else:
                logger.error(f"Failed to verify collections: {response.text}")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")
    
    def create_sample_docs_structure(self):
        """Create sample directory structure for vGPU documentation"""
        docs_base_path = Path(VGPU_DOCS_PATH)
        
        if docs_base_path.exists():
            logger.info("vGPU documentation directory already exists")
            return
        
        logger.info(f"Creating sample vGPU documentation structure at {docs_base_path}")
        
        # Create directory structure
        for collection_config in VGPU_COLLECTIONS:
            if collection_config["docs_subdir"]:
                dir_path = docs_base_path / collection_config["docs_subdir"]
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Create README file explaining what docs should go here
                readme_path = dir_path / "README.md"
                readme_content = f"""# {collection_config['name']} Documentation

{collection_config['description']}

## Instructions

Place NVIDIA vGPU PDF documentation files in this directory. The bootstrap process will automatically:
1. Create the `{collection_config['name']}` collection in Milvus
2. Ingest all PDF files from this directory into the collection
3. Process documents through NV-Ingest for text extraction and chunking

## Expected Files

This directory should contain relevant NVIDIA vGPU documentation PDFs such as:
- Installation guides
- User manuals
- Release notes
- Best practices guides
- Hardware compatibility matrices
- Performance benchmarks

## File Naming

Use descriptive names for PDF files. Examples:
- `nvidia_vgpu_software_user_guide.pdf`
- `vgpu_profile_specifications.pdf`
- `hypervisor_installation_guide.pdf`
"""
                readme_path.write_text(readme_content)
        
        # Create main README
        main_readme = docs_base_path / "README.md"
        main_readme_content = """# NVIDIA vGPU Documentation

This directory contains the pre-loaded NVIDIA vGPU documentation that powers the enhanced vGPU RAG system.

## Directory Structure

The documentation is organized into specialized collections for optimal retrieval:

"""
        
        for collection_config in VGPU_COLLECTIONS:
            if collection_config["docs_subdir"]:
                main_readme_content += f"- **{collection_config['docs_subdir']}/**: {collection_config['description']}\n"
        
        main_readme_content += """
## Setup Instructions

1. **Obtain NVIDIA vGPU Documentation**: Download official NVIDIA vGPU documentation PDFs from:
   - NVIDIA Developer Documentation
   - NVIDIA Enterprise Support Portal
   - NVIDIA vGPU Software Documentation

2. **Organize Documentation**: Place PDF files in the appropriate subdirectories based on their content type

3. **Restart Containers**: The bootstrap process will automatically create collections and ingest documents on startup

## Bootstrap Process

When containers start up with `ENABLE_VGPU_BOOTSTRAP=true`, the system will:

1. Wait for all services (Milvus, Ingestor) to be healthy
2. Create all vGPU collections if they don't exist
3. Ingest PDF files from each subdirectory into corresponding collections
4. Verify the setup was successful

## Environment Variables

- `ENABLE_VGPU_BOOTSTRAP`: Enable/disable automatic bootstrap (default: true)
- `VGPU_DOCS_PATH`: Path to vGPU documentation directory (default: /app/vgpu_docs)
- `BOOTSTRAP_TIMEOUT`: Maximum time to wait for services (default: 300 seconds)

## Enhanced RAG Features

With proper documentation loaded, the enhanced vGPU RAG system provides:

- **Multi-collection document chaining**: Retrieves from multiple relevant collections
- **vGPU profile validation**: Only suggests officially documented profiles  
- **Hardware-specific guidance**: GPU model-specific recommendations
- **Cost optimization insights**: Cost-efficiency focused suggestions
- **Hypervisor compatibility**: Platform-specific deployment guidance
"""
        
        main_readme.write_text(main_readme_content)
        logger.info(f"✅ Created sample vGPU documentation structure at {docs_base_path}")

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