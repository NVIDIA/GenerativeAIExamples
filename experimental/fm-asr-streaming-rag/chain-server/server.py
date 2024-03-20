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
import logging

from database import VectorStoreInterface
from chains import RagChain
from common import (
    TextEntry,
    SearchDocumentConfig,
    RecentDocumentConfig,
    PastDocumentConfig,
    LLMConfig
)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

LOG_LEVEL = logging.getLevelName(os.environ.get('CHAIN_LOG_LEVEL', 'WARN').upper())
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

app = FastAPI()

# Create vector database
db = VectorStoreInterface(
    chunk_size=int(os.environ.get('DB_CHUNK_SIZE', 256)),
    chunk_overlap=int(os.environ.get('DB_CHUNK_OVERLAP', 32))
)


# API for database storage and searching
@app.post("/storeStreamingText")
async def store_streaming_text(request: Request, data: TextEntry) -> JSONResponse:
    return JSONResponse(
        db.store_streaming_text(data.transcript, tstamp=data.timestamp)
    )

@app.get("/searchDocuments")
async def search_documents(request: Request, data: SearchDocumentConfig) -> JSONResponse:
    docs = db.search(
        data.content, max_entries=data.max_docs, score_threshold=data.threshold
    )
    return JSONResponse([doc.dict() for doc in docs])

@app.get("/recentDocuments")
async def recent_documents(request: Request, data: RecentDocumentConfig) -> JSONResponse:
    docs = db.recent(data.timestamp, max_entries=data.max_docs)
    return JSONResponse([doc.dict() for doc in docs])

@app.get("/pastDocuments")
async def past_documents(request: Request, data: PastDocumentConfig) -> JSONResponse:
    docs = db.past(data.timestamp, window=data.window, max_entries=data.max_docs)
    return JSONResponse([doc.dict() for doc in docs])

# API for LLM interaction
@app.get("/generate")
async def generate_answer(request: Request, config: LLMConfig) -> StreamingResponse:
    chain = RagChain(config, db)
    return StreamingResponse(chain.answer())