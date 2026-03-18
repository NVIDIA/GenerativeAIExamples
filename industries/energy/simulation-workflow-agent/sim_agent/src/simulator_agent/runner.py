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
Simulator agent runner: SimulatorAgent class, CLI, HITL helpers.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

from .config import AgentConfig, init_config, set_config
from .graph import app


# --- HITL approval parsing ---
_DECLINE_EXACT = frozenset({"n", "no", "never", "skip", "stop"})
_APPROVE_EXACT = frozenset({"y", "yes", "sure", "ok", "okay", "run", "confirm"})
_DECLINE_PHRASES = ("do not approve", "don't approve", "not approve", "decline", "reject", "cancel")
_APPROVE_PHRASES = ("approve", "go ahead", "run it", "please do", "yes", "run", "run diagnostics", "run flow diagnostics")


def _has_relaunch_message(state: dict[str, Any]) -> bool:
    msg = (state.get("agent_final_output") or "").lower()
    return "relaunch" in msg and ("fixed" in msg or "_fixed" in msg)


def _indicates_completed_run_or_plot(state: dict[str, Any]) -> bool:
    """True when agent_final_output shows run/plot already completed (not waiting for approval)."""
    msg = (state.get("agent_final_output") or "").lower()
    if not msg:
        return False
    if _has_relaunch_message(state):
        return False  # relaunch is handled separately
    return (
        "simulation completed" in msg
        or "plot saved" in msg
        or "comparison plot saved" in msg
    )


def is_waiting_for_approval(state: dict[str, Any]) -> bool:
    """True when the graph interrupted at approval_needed (run_and_heal, plot, or flow diagnostics) and needs human_approve to continue."""
    routing = state.get("routing_to") or []
    if not routing:
        return False
    r = routing[-1]
    skill = (r.get("skill_name") or "").strip()
    tool = (r.get("tool_name") or "").strip()
    data_file = ((r.get("tool_input") or {}).get("data_file") or "").strip()
    needs = (
        (skill == "simulation_skill" and tool == "run_and_heal")
        or (skill == "plot_skill")
        or (tool == "run_and_heal" and data_file and "_FIXED" in data_file.upper())
        or (skill == "results_skill" and tool == "run_flow_diagnostics")
    )
    if not needs:
        return False
    if _has_relaunch_message(state):
        return False  # handled by is_asking_relaunch_confirmation
    # Run/plot already completed successfully — graph reached END, routing_to not yet cleared
    if _indicates_completed_run_or_plot(state):
        return False
    return True


def is_asking_relaunch_confirmation(state: dict[str, Any]) -> bool:
    return _has_relaunch_message(state)


def _is_decline(text: str) -> bool:
    if text in _DECLINE_EXACT:
        return True
    return any(p in text for p in _DECLINE_PHRASES)


def _is_approve(text: str) -> bool:
    if text in _APPROVE_EXACT:
        return True
    return any(p in text for p in _APPROVE_PHRASES)


def parse_approval_from_user_input(user_input: str) -> tuple[bool, str, str]:
    """Parse user input for HITL approval. Returns (approved, original_input, short)."""
    raw = (user_input or "").strip()
    if not raw:
        return False, "I do NOT approve", "n"
    text = raw.lower()
    if _is_decline(text):
        return False, raw, "n"
    if _is_approve(text):
        return True, raw, "y"
    # For flow diagnostics: bare numbers (e.g. "1,5,10") count as approval with those steps
    if re.search(r"\d", raw):
        return True, raw, "y"
    return False, raw, "n"  # ambiguous → reject


def _parse_time_step_ids_from_approval(text: str) -> Optional[list[int]]:
    """Extract time step IDs from approval input (e.g. '1,5,10' or '1 5 10'). Returns None if no numbers (use default)."""
    if not (text or "").strip():
        return None
    ids = [int(m) for m in re.findall(r"\d+", text)]
    return ids if ids else None


def _is_flow_diagnostics_pending(state: dict[str, Any]) -> bool:
    """True when waiting for approval and the pending tool is run_flow_diagnostics."""
    routing = state.get("routing_to") or []
    if not routing:
        return False
    r = routing[-1]
    return (r.get("skill_name") or "").strip() == "results_skill" and (r.get("tool_name") or "").strip() == "run_flow_diagnostics"


def parse_relaunch_confirmation(user_input: str) -> bool:
    """Parse user input for relaunch confirmation (yes/no)."""
    raw = (user_input or "").strip()
    if not raw:
        return False
    text = raw.lower()
    if _is_decline(text) or "don't" in text or "do not" in text:
        return False
    return _is_approve(text) or "run" in text


def base_state() -> dict[str, Any]:
    return {
        "chat_history": [],
        "routing_to": [],
        "agent_final_output": None,
        "skill_failure_reason": None,
    }


def run_one_input(
    turn_input: dict[str, Any],
    thread: dict[str, Any],
    use_interactive: bool,
    auto_approval: str,
) -> dict[str, Any]:
    """Invoke the graph for one user turn, handling HITL approval and relaunch loops."""
    print("--- invoke ---")
    out = app.invoke(turn_input, config=thread)
    print("agent_final_output:", out.get("agent_final_output"))

    while True:
        if is_waiting_for_approval(out):
            if use_interactive:
                if _is_flow_diagnostics_pending(out):
                    prompt = (
                        "Do you want me to run flow diagnostics? If yes, which time step(s) would you like to analyze? "
                        "(default: last step only — press Enter or yes to confirm and use default, or enter e.g. 1,5,10): "
                    )
                    approval_user = input(f"\n{prompt}").strip() or auto_approval
                else:
                    approval_user = input(
                        "\nApproval required. Enter 'I approve' / 'yes go ahead' / 'no': "
                    ).strip() or auto_approval
            else:
                approval_user = auto_approval
            print("Approval input:", repr(approval_user))
            if _is_flow_diagnostics_pending(out) and not (approval_user or "").strip():
                # Flow diagnostics: empty = "use default" (last step) = approve
                approved, approved_str, approveYN = True, "(use default)", "y"
            else:
                approved, approved_str, approveYN = parse_approval_from_user_input(approval_user)
            print(f"Parsed → approved={approved}, approveYN={approveYN!r}")

            update_payload: dict[str, Any] = {"human_approve": approveYN, "human_approve_input": approved_str}
            if approved and _is_flow_diagnostics_pending(out):
                time_step_ids = _parse_time_step_ids_from_approval(approval_user)
                if time_step_ids is not None:
                    routing = list(out.get("routing_to") or [])
                    if routing:
                        last = dict(routing[-1])
                        ti = dict(last.get("tool_input") or {})
                        ti["time_step_ids"] = time_step_ids
                        last["tool_input"] = ti
                        routing[-1] = last
                        update_payload["routing_to"] = routing

            app.update_state(
                thread,
                update_payload,
                as_node="approval_needed",
            )
            print("--- Resuming (invoke(None)) ---")
            out = app.invoke(None, config=thread)
            print("agent_final_output:", out.get("agent_final_output"))
            continue

        if is_asking_relaunch_confirmation(out):
            if use_interactive:
                relaunch_user = input(
                    "\nRelaunch with fixed file? (yes/run to confirm, no to skip): "
                ).strip()
            else:
                relaunch_user = "yes"
            if parse_relaunch_confirmation(relaunch_user):
                next_input = dict(out)
                next_input["user_input"] = relaunch_user.strip() or "yes"
                print("--- Invoke relaunch ---")
                out = app.invoke(next_input, config=thread)
                print("agent_final_output:", out.get("agent_final_output"))
            else:
                print("Relaunch declined.")
                break
            continue

        break

    return out


# --- SimulatorAgent ---
class SimulatorAgent:
    """
    LangGraph-based simulator agent. Wraps config and graph.
    Supports config injection for testability.
    """

    def __init__(
        self,
        config_path: str | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        if config is not None:
            set_config(config)
        else:
            init_config(config_path)
        self.graph = app  # built at module load

    def run_interactive(
        self,
        *,
        output_dir: str = ".",
        base_simulation_file: str = "",
        uploaded_files: Optional[list[str]] = None,
        log_file: Optional[str] = None,
    ) -> None:
        uploaded = list(uploaded_files or [])
        shared_chat_history: list = []
        thread = {"configurable": {"thread_id": "interactive"}}

        print("Simulation Assistant — Interactive mode")
        print("Type your query and press Enter. Commands: 'quit' or 'exit' to stop.")
        print("-" * 60)

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break

            turn_input: dict[str, Any] = {
                **base_state(),
                "user_input": user_input,
                "chat_history": list(shared_chat_history),
                "uploaded_files": uploaded,
                "output_dir": output_dir,
                "base_simulation_file": base_simulation_file or "",
            }

            out = run_one_input(turn_input, thread, use_interactive=True, auto_approval="")
            shared_chat_history = list(out.get("chat_history") or [])

            response = out.get("agent_final_output") or ""
            print(f"\nAssistant: {response}")
            if log_file and response:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"User: {user_input}\nAssistant: {response}\n\n")

    def run_single(
        self,
        query: str,
        *,
        uploaded_files: Optional[list[str]] = None,
        output_dir: str = ".",
        base_simulation_file: str = "",
    ) -> dict[str, Any]:
        """Run a single query and return the output state."""
        turn_input: dict[str, Any] = {
            **base_state(),
            "user_input": query,
            "uploaded_files": uploaded_files or [],
            "output_dir": output_dir,
            "base_simulation_file": base_simulation_file or "",
        }
        thread = {"configurable": {"thread_id": "single"}}
        return run_one_input(turn_input, thread, use_interactive=False, auto_approval="yes go ahead and run it")


def _resolve_config_path(cli_path: str | None) -> str | None:
    """Resolve config path from CLI or CONFIG_PATH env. Returns None for default."""
    if cli_path:
        return str(Path(cli_path).resolve())
    env = os.environ.get("CONFIG_PATH", "").strip()
    return env if env else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulation Assistant — LangGraph workflow for simulation tools"
    )
    parser.add_argument("--interactive", action="store_true", help="Run interactively: read queries from stdin")
    parser.add_argument("--input", metavar="QUERY", help="Single query (non-interactive)")
    parser.add_argument("--config", metavar="PATH", help="Config file path")
    parser.add_argument("--output-dir", default=".", help="Output directory for simulation results")
    parser.add_argument("--base-file", metavar="PATH", default="", help="Base simulator input file")
    parser.add_argument("--uploaded-files", metavar="PATH", nargs="*", default=[], help="Pre-loaded simulator input file paths")
    parser.add_argument("--log-file", metavar="PATH", help="Append interactions to this file")
    args = parser.parse_args()

    config_path = _resolve_config_path(args.config)
    agent = SimulatorAgent(config_path=config_path)

    if args.interactive:
        agent.run_interactive(
            output_dir=args.output_dir,
            base_simulation_file=args.base_file,
            uploaded_files=args.uploaded_files or None,
            log_file=args.log_file,
        )
        return

    if args.input:
        out = agent.run_single(
            args.input,
            uploaded_files=args.uploaded_files,
            output_dir=args.output_dir,
            base_simulation_file=args.base_file,
        )
        print("\n--- Result ---")
        print(out.get("agent_final_output", ""))
        return

    parser.print_help()
    print("\nUse --interactive for chat mode, or --input QUERY for a single query.")
    print("For the test suite, run: python scripts/run_agent_tests.py")
    sys.exit(1)


if __name__ == "__main__":
    main()
