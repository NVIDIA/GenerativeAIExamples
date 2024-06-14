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
import json
import re

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from pydantic import BaseModel

from common import get_logger, LLMConfig

logger = get_logger(__name__)

def get_llm(config: LLMConfig):
    client = ChatNVIDIA(
        model=config.name,
        temperature=config.temperature,
        max_tokens=config.num_tokens
    )
    if config.engine == "triton-trt-llm":
        nim_llm_port = os.environ.get('NIM_LLM_PORT', 9999)
        return client.mode("nim", base_url=f"http://0.0.0.0:{nim_llm_port}/v1")
    elif config.engine == "nvai-api-endpoint":
        return client
    else:
        raise ValueError(f"Unknown engine {config.engine}")

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
            logger.warning(f"Failed to parse initial output {output}")
            sanitized_output = sanitize_json(output)
            result = pydantic_obj.model_validate_json(sanitized_output)
        except ValueError:
            # Neither approach worked, return None
            logger.error(f"Error parsing output into {pydantic_obj}: '{output}'")
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