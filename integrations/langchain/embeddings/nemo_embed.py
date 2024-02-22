# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Nemo Embedding Microservice"""

import requests
import json
import logging
from typing import Any, List, Sequence, Optional

from langchain.pydantic_v1 import BaseModel
from langchain.schema.embeddings import Embeddings

logger = logging.getLogger(__name__)

class NemoEmbeddings(BaseModel, Embeddings):
    """A custom Langchain Embedding class that integrates with Nemo Embedding MS
    
    Arguments:
    server_url: (str) The URL of the Nemo Embedding MS to use.
    model_name: (str) The name of the Nemo Embedding MS model to use.
    """
    server_url: str = "http://localhost:9080/v1/embeddings"
    model_name: str = "NV-Embed-QA-003"

    def __init__(self, *args: Sequence, **kwargs: Any):
        super().__init__(*args, **kwargs)

    def _embed(
        self,
        query: Optional[str] = "",
        input_type: Optional[str] = "query",
        request_timeout: Optional[int] = 5,
        **kwargs,
    ) -> List[float]:
        """ Function to get the embeddings from Nemo MS using REST API"""

        headers = {"accept": "application/json", "Content-Type": "application/json"}
        data = {}
        if query:
            data["input"] = query

        if not data["input"]:
            logger.warning("Valid query/passage not found in request")
            return []

        if self.model_name:
            data["model"] = self.model_name

        if input_type:
            data["input_type"] = input_type

        data["encoding_format"] = "float"
        data["truncate"] = "END"

        response = None
        request_timeout = int(request_timeout)

        if self.server_url is None:
            logger.warning(
                "Nemo Embedding Microservice URL not provided"
            )
            return []

        try:
            response = requests.post(self.server_url, headers=headers, data=json.dumps(data), timeout=request_timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.info("Http request to Nemo Embedding Microservice timed out.")
        except requests.exceptions.RequestException as e:
            logger.info(f"An error occurred in Http request to Nemo Embedding Microservice endpoint {str(e)}")

        if response and response.json():
            response_data = response.json().get("data", {})
            if len(response_data):
                return response_data[0].get("embedding", [])
            else:
                return []

        else:
            logger.info(f"Invalid or empty response returned by the Nemo Embedding Microservice endpoint {response}")
        return []

    def embed_query(self, text: str) -> List[float]:
        """Input pathway for query embeddings."""
        return self._embed(query=text, input_type="query")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Input pathway for document embeddings."""
        return [self._embed(query=text, input_type="passage") for text in texts]