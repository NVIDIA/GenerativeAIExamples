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
Build and compile the LangGraph simulator workflow.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..state import GlobalState
from .nodes import (
    query_routing,
    check_args,
    approval_needed,
    advance_step,
    skill_failed_handling,
    execute_tools,
    final_response,
)
from .edges import (
    route_after_query,
    condition_edges_has_valid_args,
    route_after_execute_tools,
    route_after_advance_step,
)


def build_simulator_graph():
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(GlobalState)

    workflow.add_node("query_routing", query_routing)
    workflow.add_node("check_args", check_args)
    workflow.add_node("approval_needed", approval_needed)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("advance_step", advance_step)
    workflow.add_node("skill_failed_handling", skill_failed_handling)
    workflow.add_node("final_response", final_response)

    workflow.set_entry_point("query_routing")

    workflow.add_conditional_edges("query_routing", route_after_query, {"check_args": "check_args", "final_response": "final_response"})
    workflow.add_conditional_edges(
        "check_args",
        condition_edges_has_valid_args,
        {"approval_needed": "approval_needed", "execute_tools": "execute_tools", "skill_failed_handling": "skill_failed_handling"},
    )
    workflow.add_edge("approval_needed", "execute_tools")
    workflow.add_conditional_edges(
        "execute_tools",
        route_after_execute_tools,
        {"advance_step": "advance_step", "final_response": "final_response", "skill_failed_handling": "skill_failed_handling"},
    )
    workflow.add_conditional_edges(
        "advance_step",
        route_after_advance_step,
        {"check_args": "check_args", "final_response": "final_response"},
    )
    workflow.add_edge("skill_failed_handling", "final_response")
    workflow.add_edge("final_response", END)

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["approval_needed"])


app = build_simulator_graph()
