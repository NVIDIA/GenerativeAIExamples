#!/usr/bin/env python3
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
Self-Heal Chain Script

This script implements a chain that:
1. Runs a reservoir simulation in parallel with report-file wait+error parsing.
2. If errors are found:
   - Uses a ReAct agent (with input_file_tools) to produce a fixed simulator input file.

Usage:
    python -m simulator_agent.skills.simulation_skill.scripts.self_heal_chain \
        --primary-input-file /workspace/sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA

    The report directory is derived from the primary input file path (same directory).
    Optional: Add --config to load LLM settings from a config.yaml
        --config /workspace/sim_agent/config/config.yaml
"""

import argparse
import json
import os
import re
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

from simulator_agent.skills.input_file_skill import (
    patch_simulation_input_keyword,
    modify_simulation_input_file,
)
from simulator_agent.skills.input_file_skill.utils import find_keyword_block

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA as ReActLLM
except ImportError:
    ReActLLM = None

# Report polling
_REPORT_POLL_INTERVAL_SEC = 2
_REPORT_MAX_WAIT_SEC = 300
_REPORT_LOG_INTERVAL = 5

EMPTY_ERROR_INFO = {"error_found_flag": False, "errors": [], "patch_arguments": [], "error_count": 0}

# Common simulator pattern: "Please increase item N of KEYWORD to at least M"
_INCREASE_PATTERN = re.compile(
    r"Please\s+increase\s+item\s+(\d+)\s+of\s+(\w+)\s+to\s+at\s+least\s+(\d+)",
    re.IGNORECASE,
)


# ============================================================================
# Report file helpers (find_report_file, parse_report_errors_for_patching)
# ============================================================================

def find_report_file(work_dir: str, data_file: Optional[str] = None) -> Optional[str]:
    """
    Return path to the simulator report file (e.g., .PRT) for the current run.

    When data_file is provided, prefer the report matching the input file stem
    (simulators typically create {stem}.PRT for {stem}.DATA). This avoids picking
    a stale report from a different case when multiple report files exist.
    """
    p = Path(work_dir)
    if not p.exists():
        return None
    if data_file:
        data_path = Path(data_file)
        preferred = p / f"{data_path.stem}.PRT"
        if preferred.exists():
            return str(preferred)
        # Matching PRT not found yet - don't use a wrong file
        return None
    prt_files = list(p.glob("*.PRT"))
    return str(prt_files[0]) if prt_files else None


def parse_report_errors_for_patching(data_file: str, work_dir: str) -> Dict[str, Any]:
    """
    Parse a simulator report file for actionable errors (e.g. 'Please increase item N of KEYWORD to at least M').

    Returns:
        dict with keys: error_found_flag (bool), errors (list), patch_arguments (list), error_count (int).
    """
    report_path = find_report_file(work_dir, data_file=data_file)
    if not report_path:
        return EMPTY_ERROR_INFO
    try:
        content = Path(report_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return EMPTY_ERROR_INFO

    errors = []
    patch_arguments = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        m = _INCREASE_PATTERN.search(line)
        if m:
            item_index = int(m.group(1))
            keyword = m.group(2).upper()
            new_value = int(m.group(3))
            errors.append({"keyword": keyword, "line_number": line_num, "message": line.strip()})
            patch_arguments.append({"keyword": keyword, "item_index": item_index, "new_value": new_value})

    return {
        "error_found_flag": len(errors) > 0,
        "errors": errors,
        "patch_arguments": patch_arguments,
        "error_count": len(errors),
    }


# ============================================================================
# ReAct agent tool wrappers
# ============================================================================

def _parse_agent_input(action_input) -> dict:
    """Parse ReAct action input (string or dict) to a dict."""
    if isinstance(action_input, dict):
        return action_input
    return json.loads(action_input.strip())


def _make_find_keyword_block_tool():
    """Tool: find the (start_line, end_line) of a keyword block in a simulator input file (1-based)."""

    @tool("find_keyword_block")
    def _find_keyword_block_tool(action_input: str) -> str:
        """Find the line range of a keyword block in a simulator input file. Input must be a JSON string with keys: file_path, keyword. Returns 'start_line end_line' (1-based) or an error message."""
        try:
            data = _parse_agent_input(action_input)
            file_path = data.get("file_path")
            keyword = data.get("keyword")
            if not file_path or not keyword:
                return "Error: action_input must be JSON with 'file_path' and 'keyword' keys."
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"
            content = path.read_text(encoding="utf-8", errors="replace")
            block = find_keyword_block(content, keyword)
            if block is None:
                return f"Keyword '{keyword}' not found in file."
            start, end = block
            return f"Keyword '{keyword}' block: lines {start + 1} to {end + 1} (1-based)."
        except json.JSONDecodeError as e:
            return f"Error: invalid JSON for find_keyword_block: {e!s}"
        except Exception as e:
            return f"Error: {e!s}"

    return _find_keyword_block_tool


def _make_patch_simulation_input_keyword_tool():
    """Wrap patch_simulation_input_keyword so it accepts a single JSON string from the ReAct agent."""

    @tool("patch_simulation_input_keyword")
    def patch_simulation_input_keyword_tool(action_input: str) -> str:
        """Change one keyword block in a simulator input file. Input: JSON with file_path, keyword, output_path; optionally item_index, new_value (1-based), or new_block_content."""
        try:
            data = _parse_agent_input(action_input)
        except json.JSONDecodeError as e:
            return f"Error: invalid JSON for patch_simulation_input_keyword: {e!s}"
        if not data.get("file_path") or not data.get("keyword") or not data.get("output_path"):
            return "Error: patch_simulation_input_keyword requires file_path, keyword, and output_path."
        return patch_simulation_input_keyword.invoke(data)

    return patch_simulation_input_keyword_tool


def _make_modify_simulation_input_file_tool():
    """Wrap modify_simulation_input_file so it accepts a single JSON string from the ReAct agent."""

    @tool("modify_simulation_input_file")
    def modify_simulation_input_file_tool(action_input: str) -> str:
        """Modify a simulator input file from natural language. Input: JSON with file_path, modifications; optionally output_path, target_keyword."""
        try:
            data = _parse_agent_input(action_input)
        except json.JSONDecodeError as e:
            return f"Error: invalid JSON for modify_simulation_input_file: {e!s}"
        if not data.get("file_path") or not data.get("modifications"):
            return "Error: modify_simulation_input_file requires file_path and modifications."
        return modify_simulation_input_file.invoke(data)

    return modify_simulation_input_file_tool


# ============================================================================
# ReAct prompt
# ============================================================================

REACT_FIX_PROMPT_TEMPLATE = """You are an expert at fixing reservoir simulator input files based on simulator report/error messages.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (as JSON when the tool expects multiple arguments)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the path to the fixed simulator input file you wrote, or a brief explanation if you could not fix it

Begin!

Question: {input}
Thought:{agent_scratchpad}"""


# ============================================================================
# Core chain functions
# ============================================================================

def _print_step(step_num: int, title: str) -> None:
    """Print a step header."""
    print("=" * 80)
    print(f"STEP {step_num}: {title}")
    print("=" * 80)


def _resolve_fixed_output_path(
    data_file: str,
    output_file: Optional[str],
    work_dir: str,
) -> str:
    """Resolve path for the fixed simulator input file (<stem>_FIXED<suffix>)."""
    input_path = Path(data_file)
    output_filename = f"{input_path.stem}_FIXED{input_path.suffix}"
    if output_file:
        arg_path = Path(output_file)
        if arg_path.suffix and not arg_path.is_dir():
            return os.path.normpath(output_file)
        output_dir = output_file.rstrip(os.sep)
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, output_filename)
    output_dir = work_dir.rstrip(os.sep)
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, output_filename)


def _create_react_llm(config_path: Optional[str]):
    """Create ChatNVIDIA LLM from config or env. Returns None if unavailable."""
    config: Dict[str, Any] = {}
    if config_path:
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            pass
    if config and ReActLLM is not None:
        llm_cfg = config.get("llm", {})
        model = llm_cfg.get("model_name") or os.getenv(
            "SIM_LLM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1.5"
        )
        try:
            return ReActLLM(
                model=model,
                temperature=llm_cfg.get("temperature", 0.7),
                max_tokens=llm_cfg.get("max_tokens", 4096),
            )
        except Exception:
            pass
    if ReActLLM is not None:
        try:
            model = os.getenv("SIM_LLM_MODEL")
            if not model:
                from simulator_agent.config import get_config
                model = get_config().get_llm_model(use_for="tool")
            return ReActLLM(model=model, max_tokens=4096)
        except Exception:
            pass
    return None


def _heal_result(success: bool, message: str, fixed_file_path: Optional[str] = None) -> Dict[str, Any]:
    """Build a consistent result dict for run_self_heal_chain."""
    return {"success": success, "fixed_file_path": fixed_file_path, "message": message}


def _wait_and_parse_report(data_file: str, work_dir: str) -> Dict[str, Any]:
    """Poll work_dir for a simulator report file (e.g., .PRT), then parse for errors."""
    wait_start = time.time()
    wait_count = 0
    while True:
        report_path = find_report_file(work_dir, data_file=data_file)
        if report_path is not None:
            print(f"[report branch] Found report file: {report_path}")
            return parse_report_errors_for_patching(data_file, work_dir)
        elapsed = time.time() - wait_start
        if elapsed > _REPORT_MAX_WAIT_SEC:
            print(f"[report branch] No report file found after {elapsed:.1f}s in: {work_dir}")
            return EMPTY_ERROR_INFO
        wait_count += 1
        if wait_count % _REPORT_LOG_INTERVAL == 0:
            print(f"[report branch] Waiting for report file (attempt {wait_count}, elapsed: {elapsed:.1f}s)")
        time.sleep(_REPORT_POLL_INTERVAL_SEC)


def run_fix_with_react_agent(
    data_file: str,
    work_dir: str,
    output_file: Optional[str],
    error_info: Dict[str, Any],
    config_path: Optional[str],
) -> Dict[str, Any]:
    """
    Use a ReAct agent with input_file_tools to fix the simulator input file based on report error info.
    Writes the fixed file to <stem>_FIXED<suffix>.
    """
    output_file_path = _resolve_fixed_output_path(data_file, output_file, work_dir)
    llm = _create_react_llm(config_path)
    if llm is None:
        return _heal_result(
            False,
            "ReAct agent requires langchain_nvidia_ai_endpoints.ChatNVIDIA (or NVIDIA_API_KEY set).",
        )

    agent_tools = [
        _make_find_keyword_block_tool(),
        _make_patch_simulation_input_keyword_tool(),
        _make_modify_simulation_input_file_tool(),
    ]
    prompt = PromptTemplate.from_template(REACT_FIX_PROMPT_TEMPLATE)
    agent = create_react_agent(llm, agent_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=agent_tools, verbose=True, max_iterations=15, handle_parsing_errors=True
    )

    error_summary = json.dumps(
        {
            "errors": error_info.get("errors") or [],
            "patch_arguments": error_info.get("patch_arguments") or [],
            "error_count": error_info.get("error_count", 0),
        },
        indent=2,
    )
    task_input = (
        f"Fix the simulator input file. Input file: {data_file}. "
        f"Write the fixed file to: {output_file_path}. "
        f"Errors from the simulator report:\n{error_summary}\n\n"
        "Use find_keyword_block to locate keyword blocks, then patch_simulation_input_keyword to change a single keyword "
        "(set output_path to the fixed file path, use item_index/new_value from the error message when available). "
        "If patch_arguments lack item_index/new_value, infer from the error text or use modify_simulation_input_file. "
        "Always write the result to the exact output path given above. "
        "When done, give the Final Answer with the fixed file path."
    )

    try:
        result = agent_executor.invoke({"input": task_input})
        output = result.get("output") or str(result)
        if Path(output_file_path).exists():
            return _heal_result(True, f"Fixed file created: {output_file_path}", output_file_path)
        return _heal_result(False, output or "ReAct agent did not confirm writing the fixed file.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = str(e).strip()
        if "401" in msg or "Unauthorized" in msg or "Authentication" in msg:
            msg = "ReAct agent LLM authentication failed (check NVIDIA_API_KEY). " + msg
        return _heal_result(
            False, f"ReAct agent failed: {msg}",
            output_file_path if Path(output_file_path).exists() else None,
        )


def _run_simulation(data_file: str, work_dir: str, num_mpi_processes: int, run_simulation_tool) -> str:
    """Run the reservoir simulator in foreground and return result string."""
    result = run_simulation_tool.invoke({
        "data_file": data_file,
        "background": False,
        "output_dir": work_dir,
        "num_mpi_processes": num_mpi_processes,
    })
    return str(result) if not isinstance(result, str) else result


def run_self_heal_chain(
    data_file: str,
    work_dir: Optional[str] = None,
    output_file: Optional[str] = None,
    config_path: Optional[str] = None,
    num_mpi_processes: int = 1,
) -> Dict[str, Any]:
    """
    Run the reservoir simulator in parallel with report wait+parse; on failure auto-fix via ReAct agent.

    Returns:
        dict with keys: success (bool), fixed_file_path (str or None), message (str).
    """
    work_dir = (work_dir or "").strip() or str(Path(data_file).parent)
    output_file = (output_file or "").strip() or None
    config_path = (config_path or "").strip() or None
    if not config_path and os.environ.get("CONFIG_PATH"):
        config_path = os.environ.get("CONFIG_PATH", "").strip() or None

    try:
        from simulator_agent.skills.simulation_skill.scripts.simulation_tools import run_simulation as _run_simulation_tool

        run_simulation_branch = RunnableLambda(
            lambda x: _run_simulation(
                x["data_file"], work_dir, x.get("num_mpi_processes", 1), _run_simulation_tool
            )
        )
        report_parse_branch = RunnableLambda(
            lambda x: _wait_and_parse_report(x["data_file"], x["work_dir"])
        )
        parallel_chain = RunnableParallel(
            branches={"run_simulation_result": run_simulation_branch, "error_info": report_parse_branch}
        )

        _print_step(1, "Running simulation in parallel with report error parsing")
        parallel_result = parallel_chain.invoke({
            "data_file": data_file,
            "work_dir": work_dir,
            "num_mpi_processes": num_mpi_processes,
        })
        branches = parallel_result.get("branches", parallel_result)
        error_info = branches.get("error_info")

        if error_info is None:
            return _heal_result(False, "Report error parsing did not return results.")
        if not error_info.get("error_found_flag"):
            return _heal_result(True, "Simulation completed; no actionable errors found in report.")

        _print_step(2, "ReAct agent fixing simulator input file using report error info")
        fix_result = run_fix_with_react_agent(
            data_file=data_file,
            work_dir=work_dir,
            output_file=output_file,
            error_info=error_info,
            config_path=config_path,
        )
        fixed_path = fix_result.get("fixed_file_path")
        if not fixed_path or not Path(fixed_path).exists():
            return fix_result

        _print_step(3, "Re-running simulation on fixed input file")
        rerun_str = run_simulation_branch.invoke({
            "data_file": fixed_path,
            "work_dir": work_dir,
            "num_mpi_processes": num_mpi_processes,
        })
        if "Simulation completed successfully" in rerun_str:
            return _heal_result(
                True,
                f"Fixed file created and re-run succeeded.\n{fix_result.get('message', '')}",
                fixed_path,
            )
        return _heal_result(
            False,
            f"Fixed file created but re-run failed.\n{rerun_str}",
            fixed_path,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return _heal_result(False, f"Self-heal chain failed: {e!s}")


# ============================================================================
# LangChain tool: run_and_heal
# ============================================================================

class RunAndHealInput(BaseModel):
    data_file: str = Field(..., description="Path to the simulator input (e.g., DATA) file to run")
    output_dir: Optional[str] = Field(
        default=None,
        description="Output directory for simulation results and fixed files (default: same directory as input file)",
    )
    num_mpi_processes: int = Field(
        default=1,
        description="Number of MPI processes (np). When > 1, runs via mpirun -np N flow ...",
    )


@tool("run_and_heal", args_schema=RunAndHealInput)
def run_and_heal(
    data_file: str,
    output_dir: Optional[str] = None,
    num_mpi_processes: int = 1,
) -> str:
    """
    Run a reservoir simulation and automatically attempt to fix and re-run on failure.
    Runs the simulation and monitors the report file in parallel; if actionable errors are found,
    a ReAct agent patches the simulator input file and reports the result.
    Use this as the primary tool for running simulations (replaces run_simulation).
    """
    result = run_self_heal_chain(
        data_file=data_file,
        work_dir=output_dir or None,
        output_file=output_dir or None,
        num_mpi_processes=num_mpi_processes,
    )
    if result.get("fixed_file_path"):
        if result.get("success"):
            return (
                f"Simulation completed with auto-fix.\n"
                f"Fixed file: {result['fixed_file_path']}\n"
                f"{result.get('message', '')}"
            )
        return (
            f"Simulation auto-fixed but re-run failed.\n"
            f"Fixed file: {result['fixed_file_path']}\n"
            f"{result.get('message', '')}"
        )
    if result.get("success"):
        return f"Simulation completed successfully.\n{result.get('message', '')}"
    return f"Simulation run-and-heal failed.\n{result.get('message', 'Unknown error')}"


# ============================================================================
# CLI entry
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Self-Heal Chain: run reservoir simulation + auto-fix on report errors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--primary-input-file", type=str, required=True,
                        help="Path to the primary simulator input file")
    parser.add_argument("--config", type=str, default=None,
                        help="Optional path to config.yaml to configure LLM")
    parser.add_argument("--output-file", type=str, default=None,
                        help="Output directory or full file path for the fixed simulator input file")
    args = parser.parse_args()

    result = run_self_heal_chain(
        data_file=args.primary_input_file,
        output_file=args.output_file or None,
        config_path=args.config or None,
    )
    if result.get("fixed_file_path"):
        print("\n" + "=" * 80)
        print("CHAIN COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Fixed file: {result['fixed_file_path']}")
    elif not result.get("success"):
        print("\n" + "=" * 80)
        print("CHAIN FAILED")
        print("=" * 80)
        print(result.get("message", ""))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
