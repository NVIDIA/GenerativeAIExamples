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

import logging
import requests
import json
import os
import numpy as np

from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import Literal
from langchain_community.utils.math import cosine_similarity

USE_NEMO_RETRIEVER = os.environ.get('USE_NEMO_RETRIEVER', 'False').lower() in ('true', '1')
NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY', 'null')

def get_logger(name):
    LOG_LEVEL = logging.getLevelName(os.environ.get('CHAIN_LOG_LEVEL', 'WARN').upper())
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(logging.StreamHandler())
    return logger

class TextEntry(BaseModel):
    """ API to store text in database
    """
    transcript: str = Field("Streaming text to store")
    source_id: str = Field("Source of text")
    timestamp: datetime = Field("Timestamp of text")

class LLMConfig(BaseModel):
    """ Definition of the LLMConfig API data type
    """
    # Input text
    question: str = Field("The input query/prompt to the pipeline.")
    context: str = Field(
        description="Additional context for the question (optional)", default=None
    )
    # Model choice
    name: str = Field("Name of LLM instance to use")
    engine: str = Field("Name of engine ['nvai-api-endpoint', 'triton-trt-llm']")
    # Chain parameters
    use_knowledge_base: bool = Field(
        description="Whether to use a knowledge base", default=True
    )
    allow_summary: bool = Field("Use recursive summarization to reduce long contexts")
    temperature: float = Field("Temperature of the LLM response")
    max_docs: int = Field("Maximum number of documents to return")
    num_tokens: int = Field("The maximum number of tokens in the response")

def nemo_embedding(text):
    """
    Uses the NeMo Embedding MS to convert text to embeddings
    - ex: embeddings = nemo_embedding(['Chunk A', 'Chunk B'])
    """
    port = os.environ.get('NEMO_EMBEDDING_PORT', 1985)
    url = f"http://localhost:{port}/v1/embeddings"
    payload = json.dumps({
        "input": text,
        "model": "NV-Embed-QA",
        "input_type": "query"
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    embeddings = [chunk['embedding'] for chunk in response.json()['data']]
    return embeddings

def nvapi_embedding(text):
    session = requests.Session()
    url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/embeddings"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
    }
    payload = {
        "input": text,
        "input_type": "passage",
        "model": "NV-Embed-QA"
    }
    response = session.post(url, headers=headers, json=payload)
    embeddings = [chunk['embedding'] for chunk in response.json()['data']]
    return embeddings

VALID_TIME_UNITS = ["seconds", "minutes", "hours", "days"]
TIME_VECTORS = None # Lazy loading in 'sanitize_time_unit'
if USE_NEMO_RETRIEVER:
    embedding_service = nemo_embedding
else:
    embedding_service = nvapi_embedding

def sanitize_time_unit(time_unit):
    """
    For cases where an LLM returns a time unit that doesn't match one of the
    discrete options, find the closest with cosine similarity.

    Example: 'min' -> 'minutes'
    """
    if time_unit in VALID_TIME_UNITS:
        return time_unit

    if TIME_VECTORS is None:
        TIME_VECTORS = embedding_service(VALID_TIME_UNITS)

    unit_embedding = embedding_service([time_unit])
    similarity = cosine_similarity(unit_embedding, TIME_VECTORS)
    return VALID_TIME_UNITS[np.argmax(similarity)]

"""
Pydantic classes that are used to detect user intent and plan accordingly
"""
class TimeResponse(BaseModel):
    timeNum: float = Field("The number of time units the user asked about")
    timeUnit: str = Field("The unit of time the user asked about")

    def to_seconds(self):
        """ Return the total number of seconds this represents
        """
        self.timeUnit = sanitize_time_unit(self.timeUnit)
        return timedelta(**{self.timeUnit: self.timeNum}).total_seconds()

class UserIntent(BaseModel):
    intentType: Literal[
        "SpecificTopic",
        "RecentSummary",
        "TimeWindow",
        "Unknown"
    ] = Field("The intent of user's query")