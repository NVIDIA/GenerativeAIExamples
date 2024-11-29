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
import os

from datetime import datetime
from pydantic import BaseModel, Field

NVIDIA_API_KEY  = os.environ.get('NVIDIA_API_KEY', 'null')
LLM_URI         = os.environ.get('LLM_URI', None)
RERANKING_MODEL = os.environ.get('RERANK_MODEL', None)
RERANKING_URI   = os.environ.get('RERANK_URI', None)
EMBEDDING_MODEL = os.environ.get('EMBED_MODEL', None)
EMBEDDING_URI   = os.environ.get('EMBED_URI', None)
MAX_DOCS        = int(os.environ.get('MAX_DOCS_RETR', 8))

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
    engine: str = Field("Name of engine ['nvai-api-endpoint', 'local-nim']")
    # Chain parameters
    use_knowledge_base: bool = Field(
        description="Whether to use a knowledge base", default=True
    )
    allow_summary: bool = Field("Use recursive summarization to reduce long contexts")
    temperature: float = Field("Temperature of the LLM response")
    max_docs: int = Field("Maximum number of documents to return")
    num_tokens: int = Field("The maximum number of tokens in the response")
