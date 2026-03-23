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
OPM Simulation Skill for OPM Flow

This skill provides tools for running, monitoring, and controlling OPM Flow simulations.
Follows the Agent Skills specification: https://agentskills.io/specification

Structure:
- SKILL.md: Skill metadata and instructions
- test.py: Test suite
- scripts/: Tool implementations (simulation_tools.py, self_heal_chain.py)
- references/: Additional documentation
- assets/: Static resources

Based on TOOL_DECISION_TREE.md Sections 2.1, 2.3, 2.4, 3.3, and 3.5.

Tools:
- run_and_heal: Run OPM Flow + auto-fix on failure (primary run tool)
- run_simulation: Low-level run tool (used internally by run_and_heal)
- monitor_simulation: Monitor simulation progress and status
- stop_simulation: Stop running simulations by PID
"""

from .scripts.simulation_tools import (
    run_simulation,
    monitor_simulation,
    stop_simulation,
)
from .scripts.self_heal_chain import run_and_heal

__all__ = [
    "run_and_heal",
    "run_simulation",
    "monitor_simulation",
    "stop_simulation",
]
