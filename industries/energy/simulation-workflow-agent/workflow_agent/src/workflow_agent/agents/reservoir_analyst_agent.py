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
Reservoir analyst agent.
"""

from __future__ import annotations

from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent


class ReservoirAnalystAgent(BaseAgent):
    def execute(self, task: Dict[str, Any]) -> AgentResponse:
        prompt = self.format_prompt(task)
        system_prompt = (
            "You are a reservoir optimization analyst. Analyze the inputs and return "
            "a concise JSON/YAML summary of problem characteristics and optimization hints."
        )
        content = self._call_llm(prompt, system_prompt)
        data = self.parse_response(content)
        return AgentResponse(
            success=True,
            content=content,
            data=data,
            metadata={"agent": self.name, "endpoint": self._last_endpoint, "model": self._last_model},
        )

    @staticmethod
    def extract_characteristics(base_config: Dict[str, Any]) -> Dict[str, Any]:
        variables = base_config.get("variables", {})
        template_path = base_config.get("paths", {}).get("template")
        return {
            "n_variables": len(variables),
            "variable_names": list(variables.keys()),
            "template_path": template_path,
            "has_integer_vars": any(v.get("type") == "int" for v in variables.values()),
        }
