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

import json
import re
import json
import numpy as np

from datetime import timedelta
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings, NVIDIARerank
from pydantic import BaseModel, Field
from langchain_community.utils.math import cosine_similarity
from typing import Literal

from common import (
    get_logger,
    LLMConfig,
    NVIDIA_API_KEY,
    LLM_URI,
    RERANKING_MODEL,
    RERANKING_URI,
    EMBEDDING_MODEL,
    EMBEDDING_URI,
    MAX_DOCS
)

logger = get_logger(__name__)

def get_llm(config: LLMConfig):
    """
    Returns LLM client matching given config. If not using local NIM, uses
    API endpointat https://build.nvidia.com
    """
    if config.engine == "local-nim":
        return ChatNVIDIA(
            base_url=f"http://{LLM_URI}/v1",
            model=config.name,
            temperature=config.temperature
        )
    elif config.engine == "nvai-api-endpoint":
        return ChatNVIDIA(
            model=config.name,
            api_key=NVIDIA_API_KEY,
            temperature=config.temperature
        )
    else:
        raise ValueError(f"Unknown engine {config.engine}")

def get_reranker(local: bool=True):
    """
    Returns LLM reranking client. If not using local NIM, uses API endpoint
    at https://build.nvidia.com
    """
    if local:
        try:
            return NVIDIARerank(
                base_url=f"http://{RERANKING_URI}/v1",
                model=RERANKING_MODEL,
                top_n=MAX_DOCS
            )
        except Exception as e:
            logger.warning(f"Caught exception '{e}' when loading local "
                           "NVIDIARerank, using build.nvidia.com version")

    return NVIDIARerank(
        model=RERANKING_MODEL,
        api_key=NVIDIA_API_KEY,
        top_n=MAX_DOCS
    )

def get_embedder(local: bool=True):
    """
    Returns LLM embedding client. If not using local NIM, uses API endpoint
    at https://build.nvidia.com
    """
    if local:
        try:
            return NVIDIAEmbeddings(
                base_url=f"http://{EMBEDDING_URI}/v1",
                model=EMBEDDING_MODEL,
                truncate="NONE"
            )
        except Exception as e:
            logger.warning(f"Caught exception '{e}' when loading local "
                           "NVIDIAEmbeddings, using build.nvidia.com version")

    return NVIDIAEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=NVIDIA_API_KEY,
        truncate="NONE"
    )

embed_client = get_embedder()
VALID_TIME_UNITS = ["seconds", "minutes", "hours", "days"]
TIME_VECTORS = embed_client.embed_documents(VALID_TIME_UNITS)

def sanitize_time_unit(time_unit):
    """
    For cases where an LLM returns a time unit that doesn't match one of the
    discrete options, find the closest with cosine similarity.

    Example: 'min' -> 'minutes'
    """
    if time_unit in VALID_TIME_UNITS:
        return time_unit

    unit_embedding = embed_client.embed_documents([time_unit])
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

def classify(question, chain, pydantic_obj: BaseModel):
    """ Parse a question into structured pydantic_obj
    """
    output = chain.invoke({"input": question})
    try:
        # Try to parse as Pydantic object
        result = pydantic_obj.model_validate_json(output)
    except ValueError:
        try:
            # If failed, look for valid JSON inside output
            logger.warning(fr"Failed to parse initial output '{output}'")
            sanitized_output = sanitize_json(output)
            logger.warning(fr"Sanitized output '{sanitized_output}'")
            result = pydantic_obj.model_validate_json(sanitized_output)
        except ValueError:
            # Neither approach worked, return None
            logger.error(f"Error parsing output into {pydantic_obj}: "
                         rf"'{output}'")
            result = None
    logger.info(f"Result: {result}")
    return result

"""
These are some functions that try to fix some common mistakes LLMs might make
when outputting structured JSON. Rather than immediately giving up, we replace
some incorrect special characters and look for possible JSON matches that are
embeddeded into a wider string.

Example:
 - LLM output:  Sure! Here's the JSON you asked for: {'key': value}
 - Sanitized:   {"key": value}
"""
def sanitize_json(text: str, pydantic_obj: BaseModel=None):
    return find_first_valid_json(
        replace_special(text), pydantic_obj=pydantic_obj
    )

def replace_special(text_in: str):
    text_out = text_in.replace("\'", "\"")
    text_out = text_out.replace("\_", "_")
    text_out = text_out.replace("\\", "")
    return text_out

def find_first_valid_json(text: str, pydantic_obj: BaseModel=None):
    # Regex pattern to find substrings that look like JSON objects or arrays
    pattern = r'(\{.*?\}|\[.*?\])'

    # Find all substrings that match the pattern
    potential_jsons = re.findall(pattern, text, re.DOTALL)
    for pj in potential_jsons:
        try:
            # Attempt to parse the substring as JSON
            json.loads(pj)
            if pydantic_obj:
                pydantic_obj.model_validate_json(pj)
            return pj
        except (json.JSONDecodeError, ValueError):
            continue  # if parsing fails, move on to the next substring
    return None  # if no valid JSON is found, return None