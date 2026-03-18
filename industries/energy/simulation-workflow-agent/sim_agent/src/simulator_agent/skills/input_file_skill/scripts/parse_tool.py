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
Parse DATA File Tool

Tool for parsing and analyzing OPM DATA file structure.
Used in TOOL_DECISION_TREE.md Section 2.4 (Scenario test chain) as the first step.
"""

from pathlib import Path

from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

from ..utils import parse_data_sections


class ParseDataFileInput(BaseModel):
    file_path: str = Field(..., description="Path to the OPM DATA file")


@tool("parse_simulation_input_file", args_schema=ParseDataFileInput)
def parse_simulation_input_file(file_path: str) -> str:
    """
    Parse an OPM DATA file and return its structure.
    
    This tool is the first step in the scenario test chain (Section 2.4):
    parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal
    
    Returns a string listing all sections found in the DATA file.
    """
    try:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return f"Error: File not found: {file_path}"

        # Read file content
        with open(file_path_obj, 'r') as f:
            content = f.read()

        # Parse into sections
        sections = parse_data_sections(content)

        section_list = ", ".join(sections.keys()) if sections else "None"
        return f"Sections found: {section_list}"

    except Exception as e:
        return f"Error parsing DATA file: {str(e)}"

