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
DATA File Skill for OPM Flow

This skill provides tools for parsing, modifying, and patching simulator input files (OPM Flow uses .DATA format).
Follows the Agent Skills specification: https://agentskills.io/specification

Structure:
- SKILL.md: Skill metadata and instructions
- test.py: Test suite
- scripts/: Tool implementations (parse_tool.py, modify_tool.py, patch_tool.py)
- references/: Additional documentation
- assets/: Static resources

Based on TOOL_DECISION_TREE.md Section 2.4 (Scenario test chain) and related sections.

Tools:
- parse_simulation_input_file: Parse and analyze simulator input file structure
- modify_simulation_input_file: Modify simulator input files with natural language instructions
- patch_simulation_input_keyword: Patch specific keyword blocks in simulator input files
"""

from .scripts.parse_tool import parse_simulation_input_file
from .scripts.modify_tool import modify_simulation_input_file
from .scripts.patch_tool import patch_simulation_input_keyword

__all__ = [
    "parse_simulation_input_file",
    "modify_simulation_input_file",
    "patch_simulation_input_keyword",
]
