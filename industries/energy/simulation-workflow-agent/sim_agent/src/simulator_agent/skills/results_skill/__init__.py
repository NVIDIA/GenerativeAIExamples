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
OPM Results Skill for OPM Flow

This skill provides tools for reading and analyzing OPM Flow simulation binary output files.
Follows the Agent Skills specification: https://agentskills.io/specification

Structure:
- SKILL.md: Skill metadata and instructions
- test.py: Test suite
- scripts/: Tool implementations (opm_results_tools.py, flow_diagnostics_tools.py)
- references/: Additional documentation
- assets/: Static resources

Based on TOOL_DECISION_TREE.md Section 2.6 (LLM tool choice) and Section 3.3 (after run_and_heal).

Tools:
- read_simulation_summary: Read time-series data from simulation summary files
- read_grid_properties: Read static grid properties from initialization files
- run_flow_diagnostics: Run flow diagnostics (TOF, tracer, allocation, F-Phi, Lorenz)
"""

from .scripts.opm_results_tools import (
    read_simulation_summary,
    read_grid_properties,
)
from .scripts.flow_diagnostics_tools import run_flow_diagnostics

__all__ = [
    "read_simulation_summary",
    "read_grid_properties",
    "run_flow_diagnostics",
]
