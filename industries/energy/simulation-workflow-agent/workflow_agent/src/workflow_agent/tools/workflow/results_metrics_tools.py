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
Workflow-specific result parsing and metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from scipy.spatial.distance import pdist  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    pdist = None

from ...utils import load_yaml


def extract_convergence_with_populations(
    results_json: Path,
    evaluations_csv: Optional[Path],
) -> Tuple[List[Dict[str, Any]], Optional[np.ndarray], Optional[np.ndarray]]:
    with results_json.open("r", encoding="utf-8") as handle:
        results = json.load(handle)
    convergence_history = results.get("convergence_history", [])

    population_gen0 = None
    population_final = None
    if evaluations_csv and evaluations_csv.exists():
        try:
            import pandas as pd  # type: ignore[import-not-found]
        except ImportError:  # pragma: no cover - optional dependency
            return convergence_history, None, None

        df = pd.read_csv(evaluations_csv)
        if "generation" in df.columns:
            population_gen0 = _extract_population(df, generation=0)
            if convergence_history:
                final_gen = convergence_history[-1].get("generation", 0)
                population_final = _extract_population(df, generation=final_gen)

    return convergence_history, population_gen0, population_final


def _extract_population(df, generation: int) -> Optional[np.ndarray]:
    if "generation" not in df.columns:
        return None
    gen_data = df[df["generation"] == generation]
    if gen_data.empty:
        return None
    exclude = {"generation", "individual", "case_name", "success", "objective"}
    variable_cols = [col for col in gen_data.columns if col not in exclude]
    if not variable_cols:
        return None
    return gen_data[variable_cols].values


def calculate_genotypic_diversity(population: np.ndarray) -> float:
    if len(population) < 2:
        return 0.0
    mins = np.min(population, axis=0)
    maxs = np.max(population, axis=0)
    ranges = maxs - mins
    ranges[ranges == 0] = 1.0
    normalized = (population - mins) / ranges
    if pdist is None:
        return 0.0
    distances = pdist(normalized, metric="euclidean")
    max_distance = np.sqrt(len(population[0]))
    return float(np.mean(distances) / max_distance)


def analyze_convergence_pattern(convergence_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(convergence_history) < 2:
        return {
            "pattern": "insufficient_data",
            "avg_improvement_pct": 0.0,
            "improvements": [],
            "trend": "unknown",
            "description": "Need at least 2 generations to analyze pattern",
        }

    best_values = [gen["best"] for gen in convergence_history if "best" in gen]
    improvements = np.diff(best_values)
    relative_improvements = improvements / np.abs(best_values[:-1])
    relative_improvements_pct = relative_improvements * 100
    avg_improvement_pct = float(np.mean(relative_improvements_pct))

    if len(improvements) < 2:
        return {
            "pattern": "insufficient_data",
            "avg_improvement_pct": avg_improvement_pct,
            "improvements": [float(x) for x in relative_improvements_pct],
            "trend": "unknown",
            "description": f"Improved {avg_improvement_pct:+.1f}% on average",
        }

    improvement_changes = np.diff(improvements)
    if np.all(improvement_changes <= 0):
        pattern = "plateau"
    elif np.all(improvement_changes >= 0):
        pattern = "accelerating"
    else:
        pattern = "steady"

    trend = "healthy" if avg_improvement_pct >= 2.0 else "concerning"
    description = f"{pattern.title()} with {avg_improvement_pct:+.1f}%/gen avg improvement."
    return {
        "pattern": pattern,
        "avg_improvement_pct": avg_improvement_pct,
        "improvements": [float(x) for x in relative_improvements_pct],
        "trend": trend,
        "description": description,
    }


def find_evaluations_csv(results_dir: Path) -> Optional[Path]:
    return next(results_dir.glob("*_evaluations.csv"), None)


def find_results_file(results_dir: Path, results_file_name: Optional[str]) -> Optional[Path]:
    if not results_file_name:
        return None
    candidate = results_dir / results_file_name
    return candidate if candidate.exists() else None


def resolve_results_file(
    output_dir: Path,
    config_path: Path,
    workflow_config: Dict[str, Any],
) -> Optional[Path]:
    results_file_name = workflow_config.get("results_file")

    try:
        config = load_yaml(config_path)
        paths = config.get("paths", {})
        sim_dir_base = paths.get("sim_dir_base")
        case_name = paths.get("case_name")
        if not sim_dir_base or not case_name:
            return None

        if not results_file_name:
            results_file_name = f"{case_name}_results.json"
            results_file = find_results_file(output_dir, results_file_name)
            if results_file:
                return results_file

        sim_base = Path(sim_dir_base)
        if not sim_base.is_absolute():
            # When run_cwd is set (e.g. ./workflow), optimization writes to run_cwd/dataset/...
            run_cwd = workflow_config.get("run_cwd")
            base = Path(run_cwd).resolve() if run_cwd else config_path.parent
            sim_base = base / sim_base

        candidates = sorted(
            sim_base.glob(f"{case_name}*.sim"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for candidate in candidates[:5]:
            results = find_results_file(candidate, results_file_name)
            if results:
                return results
    except Exception:
        return None

    return None


def extract_results_summary(results_path: Path) -> Dict[str, Any]:
    with results_path.open("r", encoding="utf-8") as handle:
        results = json.load(handle)

    best_solution = results.get("best_solution")
    best_objective = None
    if isinstance(best_solution, dict):
        best_objective = best_solution.get("objective")
    if best_objective is None:
        best_objective = results.get("best_objective")
    if best_objective is None and results.get("statistics"):
        best_objective = results["statistics"].get("best_objective")

    total_evaluations = (
        results.get("optimization_summary", {}).get("total_evaluations")
        or results.get("evaluations", {}).get("total_evaluations")
    )

    return {
        "best_objective": best_objective,
        "best_solution": best_solution,
        "total_evaluations": total_evaluations,
        "convergence_history": results.get("convergence_history", []),
        "run_info": results.get("run_info", {}),
    }
