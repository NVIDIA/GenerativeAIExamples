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
Patch DATA File Keyword Tool

Tool for patching specific keyword blocks in OPM DATA files.
Used in TOOL_DECISION_TREE.md Section 2.2 (HITL: apply fix) for auto-fixes.
"""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

from ..utils import find_keyword_block, replace_nth_number_in_block


class PatchDataFileKeywordInput(BaseModel):
    file_path: str = Field(..., description="Path to the OPM DATA file")
    keyword: str = Field(..., description="Keyword to patch (e.g. WELLDIMS, TABDIMS)")
    output_path: str = Field(
        ...,
        description="Path for the new file (original is unchanged; use e.g. stem_agent_fixed.DATA)",
    )
    item_index: Optional[int] = Field(
        default=None,
        description="1-based index of the numeric item to replace in the keyword's data (e.g. 1 = first number)",
    )
    new_value: Optional[str] = Field(
        default=None,
        description="New value for the item (used with item_index)",
    )
    new_block_content: Optional[str] = Field(
        default=None,
        description="Exact new block content (keyword line + data). If set, item_index/new_value are ignored.",
    )


@tool("patch_simulation_input_keyword", args_schema=PatchDataFileKeywordInput)
def patch_simulation_input_keyword(
    file_path: str,
    keyword: str,
    output_path: str,
    item_index: Optional[int] = None,
    new_value: Optional[str] = None,
    new_block_content: Optional[str] = None,
) -> str:
    """
    Change only a single keyword block in an OPM DATA file; all other lines are copied unchanged.
    Use this to avoid rewriting the whole file. Either set item_index and new_value to replace
    the N-th number in the keyword's data, or set new_block_content to replace the entire block.
    Writes to output_path (original file is never modified).
    
    This tool is used in TOOL_DECISION_TREE.md Section 2.2 (HITL: apply fix) for auto-fixes:
    patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal
    """
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return f"Error: File not found: {file_path}"

        content = file_path_obj.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines(keepends=True)  # keep newlines for exact mirror
        if not lines:
            return "Error: File is empty."

        block = find_keyword_block(content, keyword)
        if not block:
            return f"Error: Keyword '{keyword}' not found in file."

        start, end = block
        # Rebuild: before + modified_block + after (as strings with newlines)
        before = "".join(lines[:start])
        block_lines = [lines[i] for i in range(start, end + 1)]
        after = "".join(lines[end + 1 :])

        # Use same line ending as source file so we never introduce CRLF/LF mismatch
        line_ending = "\n"
        if block_lines:
            last = block_lines[-1]
            if last.endswith("\r\n"):
                line_ending = "\r\n"
            elif last.endswith("\n"):
                line_ending = "\n"

        if new_block_content is not None:
            new_block = new_block_content.rstrip().rstrip("\r")
            if not new_block.endswith(line_ending):
                new_block += line_ending
        elif item_index is not None and new_value is not None:
            block_lines_no_nl = [s.rstrip("\n\r") for s in block_lines]
            new_block_lines = replace_nth_number_in_block(
                block_lines_no_nl, item_index, new_value
            )
            new_block = line_ending.join(new_block_lines) + line_ending
        else:
            return "Error: Set either (item_index and new_value) or new_block_content."

        new_content = before + new_block + after
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(new_content, encoding="utf-8", newline="")

        return (
            f"Patched keyword '{keyword}' only; rest of file unchanged.\n"
            f"- Input: {file_path}\n"
            f"- Output: {output_path}\n"
        )
    except Exception as e:
        return f"Error patching DATA file: {str(e)}"

