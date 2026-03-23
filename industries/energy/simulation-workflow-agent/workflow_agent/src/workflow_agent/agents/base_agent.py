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
Base agent building blocks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import yaml

from .llm import MultiLLMManager, call_chat_completion, LLMEndpoint
from ..utils import ensure_serializable, parse_jsonish, parse_yamlish


@dataclass
class AgentResponse:
    success: bool
    content: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BaseAgent:
    name: str = "Base"

    def __init__(self, config: Dict[str, Any], llm_config: Dict[str, Any]) -> None:
        self.config = config
        self.llm_config = llm_config
        self.name = self.__class__.__name__.replace("Agent", "")
        self.enabled = config.get("enabled", True)

        self._last_endpoint: Optional[str] = None
        self._last_model: Optional[str] = None

        self.use_multi_llm = "endpoints" in llm_config
        self.llm_manager = MultiLLMManager(llm_config) if self.use_multi_llm else None
        if not self.use_multi_llm:
            self.provider = llm_config.get("provider", "openai")
            self.model = llm_config.get("primary_model", llm_config.get("model", "gpt-4"))
            self.temperature = llm_config.get("temperature", 0.7)
            self.max_tokens = llm_config.get("max_tokens", 4096)
            self.api_url = llm_config.get("api_url", "")
            self.api_key = llm_config.get("api_key") or os.getenv(
                llm_config.get("api_key_env", f"{self.provider.upper()}_API_KEY")
            )

    def _infer_task_type(self) -> str:
        name = self.name.lower()
        if "analyst" in name:
            return "reservoir_analysis"
        if "strategy" in name:
            return "strategy_proposal"
        if "critic" in name:
            return "critique"
        if "result" in name:
            return "result_analysis"
        if "knowledge" in name:
            return "knowledge_retrieval"
        return "general"

    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.use_multi_llm and self.llm_manager:
            response = self.llm_manager.call(prompt, system_prompt, self._infer_task_type())
            if not response.success:
                raise RuntimeError(response.error or "LLM error")
            self._last_endpoint = response.endpoint
            self._last_model = response.model
            return response.content

        if not self.api_key:
            raise ValueError("Missing API key for single-LLM mode")
        endpoint = LLMEndpoint(
            name="single",
            provider=self.provider,
            model=self.model,
            api_url=self.api_url,
            api_key=self.api_key,
            api_key_env=None,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        self._last_endpoint = endpoint.name
        self._last_model = endpoint.model
        return call_chat_completion(endpoint, prompt, system_prompt)

    def format_prompt(self, task: Dict[str, Any]) -> str:
        return yaml.safe_dump(ensure_serializable(task), sort_keys=False)

    def parse_response(self, content: str) -> Dict[str, Any]:
        parsed = parse_yamlish(content)
        if parsed:
            return parsed
        parsed = parse_jsonish(content)
        return parsed if parsed else {"raw": content}
