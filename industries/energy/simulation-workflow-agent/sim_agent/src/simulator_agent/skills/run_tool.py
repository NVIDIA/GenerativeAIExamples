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
Standalone runner for a single simulator tool.

Run one tool by name with a dict of arguments, without invoking LangGraph.
Useful for testing and scripting.

Usage (Python):
    from simulator_agent.skills.run_tool import run_tool, get_tool, list_tools

    result = run_tool("parse_simulation_input_file", {"file_path": "/path/to/CASE.DATA"})
    print(result)

Usage (CLI):
    python -m simulator_agent.skills.run_tool parse_simulation_input_file '{"file_path": "/path/to/CASE.DATA"}'
    python -m simulator_agent.skills.run_tool --list

Usage (inside Docker):
    docker exec -it sim-agent bash
    python -m simulator_agent.skills.run_tool --list
    python -m simulator_agent.skills.run_tool parse_simulation_input_file '{"file_path": "data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA"}'
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Tuple

from simulator_agent.skills.input_file_skill import (
    modify_simulation_input_file,
    parse_simulation_input_file,
    patch_simulation_input_keyword,
)
from simulator_agent.skills.results_skill import (
    read_grid_properties,
    read_simulation_summary,
    run_flow_diagnostics,
)
from simulator_agent.skills.simulation_skill import (
    run_and_heal,
    monitor_simulation,
    stop_simulation,
)
from simulator_agent.skills.plot_skill import (
    plot_compare_summary_metric,
    plot_summary_metric,
)

# Tool list for agent wiring and standalone invocation
# run_and_heal is the primary run tool; run_simulation is internal-only (used by run_and_heal)
SIMULATION_TOOLS = [
    parse_simulation_input_file,
    modify_simulation_input_file,
    patch_simulation_input_keyword,
    run_and_heal,
    monitor_simulation,
    stop_simulation,
    plot_summary_metric,
    plot_compare_summary_metric,
    read_simulation_summary,
    read_grid_properties,
    run_flow_diagnostics,
]


def _tool_map() -> Dict[str, Any]:
    """Build name -> tool mapping."""
    return {t.name: t for t in SIMULATION_TOOLS}


def get_tool(name: str):
    """Return the tool instance for the given name, or None if not found."""
    return _tool_map().get(name)


def list_tools() -> List[Tuple[str, str]]:
    """Return list of (tool_name, description) for all simulator tools."""
    m = _tool_map()
    return [(n, (getattr(t, "description", None) or "")) for n, t in sorted(m.items())]


def run_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """
    Invoke a single tool by name with the given arguments.

    Args:
        tool_name: Name of the tool (e.g. "parse_simulation_input_file", "run_and_heal").
        args: Dict of arguments matching the tool's schema (e.g. {"file_path": "/path/to/CASE.DATA"}).

    Returns:
        The tool's return value (usually a string).

    Raises:
        ValueError: If tool_name is unknown.
    """
    tool = get_tool(tool_name)
    if tool is None:
        known = ", ".join(sorted(_tool_map()))
        raise ValueError(f"Unknown tool: {tool_name}. Available: {known}")
    if hasattr(tool, "invoke"):
        return tool.invoke(args)
    if hasattr(tool, "run"):
        return tool.run(args)
    return tool(**args)


def main() -> int:
    """CLI entry: run_tool <tool_name> [args_json] or --list."""
    argv = sys.argv[1:]
    if not argv:
        print("Usage: python -m simulator_agent.skills.run_tool <tool_name> [args_json]", file=sys.stderr)
        print("       python -m simulator_agent.skills.run_tool --list", file=sys.stderr)
        return 1

    if argv[0] in ("--list", "-l"):
        for name, desc in list_tools():
            short = (desc or "")[:70] + ("..." if len(desc or "") > 70 else "")
            print(f"  {name}")
            if short:
                print(f"    {short}")
        return 0

    tool_name = argv[0]
    args_str = argv[1] if len(argv) > 1 else "{}"
    try:
        args = json.loads(args_str)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON for arguments: {e}", file=sys.stderr)
        return 1

    if not isinstance(args, dict):
        print("Arguments must be a JSON object.", file=sys.stderr)
        return 1

    try:
        result = run_tool(tool_name, args)
        print(result)
        return 0
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Tool error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
