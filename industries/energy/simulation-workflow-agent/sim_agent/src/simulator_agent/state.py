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
Simulator agent state types and constants.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict, Union

from langchain_core.messages import BaseMessage


class SkillUsed(TypedDict):
    skill_name: str
    tool_name: str
    tool_input: dict


class GlobalState(TypedDict, total=False):
    user_input: str
    input: str
    chat_history: list[BaseMessage]
    routing_to: list[SkillUsed]
    pending_steps: list[dict[str, Any]]
    uploaded_files: list[str]
    output_dir: str
    base_simulation_file: str
    internal_trajectory: Annotated[list[Union[Any, str, SkillUsed]], operator.add]
    agent_final_output: Optional[str]
    skill_failure_reason: Optional[str]
    args_valid: bool
    pending_confirm_relaunch: bool
    fixed_data_file_path: Optional[str]
    human_approve: Optional[str]
    human_approve_input: Optional[str]


# Tool name constants
SIMULATION_INPUT_TOOLS = {
    "run_and_heal",
    "parse_simulation_input_file",
    "modify_simulation_input_file",
    "patch_simulation_input_keyword",
}
PLOT_COMPARE_TOOL = "plot_compare_summary_metric"
PLOT_SUMMARY_TOOL = "plot_summary_metric"
CHAT_HISTORY_MAX_TURNS = 3
