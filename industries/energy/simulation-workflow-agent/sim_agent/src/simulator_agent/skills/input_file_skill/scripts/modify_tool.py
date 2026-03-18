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
Modify DATA File Tool

Tool for modifying OPM DATA files with natural language instructions.
Used in TOOL_DECISION_TREE.md Section 2.4 (Scenario test chain) after parse_simulation_input_file.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from simulator_agent.config import get_config
from llm_provider import ChatOpenAI
from pydantic.v1 import BaseModel, Field

from ..utils import find_keyword_block, parse_old_new_values, strip_code_fences, strip_think_blocks


class ModifyDataFileInput(BaseModel):
    file_path: str = Field(..., description="Path to the OPM DATA file to modify")
    modifications: str = Field(..., description="Natural language description of changes")
    output_path: Optional[str] = Field(
        default=None,
        description="Where to save modified file (default: new file named {stem}_AGENT_GENERATED.DATA in same directory)",
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="Optional model override for LLM-based modifications",
    )
    manual_context: Optional[str] = Field(
        default=None,
        description="Optional OPM manual excerpt for the relevant keyword (use when editing that keyword)",
    )
    example_context: Optional[str] = Field(
        default=None,
        description="Optional OPM example DATA snippets for the relevant keyword",
    )
    target_keyword: Optional[str] = Field(
        default=None,
        description="If set, only this keyword block is edited; the rest of the file is copied unchanged (mirror).",
    )


def _apply_llm_modifications(
    content: str,
    modifications: str,
    model_name: Optional[str] = None,
    manual_context: Optional[str] = None,
    example_context: Optional[str] = None,
) -> str:
    """Apply LLM-based modifications to the entire file content."""
    model = model_name or get_config().get_llm_model(use_for="tool")
    llm = ChatOpenAI(model=model, max_tokens=4096)
    prompt_parts = [
        "You are editing an OPM Flow DATA file.\n"
        "CRITICAL: Make ONLY the minimal change requested. Do NOT reformat, reflow, or alter any other part of the file.\n"
        "Copy every other line exactly as it appears (same spacing, comments, line breaks). Only edit the specific keyword or record that the request refers to.\n"
        "Return the FULL file content with just that one change. Do not add markdown or code fences.\n\n",
        "Modification request:\n",
        f"{modifications}\n\n",
    ]
    if manual_context and manual_context.strip():
        prompt_parts.append(
            "Reference (OPM manual excerpt for this keyword; use for correct field order and meaning):\n"
            f"{manual_context.strip()}\n\n"
        )
    if example_context and example_context.strip():
        prompt_parts.append(
            "Example snippets (OPM DATA examples for this keyword):\n"
            f"{example_context.strip()}\n\n"
        )
    prompt_parts.append("Current DATA file content:\n")
    prompt_parts.append(f"{content}\n")
    prompt = "".join(prompt_parts)
    response = llm.invoke(prompt)
    # Strip <think>...</think> blocks (LLM reasoning) and markdown code fences before writing
    updated = strip_code_fences(strip_think_blocks(response.content))
    return updated


def _apply_llm_modifications_to_block(
    content: str,
    modifications: str,
    keyword: str,
    model_name: Optional[str] = None,
    manual_context: Optional[str] = None,
    example_context: Optional[str] = None,
) -> Optional[str]:
    """
    Find the first block for the given keyword, ask LLM for ONLY the old and new value
    to substitute, then replace that value in the block. Formatting, slashes, and line
    structure are preserved (value-only replacement).
    Returns None if the keyword block is not found or LLM doesn't return a valid pair.
    """
    block_range = find_keyword_block(content, keyword)
    if not block_range:
        return None
    start, end = block_range
    lines_with_endings = content.splitlines(keepends=True)
    if not lines_with_endings:
        return None
    line_ending = "\r\n" if "\r\n" in content else "\n"
    block_lines = content.splitlines()[start : end + 1]
    block_content = "\n".join(block_lines)

    model = model_name or get_config().get_llm_model(use_for="tool")
    llm = ChatOpenAI(model=model, max_tokens=128)
    prompt_parts = [
        "You are editing ONE keyword block of an OPM Flow DATA file. "
        "Return ONLY two values: the OLD value to replace and the NEW value, separated by a single space. "
        "Do not change anything else (no slashes, no formatting). Example: 50 55\n\n",
        "Modification request:\n",
        f"{modifications}\n\n",
        "Current block:\n",
        f"{block_content}\n\n",
        "Reply with only: OLD_VALUE NEW_VALUE",
    ]
    prompt = "".join(prompt_parts)
    response = llm.invoke(prompt)
    pair = parse_old_new_values(strip_think_blocks(response.content))
    if not pair:
        return None
    old_value, new_value = pair
    # Replace first occurrence of old_value (as whole token) with new_value in the block only
    pattern = r"\b" + re.escape(old_value) + r"\b"
    if not re.search(pattern, block_content):
        return None
    modified_block_content = re.sub(pattern, new_value, block_content, count=1)
    modified_block_lines = modified_block_content.splitlines()
    new_block_lines = [ln.rstrip("\r\n") + line_ending for ln in modified_block_lines]
    result_lines = (
        lines_with_endings[:start]
        + new_block_lines
        + lines_with_endings[end + 1 :]
    )
    return "".join(result_lines)


@tool("modify_simulation_input_file", args_schema=ModifyDataFileInput)
def modify_simulation_input_file(
    file_path: str,
    modifications: str,
    output_path: Optional[str] = None,
    llm_model: Optional[str] = None,
    manual_context: Optional[str] = None,
    example_context: Optional[str] = None,
    target_keyword: Optional[str] = None,
) -> str:
    """
    Modify an OPM DATA file based on natural language instructions.
    Optionally pass manual_context and/or example_context from simulator_manual/simulator_examples for the relevant keyword.
    If target_keyword is set, only that keyword block is edited; the rest of the file is copied unchanged (mirror).
    
    This tool is used in TOOL_DECISION_TREE.md Section 2.4 (Scenario test chain):
    parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal
    """
    try:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return f"Error: File not found: {file_path}"

        # Read original content
        with open(file_path_obj, 'r') as f:
            original_content = f.read()

        if not os.getenv("NVIDIA_API_KEY"):
            return (
                "Error: NVIDIA_API_KEY is not set. LLM-based modification requires "
                "an API key in the environment."
            )

        if output_path:
            output_path_obj = Path(output_path)
        else:
            out_name = f"{file_path_obj.stem}_AGENT_GENERATED{file_path_obj.suffix}"
            output_path_obj = file_path_obj.parent / out_name
        content_to_edit = original_content
        # When target_keyword is set and writing to a different file: copy first, then edit only the block (mirror + surgical edit).
        if target_keyword and target_keyword.strip() and output_path_obj != file_path_obj:
            try:
                shutil.copy2(file_path_obj, output_path_obj)
            except Exception as e:
                return f"Error copying file to output: {e}"
            with open(output_path_obj, "r") as f:
                content_to_edit = f.read()

        if target_keyword and target_keyword.strip():
            updated_content = _apply_llm_modifications_to_block(
                content_to_edit,
                modifications,
                keyword=target_keyword.strip().upper(),
                model_name=llm_model,
                manual_context=manual_context,
                example_context=example_context,
            )
            if updated_content is None:
                updated_content = _apply_llm_modifications(
                    content_to_edit,
                    modifications,
                    model_name=llm_model,
                    manual_context=manual_context,
                    example_context=example_context,
                )
        else:
            updated_content = _apply_llm_modifications(
                content_to_edit,
                modifications,
                model_name=llm_model,
                manual_context=manual_context,
                example_context=example_context,
            )
        if not updated_content or len(updated_content) < max(100, len(content_to_edit) * 0.5):
            return "Error: LLM did not return a valid updated DATA file."

        with open(output_path_obj, "w") as f:
            f.write(updated_content)

        changed = "Yes" if updated_content != original_content else "No"
        return (
            "LLM modification complete.\n"
            f"- File: {file_path}\n"
            f"- Output: {output_path_obj}\n"
            f"- Changes applied: {changed}"
        )

    except Exception as e:
        return f"Error modifying DATA file: {str(e)}"

