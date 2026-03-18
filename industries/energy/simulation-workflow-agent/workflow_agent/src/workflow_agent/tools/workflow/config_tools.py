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
Workflow-specific configuration helpers.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def create_experiment_config(
    base_config: Dict[str, Any],
    strategy: Dict[str, Any],
    quick: bool,
    iteration: Optional[int],
    variant: Optional[int],
    experiment_name: str,
    quick_generations_ratio: float,
) -> Dict[str, Any]:
    config = json.loads(json.dumps(base_config))
    algo = config.get("algorithm", {})
    strategy_algo = strategy.get("algorithm", {})
    if strategy_algo:
        algo.update(strategy_algo)
    if quick:
        if "n_generations" in algo:
            algo["n_generations"] = max(1, int(algo["n_generations"] * quick_generations_ratio))
    config["algorithm"] = algo
    apply_case_name(config, iteration, variant, experiment_name)
    return config


def apply_case_name(
    config: Dict[str, Any],
    iteration: Optional[int],
    variant: Optional[int],
    experiment_name: str,
) -> None:
    paths = config.setdefault("paths", {})
    base_case = paths.get("case_name")
    suffix_parts = [experiment_name]
    if iteration is not None:
        suffix_parts.append(f"iter{iteration:02d}")
    if variant is not None:
        suffix_parts.append(f"var{variant:02d}")
    suffix = "_".join(suffix_parts)
    paths["case_name"] = f"{base_case}_{suffix}"
