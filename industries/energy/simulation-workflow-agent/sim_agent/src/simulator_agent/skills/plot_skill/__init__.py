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
OPM Plotting Skill for OPM Flow

This skill provides tools for visualizing and comparing OPM Flow simulation results.
Follows the Agent Skills specification: https://agentskills.io/specification

Structure:
- SKILL.md: Skill metadata and instructions
- test.py: Test suite
- scripts/: Tool implementations (simulation_tools.py for plot tools)
- references/: Additional documentation
- assets/: Static resources

Based on TOOL_DECISION_TREE.md Section 3.1 (Plot or compare results).

Tools:
- plot_summary_metric: Plot one or more summary metrics from simulation outputs
- plot_compare_summary_metric: Compare multiple cases on the same plot
"""

from .scripts.simulation_tools import (
    plot_summary_metric,
    plot_compare_summary_metric,
)

__all__ = [
    "plot_summary_metric",
    "plot_compare_summary_metric",
]
