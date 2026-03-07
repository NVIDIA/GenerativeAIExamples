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


import yaml
import os
from pathlib import Path
from typing import Dict, Any
import logging
from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Only log errors in production
logger = logging.getLogger(__name__)

app = FastAPI()

class ConfigLoader:
    def __init__(self, config_dir: str = None):
        """Initialize the config loader with the config directory path"""
        if config_dir is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, Dict[str, Any]] = {}

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a specific configuration file"""
        if config_name in self.configs:
            return self.configs[config_name]

        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            self.configs[config_name] = config
            return config

    def get_app_config(self) -> Dict[str, Any]:
        """Get the application configuration"""
        return self.load_config('app_config')

    def get_rag_config(self) -> Dict[str, Any]:
        """Get the RAG service configuration"""
        return self.load_config('rag_config')

    def get_faiss_index_status(self) -> Dict[str, Any]:
        """Get the FAISS index status"""
        # Simulated FAISS index status check
        try:
            # Replace with actual FAISS indexing logic
            faiss_index_status = {
                "indexed_files": 44,  # Example count of indexed files in FAISS
                "is_index_ready": True,  # Whether the FAISS index is ready
                "last_updated": "2026-02-28T12:00:00Z"  # Example timestamp
            }
            return faiss_index_status
        except Exception as e:
            logger.error(f"Error retrieving FAISS index status: {e}")
            return {"error": "Failed to retrieve FAISS index status"}

# Include /api/rag-status endpoint
@app.get("/api/rag-status")
async def get_rag_index_status():
    return {
        "document_count": 44,  # Example count of indexed documents
        "is_empty": False  # Index is not empty
    }

# Include /api/index/faiss-status endpoint
@app.get("/api/index/faiss-status")
async def get_faiss_index_status():
    # Simulated check for FAISS indexing status
    try:
        faiss_index_status = {
            "indexed_files": 44,  # Example count of indexed files in FAISS
            "is_index_ready": True,  # Whether the FAISS index is ready
            "last_updated": "2026-02-28T12:00:00Z"  # Example timestamp
        }
        return faiss_index_status
    except Exception as e:
        logger.error(f"Error retrieving FAISS index status: {e}")
        return {"error": "Failed to retrieve FAISS index status"}

# Create a singleton instance for loading configurations
config_loader = ConfigLoader()