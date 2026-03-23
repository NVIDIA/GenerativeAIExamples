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
Agent team registry.
"""

from __future__ import annotations

from typing import Dict, List

from .base_agent import BaseAgent


class AgentTeam:
    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    def add_agent(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        return self._agents[name]

    def enabled_agents(self) -> List[str]:
        return [name for name, agent in self._agents.items() if agent.enabled]
