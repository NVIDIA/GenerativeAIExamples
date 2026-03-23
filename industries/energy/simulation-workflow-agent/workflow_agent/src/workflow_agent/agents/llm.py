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

from __future__ import annotations

import itertools
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@dataclass
class LLMEndpoint:
    name: str
    provider: str
    model: str
    api_url: str
    api_key: Optional[str]
    api_key_env: Optional[str]
    temperature: float
    max_tokens: int
    enabled: bool = True
    priority: int = 0
    task_preferences: Optional[List[str]] = None


@dataclass
class LLMResponse:
    success: bool
    content: str
    endpoint: str
    model: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class MultiLLMManager:
    """Minimal multi-endpoint router with basic strategies."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._routing = config.get("routing_strategy", "task_based")
        self._task_routing = config.get("task_routing", {})
        self._fallback = config.get("fallback", {})
        self._endpoints = self._load_endpoints(config.get("endpoints", {}))
        if not self._endpoints:
            raise ValueError("No enabled LLM endpoints configured")
        self._round_robin = itertools.cycle(self._endpoints)

    def _load_endpoints(self, endpoints: Dict[str, Any]) -> List[LLMEndpoint]:
        loaded: List[LLMEndpoint] = []
        default_temp = self._config.get("default_temperature", 0.7)
        default_max_tokens = self._config.get("default_max_tokens", 4096)

        for name, endpoint in endpoints.items():
            if not endpoint.get("enabled", True):
                continue
            api_key = endpoint.get("api_key") or os.getenv(endpoint.get("api_key_env", ""))
            loaded.append(
                LLMEndpoint(
                    name=name,
                    provider=endpoint.get("provider", "openai"),
                    model=endpoint["model"],
                    api_url=endpoint.get("api_url", ""),
                    api_key=api_key,
                    api_key_env=endpoint.get("api_key_env"),
                    temperature=float(endpoint.get("temperature", default_temp)),
                    max_tokens=int(endpoint.get("max_tokens", default_max_tokens)),
                    enabled=True,
                    priority=int(endpoint.get("priority", 0)),
                    task_preferences=endpoint.get("task_preferences"),
                )
            )

        loaded.sort(key=lambda e: e.priority, reverse=True)
        return loaded

    def _select_candidates(self, task_type: Optional[str]) -> Iterable[LLMEndpoint]:
        if self._routing == "round_robin":
            return [next(self._round_robin)]

        if self._routing == "task_based" and task_type:
            task_map = self._task_routing.get(task_type, [])
            if task_map:
                preferred = [e for e in self._endpoints if e.name in task_map]
                if preferred:
                    return preferred

        return self._endpoints

    def call(self, prompt: str, system_prompt: Optional[str], task_type: Optional[str]) -> LLMResponse:
        candidates = list(self._select_candidates(task_type))
        retries = int(self._fallback.get("max_retries", 1))

        last_error = None
        for _ in range(retries + 1):
            for endpoint in candidates:
                start = time.time()
                try:
                    content = call_chat_completion(endpoint, prompt, system_prompt)
                    return LLMResponse(
                        success=True,
                        content=content,
                        endpoint=endpoint.name,
                        model=endpoint.model,
                        latency_ms=(time.time() - start) * 1000,
                    )
                except Exception as exc:  # pragma: no cover - network failure path
                    last_error = str(exc)
                    continue

        return LLMResponse(
            success=False,
            content="",
            endpoint=candidates[0].name if candidates else "unknown",
            model=candidates[0].model if candidates else "unknown",
            error=last_error or "Unknown LLM error",
        )


def call_chat_completion(
    endpoint: LLMEndpoint,
    prompt: str,
    system_prompt: Optional[str],
) -> str:
    if not endpoint.api_key:
        raise ValueError(f"Missing API key for endpoint {endpoint.name}")

    from llm_provider import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOpenAI(
        model=endpoint.model,
        base_url=endpoint.api_url,
        api_key=endpoint.api_key,
        temperature=endpoint.temperature,
        max_tokens=endpoint.max_tokens,
    )
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))
    return llm.invoke(messages).content
