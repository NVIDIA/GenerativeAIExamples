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
Run pre-defined agent test inputs (run, plot, scenario, compare).

Sequential execution: each turn's chat_history carries forward to the next.
Use --interactive to be prompted for HITL approvals; omit for batch/CI mode.
Use --verbose to enable INFO logging (e.g. for debugging infer_plot_metric LLM calls).
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Ensure src is on path when run from sim_agent root
_script_dir = Path(__file__).resolve().parent
_src = _script_dir.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from simulator_agent import app, base_state, run_one_input

# Paths (Docker /workspace/sim_agent layout)
_BASE_DIR = "/workspace/sim_agent/data/example_cases/SPE10/CASE"

TEST_INPUTS = [
    {
        **base_state(),
        "user_input": "run the simulation",
        "base_simulation_file": "",
        "uploaded_files": [f"{_BASE_DIR}/SPE10_TOPLAYER.DATA"],
        "output_dir": _BASE_DIR,
    },
    {
        **base_state(),
        "user_input": "plot field cumulative oil production",
        "base_simulation_file": f"{_BASE_DIR}/SPE10_TOPLAYER.DATA",
        "uploaded_files": [f"{_BASE_DIR}/SPE10_TOPLAYER.DATA"],
        "output_dir": _BASE_DIR,
    },
    {
        **base_state(),
        "user_input": "Run flow diagnostics on the attached case to compute time-of-flight and injector-producer allocation",
        "base_simulation_file": f"{_BASE_DIR}/SPE10_TOPLAYER.DATA",
        "uploaded_files": [f"{_BASE_DIR}/SPE10_TOPLAYER.DATA"],
        "output_dir": _BASE_DIR,
    },
    {
        **base_state(),
        "user_input": "Test a scenario with increased water injection rate (12) at 'I1'. The baseline case is attached.",
        "base_simulation_file": f"{_BASE_DIR}/SPE10_TOPLAYER.DATA",
        "uploaded_files": [f"{_BASE_DIR}/SPE10_TOPLAYER.DATA"],
        "output_dir": _BASE_DIR,
    },
    # {
    #     **base_state(),
    #     "user_input": "Help me understand why the new scenario shows higher oil production than the baseline case",
    #     "base_simulation_file": "",
    #     "uploaded_files": [
    #         f"{_BASE_DIR}/SPE10_TOPLAYER.DATA",
    #         f"{_BASE_DIR}/SPE10_TOPLAYER_AGENT_GENERATED.DATA",
    #     ],
    #     "output_dir": _BASE_DIR,
    # },
    {
        **base_state(),
        "user_input": "compare field cumulative oil production",
        "base_simulation_file": "",
        "uploaded_files": [
            f"{_BASE_DIR}/SPE10_TOPLAYER.DATA",
            f"{_BASE_DIR}/SPE10_TOPLAYER_AGENT_GENERATED.DATA",
        ],
        "output_dir": f"{_BASE_DIR}/",
    },
    {
        **base_state(),
        "user_input": "run the simulation",
        "base_simulation_file": "",
        "uploaded_files": [f"{_BASE_DIR}/SPE10_TOPLAYER_INFILL_TEST.DATA"],
        "output_dir": _BASE_DIR,
    },
]


def _fmt(val: Any) -> str:
    if val is None:
        return "None"
    if isinstance(val, str):
        return val
    return json.dumps(val, indent=2, default=str)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run agent test suite (run, plot, scenario, compare)")
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Config file path (sets CONFIG_PATH)",
    )
    parser.add_argument(
        "--log-file",
        metavar="PATH",
        help="Write stdout/stderr to this file",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for HITL approvals (default: auto-approve for batch/CI)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO logging (e.g. for debugging plot metric inference)",
    )
    parser.add_argument(
        "--turn",
        type=int,
        metavar="N",
        help="Run only turn N (1-based). Uses empty chat_history.",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    if args.config:
        import os
        os.environ["CONFIG_PATH"] = os.path.abspath(args.config)

    use_interactive = args.interactive
    auto_approval = "yes go ahead and run it" if not use_interactive else ""

    # Tee to log file when --log-file is set
    _log_f = None
    _orig_stdout, _orig_stderr = sys.stdout, sys.stderr
    if args.log_file:
        _log_f = open(args.log_file, "w", encoding="utf-8")

        class _Tee:
            def __init__(self, stream, f):
                self._stream = stream
                self._file = f

            def write(self, data):
                self._stream.write(data)
                self._file.write(data)
                self._file.flush()

            def flush(self):
                self._stream.flush()
                self._file.flush()

        sys.stdout = _Tee(_orig_stdout, _log_f)
        sys.stderr = _Tee(_orig_stderr, _log_f)

    try:
        shared_chat_history = []
        indices = (
            [args.turn]
            if args.turn is not None
            else list(range(1, len(TEST_INPUTS) + 1))
        )
        for idx in indices:
            if idx < 1 or idx > len(TEST_INPUTS):
                print(f"Error: --turn {idx} out of range (1-{len(TEST_INPUTS)})")
                return 1
            base_input = TEST_INPUTS[idx - 1]
            sep = "=" * 60
            print(f"\n{sep}")
            print(f"  TURN {idx}: {base_input.get('user_input', '')!r}")
            print(sep)

            turn_input = dict(base_input)
            turn_input["chat_history"] = list(shared_chat_history)
            thread = {"configurable": {"thread_id": f"test_thread_{idx}"}}

            out = run_one_input(turn_input, thread, use_interactive, auto_approval)
            shared_chat_history = list(out.get("chat_history") or [])

            print(f"\n--- Turn {idx} result ---")
            print("agent_final_output:\n", _fmt(out.get("agent_final_output")))
            print("routing_to:\n", _fmt(out.get("routing_to")))
            if out.get("internal_trajectory"):
                print("internal_trajectory (last 3 steps):\n", _fmt(out["internal_trajectory"][-3:]))
            print(f"chat_history length after turn {idx}:", len(shared_chat_history))

        print(f"\n{'=' * 60}")
        print("All turns complete.")
        return 0
    finally:
        if _log_f is not None:
            sys.stdout, sys.stderr = _orig_stdout, _orig_stderr
            _log_f.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
