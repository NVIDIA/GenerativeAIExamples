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
Tool argument validators.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from ..state import GlobalState, SkillUsed, PLOT_COMPARE_TOOL, PLOT_SUMMARY_TOOL, SIMULATION_INPUT_TOOLS
from .paths import output_dir_from_context
from .plot import infer_plot_metric_with_llm
from ..skills.rag_skill.scripts.extract_keyword import AmbiguousQueryError


def valid_data_file_path(path_or_name: str, uploaded_files: list[str]) -> tuple[bool, Optional[str]]:
    if not (path_or_name or "").strip():
        return False, "No file path provided."
    s = path_or_name.strip()
    if not s.upper().endswith(".DATA"):
        return False, (
            "run_and_heal requires a simulator primary input file with extension .DATA. "
            "You provided a file that does not end with .DATA (e.g. .pdf is not supported). "
            "Please upload a valid simulator input file (.DATA)."
        )
    p = Path(s)
    if p.exists():
        return True, None
    for u in (uploaded_files or []):
        if u and Path(u).name == Path(s).name:
            return True, None
        if u and u.strip().upper().endswith(".DATA") and (s in u or Path(u).name == s):
            return True, None
    return False, (f"Simulator input file not found: {s}. Please upload the file or provide a valid path.")


def _validate_run_and_heal(state: GlobalState, tool_input: dict) -> tuple[bool, Optional[str]]:
    uploaded = state.get("uploaded_files") or []
    data_file = (tool_input.get("data_file") or "").strip()
    if not data_file and uploaded:
        for u in uploaded:
            if (u or "").strip().upper().endswith(".DATA"):
                tool_input["data_file"] = u.strip()
                data_file = u.strip()
                break
    if not data_file:
        return False, (
            "To run the simulation, please upload a simulator primary input file (extension .DATA). "
            "No simulator input file was provided or identified in your request."
        )
    return valid_data_file_path(data_file, uploaded)


def _validate_rag(state: GlobalState, tool_input: dict) -> tuple[bool, Optional[str]]:
    user_input = (state.get("user_input") or state.get("input") or "").strip()
    tool_input["query"] = (tool_input.get("query") or user_input or "OPM documentation").strip()
    return True, None


def _validate_plot_summary(state: GlobalState, tool_input: dict) -> tuple[bool, Optional[str]]:
    data_file = (tool_input.get("data_file") or tool_input.get("file_path") or "").strip()
    if not data_file and (state.get("base_simulation_file") or "").strip():
        data_file = (state.get("base_simulation_file") or "").strip()
        tool_input["data_file"] = data_file
    out_dir = output_dir_from_context(state, tool_input, data_file=data_file)
    tool_input["output_dir"] = out_dir.strip("'\"") if out_dir else "."
    if not (tool_input.get("metric_request") or "").strip():
        user_input = (state.get("user_input") or state.get("input") or "").strip()
        try:
            inferred = infer_plot_metric_with_llm(user_input)
        except AmbiguousQueryError as e:
            return False, str(e)
        if inferred:
            tool_input["metric_request"] = inferred
        else:
            return False, (
                "Could not determine the requested metric from your query. "
                "Please specify the metric explicitly (e.g. FOPT, FOPR) or describe it clearly. "
            )
    return True, None


def _validate_plot_compare(state: GlobalState, tool_input: dict) -> tuple[bool, Optional[str]]:
    output_dir = (tool_input.get("output_dir") or "").strip()
    case_stems = (tool_input.get("case_stems") or "").strip()
    case_paths = (tool_input.get("case_paths") or "").strip()
    base_simulation_file = (state.get("base_simulation_file") or "").strip()
    uploaded = state.get("uploaded_files") or []

    # Derive output_dir from context (state, base file, or uploaded .DATA/.SMSPEC)
    out_dir = output_dir or output_dir_from_context(state, tool_input, data_file=base_simulation_file)
    if out_dir:
        out_dir = out_dir.strip("'\"")
    has_output_location = bool(out_dir and out_dir != ".")

    if not has_output_location:
        return False, (
            "To compare summary metrics, provide an output directory (output_dir) where .SMSPEC files are located, "
            "or upload .SMSPEC files / .DATA files that have corresponding .SMSPEC in the same directory. "
            "You can also run simulations first to generate results."
        )
        if not case_stems and not case_paths:
            agent_generated = [
                u for u in uploaded
                if (u or "").upper().endswith(".DATA") and "_AGENT_GENERATED" in (u or "")
            ]
            smspec_uploaded = [u for u in uploaded if (u or "").strip().upper().endswith(".SMSPEC")]
            data_uploaded = [u for u in uploaded if (u or "").strip().upper().endswith(".DATA")]
            if not agent_generated and not smspec_uploaded and not data_uploaded:
                return False, (
                    "To compare cases, you need either: (1) case_stems or case_paths, or "
                    "(2) uploaded .SMSPEC files, or (3) uploaded .DATA files (with .SMSPEC in same dir after run), "
                    "or (4) a base simulation and an uploaded scenario file (*_AGENT_GENERATED.DATA)."
                )
    return True, None


def _validate_plot_compare_full(state: GlobalState, tool_input: dict) -> tuple[bool, Optional[str]]:
    valid, err = _validate_plot_compare(state, tool_input)
    if not valid:
        return False, err
    data_file = (state.get("base_simulation_file") or "").strip()
    out_dir = output_dir_from_context(state, tool_input, data_file=data_file)
    tool_input["output_dir"] = out_dir.strip("'\"") if out_dir else "."

    # Populate case_paths from uploaded files when not provided
    if not (tool_input.get("case_paths") or "").strip() and not (tool_input.get("case_stems") or "").strip():
        uploaded = state.get("uploaded_files") or []
        smspec_files = [u.strip() for u in uploaded if (u or "").strip().upper().endswith(".SMSPEC")]
        data_files = [u.strip() for u in uploaded if (u or "").strip().upper().endswith(".DATA")]
        if smspec_files:
            tool_input["case_paths"] = ",".join(smspec_files)
        elif len(data_files) >= 2:
            tool_input["case_paths"] = ",".join(data_files)

    if not (tool_input.get("metric_request") or "").strip():
        user_input = (state.get("user_input") or state.get("input") or "").strip()
        try:
            inferred = infer_plot_metric_with_llm(user_input)
        except AmbiguousQueryError as e:
            return False, str(e)
        if inferred:
            tool_input["metric_request"] = inferred
        else:
            return False, (
                "Could not determine the requested metric from your query. "
                "Please specify the metric explicitly (e.g. FOPT, FOPR) or describe it clearly. "
            )
    return True, None


def _validate_simulation_input_tools(state: GlobalState, tool_input: dict) -> tuple[bool, Optional[str]]:
    data_file = (tool_input.get("data_file") or tool_input.get("file_path") or "").strip()
    if not data_file and state.get("uploaded_files"):
        for u in state.get("uploaded_files", []):
            if (u or "").strip().upper().endswith(".DATA"):
                tool_input["data_file"] = tool_input.get("data_file") or u.strip()
                tool_input["file_path"] = tool_input.get("file_path") or u.strip()
                data_file = u.strip()
                break
    if not (tool_input.get("data_file") or tool_input.get("file_path")):
        return False, ("Tool requires a simulator primary input file. Please upload a .DATA file or provide file_path/data_file.")
    path = (tool_input.get("data_file") or tool_input.get("file_path") or "").strip()
    if path and not path.upper().endswith(".DATA"):
        return False, (
            "Tool requires a simulator primary input file with extension .DATA. "
            "The provided file does not have a .DATA extension (e.g. .pdf is not supported)."
        )
    return True, None


def _validate_run_flow_diagnostics(state: GlobalState, tool_input: dict) -> tuple[bool, Optional[str]]:
    case_path = (tool_input.get("case_path") or "").strip()
    if not case_path and state.get("uploaded_files"):
        for u in state.get("uploaded_files", []):
            if (u or "").strip().upper().endswith(".DATA"):
                tool_input["case_path"] = u.strip()
                case_path = u.strip()
                break
    if not case_path and (state.get("base_simulation_file") or "").strip():
        tool_input["case_path"] = (state.get("base_simulation_file") or "").strip()
        case_path = tool_input["case_path"]
    if not case_path:
        return False, (
            "Flow diagnostics requires a .DATA file path. "
            "Please upload a .DATA file or provide case_path."
        )
    if not case_path.upper().endswith(".DATA"):
        return False, (
            "Flow diagnostics requires a simulator input file with .DATA extension. "
            "The simulation must have been run with RPTRST FLOWS."
        )
    return True, None


_ValidatorFn = Callable[[GlobalState, dict], tuple[bool, Optional[str]]]

TOOL_VALIDATORS: dict[str, _ValidatorFn] = {
    "run_and_heal": _validate_run_and_heal,
    "simulator_manual": _validate_rag,
    "simulator_examples": _validate_rag,
    PLOT_SUMMARY_TOOL: _validate_plot_summary,
    PLOT_COMPARE_TOOL: _validate_plot_compare_full,
    "run_flow_diagnostics": _validate_run_flow_diagnostics,
}
for _t in SIMULATION_INPUT_TOOLS:
    if _t != "run_and_heal":
        TOOL_VALIDATORS[_t] = _validate_simulation_input_tools


def validate_args_and_get_update(state: GlobalState) -> tuple[bool, Optional[str], list[SkillUsed]]:
    routing = list(state.get("routing_to") or [])
    if not routing:
        return False, "No skill/tool was selected.", routing

    r = routing[-1]
    tool_name = (r.get("tool_name") or "").strip()
    tool_input = dict(r.get("tool_input") or {})

    validator = TOOL_VALIDATORS.get(tool_name)
    if validator:
        valid, err = validator(state, tool_input)
        if not valid:
            return False, err, routing
        if tool_name in ("simulator_manual", "simulator_examples"):
            tool_input["collection_name"] = tool_name
        routing[-1] = {**r, "tool_input": tool_input}
        return True, None, routing
    return True, None, routing
