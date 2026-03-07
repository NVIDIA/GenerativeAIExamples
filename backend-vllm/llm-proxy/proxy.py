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

"""
Simple NVIDIA Dynamo Proxy Server

A lightweight proxy server that forwards chat completion requests
to NVIDIA Dynamo / Ollama-compatible LLM server.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import logging
import yaml
from pathlib import Path

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

config = load_config()

app = FastAPI(title="NVIDIA Dynamo Proxy")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["proxy"]["cors"]["allow_origins"],
    allow_credentials=config["proxy"]["cors"]["allow_credentials"],
    allow_methods=config["proxy"]["cors"]["allow_methods"],
    allow_headers=config["proxy"]["cors"]["allow_headers"],
)

# Initialize HTTP client
http_client = httpx.AsyncClient()

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    stream: bool = False
    max_tokens: Optional[int] = None


# ------------------------------------------------------------------
# NEW: Models endpoint (required by frontend model discovery)
# ------------------------------------------------------------------
@app.get("/v1/models")
async def list_models(x_llm_ip: str = Header(None)):
    """
    Returns OpenAI-compatible model list.
    Fetches models from upstream Ollama/Dynamo server.
    """
    try:
        # Always use local Ollama upstream; do not trust X-LLM-IP for local routing
        upstream_url = f"http://127.0.0.1:{config['llm']['port']}/api/tags"
        response = await http_client.get(upstream_url, timeout=config["llm"]["timeout"])
        response.raise_for_status()

        data = response.json()

        models = []
        for m in data.get("models", []):
            models.append({
                "id": m.get("name"),
                "object": "model",
                "created": 0,
                "owned_by": "ollama"
            })

        return {
            "object": "list",
            "data": models
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Upstream error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Chat Completions endpoint
# ------------------------------------------------------------------
@app.post("/v1/chat/completions")
async def proxy_chat_completions(
    request: ChatCompletionRequest,
    x_llm_ip: str = Header(None)
):
    """Forward chat completion requests to upstream LLM server"""

    try:
        # Always use local Ollama upstream; do not trust X-LLM-IP for local routing
        upstream_url = f"http://127.0.0.1:{config['llm']['port']}/v1/chat/completions"

        response = await http_client.post(
            upstream_url,
            json=request.model_dump(),  # Pydantic v2 safe
            timeout=config["llm"]["timeout"]
        )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Upstream error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["proxy"]["host"],
        port=int(config["proxy"]["port"]),
    )