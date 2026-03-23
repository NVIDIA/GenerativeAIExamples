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

"""Rerank passages by relevance to query. URL and model are configurable via config.yaml (rag.reranker_url, rag.reranker_model)."""

import os
from pathlib import Path

import requests

_DEFAULT_URL = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-3_2-nv-rerankqa-1b-v2/reranking"
_DEFAULT_MODEL = "nvidia/llama-3.2-nv-rerankqa-1b-v2"


def _get_reranker_config() -> tuple[str, str]:
    """Return (url, model) from config. Tries simulator_agent.config, else loads config file."""
    try:
        from simulator_agent.config import get_config

        return get_config().get_reranker_config()
    except ImportError:
        pass
    config_path = os.environ.get("CONFIG_PATH", "").strip()
    if not config_path:
        cfg_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
        config_path = str(cfg_dir / "config.yaml")
    if Path(config_path).exists():
        try:
            import yaml

            with open(config_path) as f:
                cfg = yaml.safe_load(f) or {}
            rag = cfg.get("rag", {})
            url = (rag.get("reranker_url") or "").strip() or _DEFAULT_URL
            model = (rag.get("reranker_model") or "").strip() or _DEFAULT_MODEL
            return (url, model)
        except Exception:
            pass
    return (_DEFAULT_URL, _DEFAULT_MODEL)


def call_reranker(query: str, passages: list[str]) -> dict:
    """Rerank passages by relevance to query. passages can be list of strings."""
    url, model = _get_reranker_config()
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is required for reranking")
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    payload = {
        "model": model,
        "query": {"text": query},
        "passages": [{"text": p} for p in passages],
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
