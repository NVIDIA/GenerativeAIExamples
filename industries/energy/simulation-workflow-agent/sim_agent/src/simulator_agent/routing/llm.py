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
LLM-based query classification (wraps query_decomposition).
"""

from __future__ import annotations

from typing import Any

from ..state import GlobalState
from ..utils import build_tool_input_for_step, chat_history_to_conversation, trim_chat_history
from .rule_based import classify_query_rule_based


def classify_query_llm(query: str, state: GlobalState) -> dict[str, Any]:
    try:
        from ..query_decomposition import query_decomposition_call
    except Exception:
        return classify_query_rule_based(query)

    trimmed_history = trim_chat_history(state.get("chat_history") or [])
    conversation = chat_history_to_conversation(trimmed_history)
    uploaded = state.get("uploaded_files") or []
    try:
        result = query_decomposition_call(
            user_input=query,
            conversation_history=conversation,
            last_tool_name=None,
            pending_confirm_run=False,
            pending_auto_fix=False,
            confirm_before_run=False,
            confirm_before_modify=False,
            uploaded_files=uploaded,
        )
    except Exception:
        return classify_query_rule_based(query)

    if not result or not isinstance(result, list):
        return classify_query_rule_based(query)

    decomp = result[0] if result else {}
    steps = decomp.get("output_steps") or []

    for i, step in enumerate(steps):
        tool_name = (step.get("tool_name") or "").strip()
        if not tool_name or tool_name.lower() == "none":
            continue
        if tool_name == "final_response":
            return {
                "skill": "final_response",
                "tool": None,
                "tool_input": {},
                "agent_final_output": (step.get("sub_query") or "").strip() or "I'll respond to your request.",
            }
        if tool_name.startswith("hitl_"):
            continue
        skill_name = (step.get("skill_name") or "").strip()
        sub_query = (step.get("sub_query") or "").strip()
        tool_input = build_tool_input_for_step(
            tool_name, sub_query,
            uploaded_files=state.get("uploaded_files") or [],
            base_simulation_file=state.get("base_simulation_file") or None,
        )
        out: dict[str, Any] = {"skill": skill_name or "final_response", "tool": tool_name, "tool_input": tool_input}
        if i + 1 < len(steps):
            out["pending_steps"] = steps[i + 1:]
        return out

    if steps:
        first = steps[0]
        return {
            "skill": "final_response",
            "tool": None,
            "tool_input": {},
            "agent_final_output": (first.get("sub_query") or "").strip() or "I'll respond to your request.",
        }
    return classify_query_rule_based(query)
