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
Shared utility functions for DATA file skill tools.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def find_keyword_block(content: str, keyword: str) -> Optional[Tuple[int, int]]:
    """
    Find the (start_line, end_line) of the keyword block (0-based line indices).
    Block starts at a line matching the keyword and runs until a line containing '/'.
    If the first such line is not a standalone '/', and the next line is standalone '/', include it too.
    """
    lines = content.splitlines()
    keyword_upper = keyword.upper().strip()
    kw_pattern = re.compile(r"^\s*" + re.escape(keyword_upper) + r"\b", re.IGNORECASE)
    start = None
    for i, line in enumerate(lines):
        if kw_pattern.match(line.strip()):
            start = i
            break
    if start is None:
        return None
    end = start
    for i in range(start, len(lines)):
        if "/" in lines[i]:
            end = i
            # Include trailing standalone '/' line if present (e.g. WCONINJE ... / then /)
            if i + 1 < len(lines) and lines[i + 1].strip() == "/":
                end = i + 1
            break
        end = i
    return (start, end)


def replace_nth_number_in_block(block_lines: List[str], item_index_1based: int, new_value: str) -> List[str]:
    """Replace the N-th numeric value (1-based) in the first data line of the block. Other lines unchanged."""
    result = []
    replaced = False
    for line in block_lines:
        if replaced or not re.search(r"\d", line):
            result.append(line)
            continue
        # This line has digits: find and replace the item_index_1based-th number
        parts = re.split(r"(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)", line)
        # parts alternates: [non-num, num, non-num, num, ...]
        n = 0
        new_parts = []
        for i, p in enumerate(parts):
            if re.fullmatch(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", p):
                n += 1
                if n == item_index_1based:
                    new_parts.append(str(new_value))
                    replaced = True
                else:
                    new_parts.append(p)
            else:
                new_parts.append(p)
        result.append("".join(new_parts))
    return result


def parse_data_sections(content: str) -> Dict[str, str]:
    """
    Parse DATA file into sections.
    
    Returns dict with section names as keys and content as values.
    """
    sections = {}
    current_section = "HEADER"
    current_content = []
    
    for line in content.split('\n'):
        # Check if line starts a new section
        stripped = line.strip()
        if stripped and not stripped.startswith('--'):
            # Common OPM sections
            section_keywords = [
                'RUNSPEC', 'GRID', 'EDIT', 'PROPS', 'REGIONS', 
                'SOLUTION', 'SUMMARY', 'SCHEDULE'
            ]
            for keyword in section_keywords:
                if stripped.startswith(keyword):
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = keyword
                    current_content = [line]
                    break
            else:
                current_content.append(line)
        else:
            current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    return sections


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        parts = stripped.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    return stripped


def strip_think_blocks(text: str) -> str:
    """
    Remove <think>...</think> blocks from LLM output.
    Some models include chain-of-thought reasoning in these tags; we must not write them to DATA files.
    Also handles unclosed <think> (truncated output) by stripping from <think> to end.
    """
    # Match <think>...</think> (non-greedy, handles nested or multiple blocks)
    pattern = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
    cleaned = pattern.sub("", text)
    # Handle unclosed <think> (e.g. truncated response)
    unclosed = re.search(r"<think>", cleaned, re.IGNORECASE)
    if unclosed:
        cleaned = cleaned[: unclosed.start()].strip()
    return cleaned.strip()


def parse_old_new_values(text: str) -> Optional[Tuple[str, str]]:
    """Parse 'old_value new_value' from LLM response. Returns (old, new) or None."""
    cleaned = strip_code_fences(text).strip()
    # Allow numbers, quoted strings, or 1* etc.
    tokens = re.findall(r"(?:\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\'\w+\'|\d+\*|\S+)", cleaned)
    if len(tokens) >= 2:
        return (tokens[0], tokens[1])
    # Fallback: split on whitespace
    parts = cleaned.split()
    if len(parts) >= 2:
        return (parts[0], parts[1])
    return None

