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
Tool input builders for query decomposition.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, List, Optional

from .paths import (
    extract_data_file_from_sub_query,
    extract_data_files_from_sub_query,
    resolve_data_path,
)
from ..state import PLOT_COMPARE_TOOL, PLOT_SUMMARY_TOOL


def _build_run_and_heal_input(sub_query: str, preferred: list[str]) -> dict[str, Any]:
    data_file = extract_data_file_from_sub_query(sub_query)
    if not data_file:
        return {}
    return {"data_file": resolve_data_path(data_file, preferred_paths=preferred)}


def _build_parse_patch_input(sub_query: str, preferred: list[str]) -> dict[str, Any]:
    data_file = extract_data_file_from_sub_query(sub_query)
    if not data_file:
        return {}
    return {"file_path": resolve_data_path(data_file, preferred_paths=preferred)}


def _build_modify_input(sub_query: str, preferred: list[str]) -> dict[str, Any]:
    data_paths = extract_data_files_from_sub_query(sub_query)
    if not data_paths:
        return {}
    file_path = resolve_data_path(data_paths[0], preferred_paths=preferred)
    out: dict[str, Any] = {
        "file_path": file_path,
        "modifications": (sub_query or "").strip() or "Apply the changes described in the scenario.",
    }
    if len(data_paths) >= 2:
        out_name = Path(data_paths[1]).name
        if preferred and Path(file_path).parent.exists():
            out["output_path"] = str(Path(file_path).parent / out_name)
        else:
            out["output_path"] = resolve_data_path(data_paths[1], preferred_paths=preferred)
    else:
        # No output path in sub_query: use _AGENT_GENERATED suffix
        out_name = f"{Path(file_path).stem}_AGENT_GENERATED.DATA"
        out["output_path"] = str(Path(file_path).parent / out_name)
    return out


def _build_rag_input(sub_query: str, preferred: list[str]) -> dict[str, Any]:
    return {
        "query": (sub_query or "").strip() or "OPM documentation",
        "collection_name": "",
    }


def _build_plot_input(sub_query: str, preferred: list[str]) -> dict[str, Any]:
    data_file = extract_data_file_from_sub_query(sub_query)
    if not data_file:
        return {}
    resolved = resolve_data_path(data_file, preferred_paths=preferred)
    return {"output_dir": str(Path(resolved).parent)}


def _extract_time_step_ids_from_query(text: str) -> Optional[List[int]]:
    """Extract time step IDs from natural language (e.g. 'time steps 5 and 10', 'steps 1, 2, 3')."""
    if not (text or "").strip():
        return None
    # Match "time step(s) X, Y, Z" or "time steps X and Y" or "at steps X, Y"
    m = re.search(
        r"(?:time\s+steps?|steps?|report\s+steps?)\s+([\d\s,and]+)",
        text,
        re.IGNORECASE,
    )
    if m:
        num_str = m.group(1)
        ids = [int(x) for x in re.findall(r"\d+", num_str)]
        if ids:
            return ids
    return None


def _build_run_flow_diagnostics_input(sub_query: str, preferred: list[str]) -> dict[str, Any]:
    data_file = extract_data_file_from_sub_query(sub_query)
    if not data_file:
        return {}
    resolved = resolve_data_path(data_file, preferred_paths=preferred)
    out: dict[str, Any] = {"case_path": str(resolved)}
    time_step_ids = _extract_time_step_ids_from_query(sub_query or "")
    if time_step_ids:
        out["time_step_ids"] = time_step_ids
    return out


_TOOL_INPUT_BUILDERS: dict[str, Callable[[str, list[str]], dict[str, Any]]] = {
    "run_and_heal": _build_run_and_heal_input,
    "parse_simulation_input_file": _build_parse_patch_input,
    "patch_simulation_input_keyword": _build_parse_patch_input,
    "modify_simulation_input_file": _build_modify_input,
    "simulator_manual": _build_rag_input,
    "simulator_examples": _build_rag_input,
    PLOT_SUMMARY_TOOL: _build_plot_input,
    PLOT_COMPARE_TOOL: _build_plot_input,
    "run_flow_diagnostics": _build_run_flow_diagnostics_input,
}


def build_tool_input_for_step(
    tool_name: str,
    sub_query: str,
    *,
    uploaded_files: Optional[list[str]] = None,
    base_simulation_file: Optional[str] = None,
) -> dict[str, Any]:
    preferred = list(uploaded_files or [])
    if base_simulation_file and base_simulation_file not in preferred:
        preferred.append(base_simulation_file)
    builder = _TOOL_INPUT_BUILDERS.get(tool_name)
    if not builder:
        return {}
    tool_input = builder(sub_query, preferred)
    if tool_name in ("simulator_manual", "simulator_examples") and tool_input:
        tool_input["collection_name"] = tool_name
    return tool_input
