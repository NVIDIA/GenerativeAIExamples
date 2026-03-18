# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""
NVIDIA NeMo Retriever embedding client using the NVIDIA API.
Uses OPENAI-compatible client with base_url for integrate.api.nvidia.com.
Requires NVIDIA_API_KEY in environment.

Rate limiting: on 429 Too Many Requests we retry with backoff.
  EMBED_RATE_LIMIT_SLEEP  Seconds to sleep on 429/500 before retry (default: 10)
  EMBED_MAX_RETRIES       Max retries on rate limit (default: 8)
"""
import os
import time
import numpy as np
from openai import OpenAI

# Model output dimension (from NVIDIA docs)
EMBEDDING_DIM = 2048
MODEL_NAME = "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1"

EMBED_RATE_LIMIT_SLEEP = int(os.environ.get("EMBED_RATE_LIMIT_SLEEP", "10"))
EMBED_MAX_RETRIES = int(os.environ.get("EMBED_MAX_RETRIES", "8"))


def _is_retryable_embed_error(e: Exception) -> bool:
    """True if we should sleep and retry (429 rate limit, 500 server error)."""
    msg = str(e).lower()
    if "429" in msg or "too many requests" in msg:
        return True
    if "500" in msg or "internal server error" in msg:
        return True
    code = getattr(e, "status_code", None)
    if code in (429, 500):
        return True
    return False


def get_client() -> OpenAI:
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is required")
    return OpenAI(
        api_key=api_key,
        base_url="https://integrate.api.nvidia.com/v1",
    )


def embed_texts(
    client: OpenAI,
    texts: list[str],
    input_type: str = "passage",
    truncate: str = "NONE",
    rate_limit_sleep: int = EMBED_RATE_LIMIT_SLEEP,
    max_retries: int = EMBED_MAX_RETRIES,
) -> list[list[float]]:
    """
    Get embeddings for a list of texts via NVIDIA API.
    On 429 Too Many Requests or 500: sleeps rate_limit_sleep seconds and retries up to max_retries times.

    Args:
        client: OpenAI client configured for NVIDIA API.
        texts: List of strings to embed.
        input_type: "passage" for documents to index, "query" for search queries.
        truncate: "NONE" or "END" (model max context is 8192 tokens).
        rate_limit_sleep: Seconds to sleep on 429/500 before retry.
        max_retries: Maximum number of retries on rate limit / server error.

    Returns:
        List of embedding vectors (each is list of floats, length EMBEDDING_DIM).
    """
    if not texts:
        return []
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=texts,
                model=MODEL_NAME,
                encoding_format="float",
                extra_body={
                    "modality": ["text"] * len(texts),
                    "input_type": input_type,
                    "truncate": truncate,
                },
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            last_error = e
            if _is_retryable_embed_error(e) and attempt < max_retries - 1:
                time.sleep(rate_limit_sleep)
            else:
                raise last_error
    raise last_error


class NvidiaEmbeddingModel:
    """
    Embedding model that matches the interface expected by the Milvus query notebook:
    embedding.get_embeddings(text) -> numpy array of shape (EMBEDDING_DIM,).
    Use for both indexing (passage) and querying (query).
    """

    def __init__(
        self,
        api_key: str | None = None,
        input_type_for_docs: str = "passage",
        truncate: str = "NONE",
    ):
        self._api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        if not self._api_key:
            raise ValueError("NVIDIA_API_KEY must be set in environment or passed")
        self._client = OpenAI(
            api_key=self._api_key,
            base_url="https://integrate.api.nvidia.com/v1",
        )
        self.input_type_for_docs = input_type_for_docs
        self.truncate = truncate

    def get_embeddings(self, text: str, input_type: str | None = None) -> np.ndarray:
        """
        Get embedding for a single string. Used for both documents and queries.
        For documents use input_type='passage', for search query use input_type='query'.

        Returns:
            np.ndarray of shape (EMBEDDING_DIM,) dtype float32, L2-normalized for IP similarity.
        """
        it = input_type if input_type is not None else self.input_type_for_docs
        vectors = embed_texts(
            self._client,
            [text],
            input_type=it,
            truncate=self.truncate,
        )
        vec = np.array(vectors[0], dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def get_embeddings_batch(
        self,
        texts: list[str],
        input_type: str | None = None,
        batch_size: int = 32,
    ) -> list[np.ndarray]:
        """
        Get embeddings for multiple texts in batches. Normalizes each vector for IP similarity.
        """
        it = input_type if input_type is not None else self.input_type_for_docs
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            vectors = embed_texts(
                self._client,
                batch,
                input_type=it,
                truncate=self.truncate,
            )
            for v in vectors:
                vec = np.array(v, dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                all_embeddings.append(vec)
        return all_embeddings


# For query-time use input_type="query"; for indexing use "passage".
# So we expose a class that defaults to "passage" for get_embeddings (docs) and the query
# notebook can use get_embeddings(query, input_type="query") or we provide a query_embed method.
def get_embedding_for_query(model: NvidiaEmbeddingModel, query: str) -> np.ndarray:
    """One-line helper for query embedding (input_type='query')."""
    return model.get_embeddings(query, input_type="query")
