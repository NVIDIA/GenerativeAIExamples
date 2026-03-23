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
LangGraph edge / routing functions.
"""

from __future__ import annotations

import logging

from ..state import GlobalState

LOG = logging.getLogger(__name__)


def _needs_approval(state: GlobalState) -> bool:
    routing = state.get("routing_to") or []
    if not routing:
        return False
    r = routing[-1]
    skill = (r.get("skill_name") or "").strip()
    tool = (r.get("tool_name") or "").strip()
    data_file = ((r.get("tool_input") or {}).get("data_file") or "").strip()
    if skill == "simulation_skill" and tool == "run_and_heal":
        return True
    if skill == "plot_skill":
        return True
    if tool == "run_and_heal" and data_file and "_FIXED" in data_file.upper():
        return True
    if skill == "results_skill" and tool == "run_flow_diagnostics":
        return True
    return False


def route_after_query(state: GlobalState) -> str:
    routing = state.get("routing_to") or []
    if not routing:
        LOG.debug("route_after_query -> final_response (no routing_to)")
        return "final_response"
    r = routing[-1]
    next_node = "check_args" if (r.get("tool_name") or "").strip() else "final_response"
    LOG.debug("route_after_query -> %s (tool_name=%r)", next_node, r.get("tool_name"))
    return next_node


def condition_edges_has_valid_args(state: GlobalState) -> str:
    args_valid = state.get("args_valid")
    if not args_valid:
        next_node = "skill_failed_handling"
        LOG.debug("condition_edges_has_valid_args -> %s (args_valid=%s)", next_node, args_valid)
        return next_node
    if _needs_approval(state):
        next_node = "approval_needed"
        LOG.debug("condition_edges_has_valid_args -> %s (approval required)", next_node)
        return next_node
    next_node = "execute_tools"
    LOG.debug("condition_edges_has_valid_args -> %s (args_valid=%s)", next_node, args_valid)
    return next_node


def route_after_execute_tools(state: GlobalState) -> str:
    if state.get("skill_failure_reason"):
        next_node = "skill_failed_handling"
        LOG.debug("route_after_execute_tools -> %s (tool returned error)", next_node)
        return next_node
    pending = state.get("pending_steps") or []
    next_node = "advance_step" if pending else "final_response"
    LOG.debug("route_after_execute_tools -> %s (pending_steps=%d)", next_node, len(pending))
    return next_node


def route_after_advance_step(state: GlobalState) -> str:
    routing = state.get("routing_to") or []
    next_node = "check_args" if routing and (routing[-1].get("tool_name") or "").strip() else "final_response"
    LOG.debug("route_after_advance_step -> %s", next_node)
    return next_node
