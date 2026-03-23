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
Skills package for simulator_agent.

This package contains all skill modules:
- simulation_skill: Run, monitor, and control OPM Flow simulations
- results_skill: Read and analyze OPM Flow simulation results
- rag_skill: Retrieve information from OPM Flow manual and examples
- plot_skill: Plot and compare summary metrics from simulation results
- input_file_skill: Parse, modify, validate, and patch OPM Flow DATA files
"""

__all__ = [
    "simulation_skill",
    "results_skill",
    "rag_skill",
    "plot_skill",
    "input_file_skill",
]

