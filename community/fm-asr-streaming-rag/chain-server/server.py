# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import requests
import pydantic

from accumulator import TextAccumulator
from retriever import NVRetriever
from chains import RagChain
from common import (
    LLM_URI,
    get_logger,
    TextEntry,
    LLMConfig
)

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

logger = get_logger(__name__)

app = FastAPI()

# Create retriever and accumulators
db_interface = NVRetriever()
text_accumulator = TextAccumulator(
    db_interface,
    chunk_size=int(os.environ.get('DB_CHUNK_SIZE', 256)),
    chunk_overlap=int(os.environ.get('DB_CHUNK_OVERLAP', 32))
)

@app.get("/availableNvidiaModels")
async def available_nvidia_models(request: Request) -> JSONResponse:
    local_models = []
    cloud_models = []
    try:
        all_models = ChatNVIDIA(base_url=f"http://{LLM_URI}/v1").available_models
        local_models = [m.id for m in all_models if m.model_type == 'chat']
    except (requests.exceptions.ConnectionError, pydantic.v1.error_wrappers.ValidationError):
        pass
    cloud_models = [m.id for m in ChatNVIDIA().available_models if m.model_type == 'chat']
    return JSONResponse({"local_models": local_models, "cloud_models": cloud_models})

@app.get("/serverStatus")
async def server_status():
    return {"is_ready": True}

# API for database storage and searching
@app.post("/storeStreamingText")
async def store_streaming_text(request: Request, data: TextEntry) -> JSONResponse:
    return JSONResponse(
        text_accumulator.update(data.source_id, data.transcript)
    )

# API for LLM interaction
@app.get("/generate")
async def generate_answer(request: Request, config: LLMConfig) -> StreamingResponse:
    chain = RagChain(config, text_accumulator, db_interface)
    return StreamingResponse(chain.answer())