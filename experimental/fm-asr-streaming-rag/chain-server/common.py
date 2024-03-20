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

import numpy as np

from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import Literal
from langchain_community.utils.math import cosine_similarity
from langchain_community.embeddings import HuggingFaceEmbeddings

class TextEntry(BaseModel):
    """ API to store text in database
    """
    transcript: str = Field("Streaming text to store")
    timestamp: datetime = Field("Timestamp of text")

class SearchDocumentConfig(BaseModel):
    """ API to do similarity search on database
    """
    content: str = Field("Content to search database for")
    max_docs: int = Field("Maximum number of documents to return")
    threshold: float = Field("Minimum similarity threshold for docs")

class RecentDocumentConfig(BaseModel):
    """ API to return all documents since timestamp
    """
    timestamp: datetime = Field("Timestamp of documents to retrieve up to")
    max_docs: int = Field("Maximum number of documents to return")

class PastDocumentConfig(BaseModel):
    """ API to return all documents near timestamp, within window seconds
    """
    timestamp: datetime = Field("Timestamp of documents to retrieve near")
    max_docs: int = Field("Maximum number of documents to return")
    window: int = Field(
        description="Window (sec) around which documents from timestamp are returned",
        default=90
    )

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
    engine: str = Field("Name of engine ['nv-ai-foundation', 'triton-trt-llm']")
    # Chain parameters
    use_knowledge_base: bool = Field(
        description="Whether to use a knowledge base", default=True
    )
    allow_summary: bool = Field("Use recursive summarization to reduce long contexts")
    temperature: float = Field("Temperature of the LLM response")
    threshold: float = Field("Minimum similarity threshold for docs")
    max_docs: int = Field("Maximum number of documents to return")
    num_tokens: int = Field("The maximum number of tokens in the response")

"""
For cases where an LLM returns a time unit that doesn't match one of the discrete
options, find the closest with cosine similarity.

Example: 'min' -> 'minutes'
"""
EMBEDDINGS = HuggingFaceEmbeddings()
VALID_TIME_UNITS = ["seconds", "minutes", "hours", "days"]
TIME_VECTORS = EMBEDDINGS.embed_documents(VALID_TIME_UNITS)

def sanitize_time_unit(time_unit):
    if time_unit in VALID_TIME_UNITS:
        return time_unit

    unit_embedding = [EMBEDDINGS.embed_query(time_unit)]
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