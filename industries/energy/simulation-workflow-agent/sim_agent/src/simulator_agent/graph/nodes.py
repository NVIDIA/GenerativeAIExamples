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
LangGraph node functions: query_routing, check_args, execute_tools, etc.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from ..config import get_config
from llm_provider import ChatOpenAI
from ..skills.input_file_skill.utils import strip_think_blocks
from ..skills.run_tool import get_tool, run_tool
from ..state import GlobalState, SkillUsed, PLOT_COMPARE_TOOL, PLOT_SUMMARY_TOOL
from ..utils import (
    output_dir_from_context,
    trim_chat_history,
    build_tool_input_for_step,
    validate_args_and_get_update,
    infer_plot_metric_with_llm,
)
from ..routing import classify_query_llm, classify_query_rule_based
from .edges import _needs_approval

LOG = logging.getLogger(__name__)

_FLOW_DIAG_INTERPRET_PROMPT = """You are an expert reservoir engineer. Interpret the flow diagnostics below for the user.

RULES:
- Output ONLY the final interpretation. No <think> tags, no reasoning blocks, no step-by-step analysis.
- Be concise: 3–5 short paragraphs. Do not exceed 400 words.
- If the user asked a specific question (e.g. "why early breakthrough at P3?"), answer it directly.

Cover: (1) Key findings (sweep efficiency, dominant flow paths, breakthrough risk). (2) What the numbers mean. (3) If multiple time steps, note trends. (4) Direct answer to the user's question. (5) When relevant, use well I,J,K locations (grid indices) as indicators of well placement — e.g. wells at grid corners or edges may explain early breakthrough or connectivity patterns.

User question: {user_query}

Flow diagnostics output:
{flow_diagnostics_output}

Your concise expert interpretation (no <think> tags):"""


def _interpret_flow_diagnostics_llm(user_query: str, raw_output: str) -> str:
    """Use LLM to interpret flow diagnostics as a reservoir engineer."""
    try:
        llm = ChatOpenAI(model=get_config().get_llm_model(use_for="tool"), max_tokens=2048, temperature=0.2)
        prompt = _FLOW_DIAG_INTERPRET_PROMPT.format(
            user_query=user_query or "Interpret the flow diagnostics results.",
            flow_diagnostics_output=raw_output[:8000],  # Cap to avoid token limits
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        if hasattr(response, "content") and response.content:
            # Strip <think>...</think> blocks (reasoning) so user gets only the final interpretation
            cleaned = strip_think_blocks(response.content.strip())
            return cleaned if cleaned else raw_output
    except Exception as e:
        LOG.debug("Flow diagnostics LLM interpretation failed: %s", e)
    return raw_output


def query_routing(state: GlobalState) -> dict[str, Any]:
    user_input_preview = (state.get("user_input") or state.get("input") or "")[:80]
    LOG.debug("query_routing | user_input=%r", user_input_preview)
    query = (state.get("user_input") or state.get("input") or "").strip()

    history: list[BaseMessage] = list(state.get("chat_history") or [])
    history.append(HumanMessage(content=query))
    history = trim_chat_history(history)

    if state.get("pending_confirm_relaunch") and state.get("fixed_data_file_path"):
        q_lower = query.strip().lower()
        confirm_phrases = ("yes", "y", "run", "go ahead", "sure", "confirm", "ok", "okay", "please", "do it")
        if q_lower in confirm_phrases or any(p in q_lower for p in ("yes", "run", "go ahead", "sure", "confirm")):
            fixed_path = (state.get("fixed_data_file_path") or "").strip()
            new_routing: list[SkillUsed] = [{
                "skill_name": "simulation_skill",
                "tool_name": "run_and_heal",
                "tool_input": {
                    "data_file": fixed_path,
                    "output_dir": output_dir_from_context(state, {}, data_file=fixed_path),
                },
            }]
            trajectory_append = [
                {"step": "query_routing", "message": "User confirmed relaunch with fixed file", "data": {"fixed_path": fixed_path}},
            ]
            LOG.debug("relaunch confirmed -> run_and_heal with %r", fixed_path)
            return {
                "routing_to": new_routing,
                "pending_confirm_relaunch": False,
                "fixed_data_file_path": None,
                "pending_steps": [],
                "internal_trajectory": trajectory_append,
                "chat_history": history,
            }

    classification = classify_query_llm(query, state)
    skill = classification.get("skill") or "final_response"
    tool = classification.get("tool")
    tool_input = classification.get("tool_input") or {}
    agent_final_from_llm = classification.get("agent_final_output")

    uploaded = state.get("uploaded_files") or []
    run_intent = query and any(kw in query.lower() for kw in ("run", "execute", "simulate", "start"))
    has_data_upload = any((u or "").strip().upper().endswith(".DATA") for u in uploaded)
    if skill == "final_response" and run_intent and has_data_upload:
        skill = "simulation_skill"
        tool = "run_and_heal"
        tool_input = {}
        agent_final_from_llm = None

    q_lower = (query or "").strip().lower()
    plot_or_compare = "plot" in q_lower or "compare" in q_lower
    if skill == "final_response" and plot_or_compare:
        rule_based = classify_query_rule_based(query)
        if rule_based.get("skill") == "plot_skill" and rule_based.get("tool"):
            skill = rule_based["skill"]
            tool = rule_based["tool"]
            tool_input = rule_based.get("tool_input") or {}
            agent_final_from_llm = None
    elif not run_intent and plot_or_compare and tool == "run_and_heal":
        # User asked to plot/compare, not run — override mistaken run_and_heal from LLM
        rule_based = classify_query_rule_based(query)
        if rule_based.get("skill") == "plot_skill" and rule_based.get("tool"):
            skill = rule_based["skill"]
            tool = rule_based["tool"]
            tool_input = rule_based.get("tool_input") or {}
            agent_final_from_llm = None

    if not (tool_input.get("output_dir") or "").strip() and tool in (PLOT_SUMMARY_TOOL, PLOT_COMPARE_TOOL):
        built = build_tool_input_for_step(
            tool, query,
            uploaded_files=uploaded,
            base_simulation_file=state.get("base_simulation_file") or None,
        )
        if built.get("output_dir"):
            tool_input = {**tool_input, **built}

    new_routing: list[SkillUsed] = [{"skill_name": skill, "tool_name": tool or "", "tool_input": tool_input}]
    LOG.debug("query_routing -> skill=%r, tool=%r, tool_input=%s", skill, tool, tool_input)

    update: dict[str, Any] = {
        "routing_to": new_routing,
        "internal_trajectory": [
            {"query_routing": classification},
            {"step": "query_routing", "message": f"skill={skill!r}, tool={tool!r}", "data": {"skill": skill, "tool": tool, "tool_input": tool_input}},
        ],
        "chat_history": history,
        "pending_confirm_relaunch": False,
    }
    update["pending_steps"] = classification.get("pending_steps") or []

    if skill in ("chitchat", "final_response") or not tool:
        update["agent_final_output"] = (
            agent_final_from_llm
            if agent_final_from_llm
            else "I'm not sure which action to take. Please try: 'run the simulation' (with a simulator input file uploaded), "
            "'plot results', or ask a specific question about the simulator."
        )
    return update


def check_args(state: GlobalState) -> dict[str, Any]:
    routing_to = state.get("routing_to") or []
    LOG.debug("check_args | routing_to=%s", routing_to)
    valid, err, updated_routing = validate_args_and_get_update(state)
    trajectory_append = [
        {"step": "edge", "message": "query_routing -> check_args", "data": {"from": "query_routing", "to": "check_args"}},
        {"step": "check_args", "message": f"args_valid={valid}, skill_failure_reason={err!r}", "data": {"routing_to": routing_to, "args_valid": valid, "skill_failure_reason": err}},
    ]
    update: dict[str, Any] = {
        "args_valid": valid,
        "skill_failure_reason": err if not valid else None,
        "internal_trajectory": trajectory_append,
    }
    if valid:
        update["routing_to"] = updated_routing
    LOG.debug("check_args -> args_valid=%s, skill_failure_reason=%r", valid, err)
    return update


def approval_needed(state: GlobalState) -> dict[str, Any]:
    LOG.debug("approval_needed (waiting for human_approve)")
    routing = state.get("routing_to") or []
    if routing:
        r = routing[-1]
        skill = (r.get("skill_name") or "").strip()
        tool = (r.get("tool_name") or "").strip()
        if skill == "results_skill" and tool == "run_flow_diagnostics":
            prompt = (
                "Do you want me to run flow diagnostics? If yes, which time step(s) would you like to analyze? "
                "(default: last step only — press Enter or yes to confirm and use default, or enter e.g. 1,5,10): "
            )
            return {"agent_final_output": prompt}
    return {}


def advance_step(state: GlobalState) -> dict[str, Any]:
    pending = list(state.get("pending_steps") or [])
    LOG.debug("advance_step | pending_steps=%d", len(pending))
    trajectory_append: list[dict[str, Any]] = [
        {"step": "edge", "message": "execute_tools -> advance_step", "data": {"pending_count": len(pending)}},
    ]
    while pending:
        pending.pop(0)  # pop the step we just ran (already executed by execute_tools)
        if not pending:
            trajectory_append.append({"step": "advance_step", "message": "no more steps", "data": {}})
            return {
                "pending_steps": [],
                "routing_to": [],
                "agent_final_output": state.get("agent_final_output") or "Done.",
                "internal_trajectory": trajectory_append,
            }
        next_step = pending[0]
        tool_name = (next_step.get("tool_name") or "").strip()
        if not tool_name or tool_name.lower() == "none":
            continue
        if tool_name.startswith("hitl_"):
            continue
        sub_query = (next_step.get("sub_query") or "").strip()
        skill_name = (next_step.get("skill_name") or "").strip()
        if tool_name == "final_response":
            trajectory_append.append({
                "step": "advance_step",
                "message": "next step is final_response",
                "data": {"tool_name": "final_response"},
            })
            return {
                "pending_steps": pending,
                "routing_to": [],
                "agent_final_output": state.get("agent_final_output") or sub_query or "Done.",
                "internal_trajectory": trajectory_append,
            }
        tool_input = build_tool_input_for_step(
            tool_name, sub_query,
            uploaded_files=state.get("uploaded_files") or [],
            base_simulation_file=state.get("base_simulation_file") or None,
        )
        new_routing: list[SkillUsed] = [{"skill_name": skill_name or "final_response", "tool_name": tool_name, "tool_input": tool_input}]
        trajectory_append.append({
            "step": "advance_step",
            "message": f"next step: {tool_name!r} -> check_args",
            "data": {"tool_name": tool_name, "tool_input_keys": list(tool_input.keys())},
        })
        LOG.debug("advance_step -> next step %r", tool_name)
        return {
            "pending_steps": pending,
            "routing_to": new_routing,
            "internal_trajectory": trajectory_append,
        }
    trajectory_append.append({"step": "advance_step", "message": "no more steps", "data": {}})
    return {
        "pending_steps": [],
        "routing_to": [],
        "agent_final_output": state.get("agent_final_output") or "Done.",
        "internal_trajectory": trajectory_append,
    }


def skill_failed_handling(state: GlobalState) -> GlobalState:
    reason = state.get("skill_failure_reason") or "The request could not be fulfilled due to missing or invalid inputs."
    LOG.debug("skill_failed_handling | skill_failure_reason=%r", reason)
    routing = state.get("routing_to") or []
    tool_name = (routing[-1].get("tool_name") or "").strip() if routing else ""
    args_valid = state.get("args_valid")
    trajectory_append: list[dict[str, Any]] = [
        {"step": "edge", "message": f"condition_edges -> skill_failed_handling (args_valid={args_valid})", "data": {"from": "check_args", "to": "skill_failed_handling", "args_valid": args_valid}},
        {"step": "skill_failed_handling", "message": f"skill_failure_reason={reason!r}", "data": {"skill_failure_reason": reason, "tool_name": tool_name}},
    ]

    if "input file" in reason and ".DATA" in reason and ("not found" in reason or "No file" in reason or "not provided" in reason):
        message = (
            "**Cannot run the simulation**\n\n"
            "No valid simulator input file was provided. Please upload a file with extension `.DATA` "
            "(e.g. `SPE10_TOPLAYER.DATA`) so I can run the simulation. "
            "If you already uploaded a file, ensure it is a .DATA file and not another format (e.g. PDF)."
        )
    elif (".DATA" in reason and ".pdf" in reason) or "does not end with .DATA" in reason:
        message = (
            "**Invalid file format**\n\n"
            "The tool requires a simulator primary input file (extension `.DATA`). "
            "You appear to have uploaded a file with a different extension (e.g. `.pdf`). "
            "Please upload a valid `.DATA` file to run the simulation."
        )
    elif "plot_compare" in reason or "compare" in reason.lower() or tool_name == PLOT_COMPARE_TOOL:
        message = (
            "**Cannot compare summary metrics**\n\n"
            "To compare cases you need: (1) an output directory with .SMSPEC files, or upload .SMSPEC/.DATA files with results, "
            "and (2) either specify case_stems/case_paths or upload multiple files (e.g. baseline + *_AGENT_GENERATED.DATA). "
            "Run simulations first, or upload existing .SMSPEC or .DATA files that have .SMSPEC in the same directory."
        )
    else:
        message = f"**Request could not be completed**\n\n{reason}"

    state["agent_final_output"] = message
    trajectory_append[1]["message"] = f"skill_failure_reason={reason!r} -> agent_final_output"
    trajectory_append[1]["data"]["agent_final_output_preview"] = (message or "")[:100]
    state["internal_trajectory"] = trajectory_append
    return state


def execute_tools(state: GlobalState) -> GlobalState:
    routing = state.get("routing_to") or []
    r = routing[-1] if routing else {}
    tool_name = (r.get("tool_name") or "").strip()
    tool_input = r.get("tool_input") or {}
    LOG.debug("execute_tools | tool_name=%r, tool_input=%s", tool_name, tool_input)
    args_valid = state.get("args_valid")
    trajectory_append: list[dict[str, Any]] = [
        {"step": "edge", "message": f"condition_edges -> execute_tools (args_valid={args_valid})", "data": {"from": "check_args", "to": "execute_tools", "args_valid": args_valid}},
    ]

    if _needs_approval(state):
        approved = (state.get("human_approve") or "").strip().lower()
        if approved and "n" in approved:
            state["agent_final_output"] = (
                "Execution declined. You chose not to approve this action. "
                "You can submit a new request when ready."
            )
            trajectory_append.append({
                "step": "execute_tools",
                "message": "human_approve=n, skipped execution",
                "data": {"tool_name": tool_name, "success": False, "human_approve": state.get("human_approve")},
            })
            state["internal_trajectory"] = trajectory_append
            return state

    if not routing:
        state["agent_final_output"] = "No tool was selected to run."
        trajectory_append.append({"step": "execute_tools", "message": "no routing_to", "data": {"tool_name": "", "success": False}})
        state["internal_trajectory"] = trajectory_append
        return state

    if not tool_name:
        state["agent_final_output"] = "No tool was selected to run."
        trajectory_append.append({"step": "execute_tools", "message": "no tool_name", "data": {"tool_name": "", "success": False}})
        state["internal_trajectory"] = trajectory_append
        return state

    if tool_name in ("simulator_manual", "simulator_examples"):
        query = (tool_input.get("query") or "").strip()
        raw = (tool_input.get("collection_name") or tool_name).strip()
        # Resolve simulator_manual -> config collection (docs)
        if raw == "simulator_manual":
            collection_name = get_config().get_manual_collection_name()
        elif raw == "simulator_examples":
            collection_name = "simulator_input_examples"
        else:
            collection_name = raw
        try:
            _rag_skill_root = Path(__file__).resolve().parent.parent / "skills" / "rag_skill"
            _scripts_dir = _rag_skill_root / "scripts"
            if str(_scripts_dir) not in sys.path:
                sys.path.insert(0, str(_scripts_dir))
            from rag_chain import build_chain
            chain = build_chain()
            response = chain.invoke({"query": query, "collection_name": collection_name})
            state["agent_final_output"] = response if isinstance(response, str) else str(response)
            trajectory_append.append({
                "step": "execute_tools",
                "message": f"rag_chain {collection_name!r} success",
                "data": {"tool_name": tool_name, "tool_input": tool_input, "success": True, "agent_final_output_preview": (state["agent_final_output"] or "")[:100]},
            })
            state["internal_trajectory"] = trajectory_append
            return state
        except ImportError as e:
            state["agent_final_output"] = (
                f"**RAG lookup unavailable**\n\n"
                f"The knowledge-base tools (simulator_manual / simulator_examples) could not be loaded: {e}. "
                f"Ensure dependencies and Milvus are configured."
            )
            trajectory_append.append({"step": "execute_tools", "message": f"rag_chain import error: {e!r}", "data": {"tool_name": tool_name, "success": False, "error": str(e)}})
            state["internal_trajectory"] = trajectory_append
            return state
        except RuntimeError as e:
            if "NVIDIA_API_KEY" in str(e):
                state["agent_final_output"] = (
                    "**RAG lookup requires API key**\n\n"
                    "NVIDIA_API_KEY must be set to use the simulator manual and examples search."
                )
            else:
                state["agent_final_output"] = f"**RAG lookup failed**\n\n{e}"
            trajectory_append.append({"step": "execute_tools", "message": f"rag_chain RuntimeError: {e!r}", "data": {"tool_name": tool_name, "success": False, "error": str(e)}})
            state["internal_trajectory"] = trajectory_append
            return state
        except Exception as e:
            state["agent_final_output"] = (
                f"**RAG lookup failed**\n\nError while running `{tool_name}`: {e!s}\n\n"
                f"Please check that Milvus and the knowledge base are available and try again."
            )
            trajectory_append.append({"step": "execute_tools", "message": f"rag_chain exception: {e!r}", "data": {"tool_name": tool_name, "success": False, "error": str(e)}})
            state["internal_trajectory"] = trajectory_append
            return state

    tool = get_tool(tool_name)
    if not tool:
        state["agent_final_output"] = f"Unknown tool: {tool_name}. Please try again with a supported action."
        trajectory_append.append({"step": "execute_tools", "message": f"unknown tool {tool_name!r}", "data": {"tool_name": tool_name, "success": False}})
        state["internal_trajectory"] = trajectory_append
        return state

    try:
        result = run_tool(tool_name, tool_input)
        state["agent_final_output"] = result if isinstance(result, str) else str(result)
        out_str = (state["agent_final_output"] or "").strip()
        if tool_name == "run_flow_diagnostics" and out_str and not out_str.lower().startswith("error"):
            user_query = (state.get("user_input") or state.get("input") or "").strip()
            interpretation = _interpret_flow_diagnostics_llm(user_query, out_str)
            # Append key metrics summary so user sees arrival times, connectivity, etc.
            key_metrics = ""
            if "--- Key metrics summary ---" in out_str:
                parts = out_str.split("--- Key metrics summary ---", 1)
                if len(parts) > 1:
                    key_metrics = "\n\n--- Key metrics ---\n" + parts[1].strip()
            state["agent_final_output"] = interpretation + key_metrics
            out_str = (state["agent_final_output"] or "").strip()
        if tool_name in ("modify_simulation_input_file", "patch_simulation_input_keyword") and out_str.lower().startswith("error"):
            state["skill_failure_reason"] = state["agent_final_output"]
            trajectory_append.append({
                "step": "execute_tools",
                "message": f"tool_name={tool_name!r} returned error",
                "data": {"tool_name": tool_name, "tool_input": tool_input, "success": False, "agent_final_output_preview": out_str[:100]},
            })
            state["internal_trajectory"] = trajectory_append
            return state
        if tool_name == "run_and_heal":
            data_file = (tool_input.get("data_file") or "").strip()
            state["output_dir"] = (tool_input.get("output_dir") or "").strip() or (str(Path(data_file).parent) if data_file else ".")
            try:
                parsed = json.loads(state["agent_final_output"])
                fixed_path = (parsed.get("fixed_file_path") or "").strip() if isinstance(parsed, dict) else ""
                if fixed_path:
                    state["pending_confirm_relaunch"] = True
                    state["fixed_data_file_path"] = fixed_path
                    state["output_dir"] = str(Path(fixed_path).parent) + os.sep
                    state["agent_final_output"] = (
                        f"**Run-and-heal completed**\n\n"
                        f"A fixed simulator input file was created: `{fixed_path}`\n\n"
                        f"Do you want to **relaunch the simulation** with this fixed file? "
                        f"Reply **yes** or **run** to confirm."
                    )
            except Exception:
                pass
        out_preview = (state["agent_final_output"] or "")[:100]
        trajectory_append.append({
            "step": "execute_tools",
            "message": f"tool_name={tool_name!r} success",
            "data": {"tool_name": tool_name, "tool_input": tool_input, "success": True, "agent_final_output_preview": out_preview},
        })
        state["internal_trajectory"] = trajectory_append
    except Exception as e:
        state["agent_final_output"] = (
            f"**Tool execution failed**\n\n"
            f"Error while running `{tool_name}`: {e!s}\n\n"
            f"Please check your inputs (e.g. file paths, output directory) and try again."
        )
        trajectory_append.append({
            "step": "execute_tools",
            "message": f"tool_name={tool_name!r} exception: {e!r}",
            "data": {"tool_name": tool_name, "tool_input": tool_input, "success": False, "error": str(e)},
        })
        state["internal_trajectory"] = trajectory_append
    return state


def final_response(state: GlobalState) -> GlobalState:
    out = (state.get("agent_final_output") or "")
    out_preview = out[:100]
    LOG.debug("final_response | agent_final_output preview=%r...", out_preview)
    trajectory_append: list[dict[str, Any]] = [
        {"step": "edge", "message": "-> final_response", "data": {"to": "final_response"}},
        {"step": "final_response", "message": f"agent_final_output preview: {out_preview!r}", "data": {"agent_final_output_preview": out_preview}},
    ]
    state["internal_trajectory"] = trajectory_append

    history: list[BaseMessage] = list(state.get("chat_history") or [])
    history.append(AIMessage(content=out))
    state["chat_history"] = trim_chat_history(history)
    return state
