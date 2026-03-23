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
Shared persistence helpers for workflows.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ExperimentRecord:
    name: str
    path: Path
    created_at: str


class ExperimentTracker:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create(self, prefix: str) -> ExperimentRecord:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{prefix}_{timestamp}"
        path = self.base_dir / name
        path.mkdir(parents=True, exist_ok=True)
        return ExperimentRecord(name=name, path=path, created_at=timestamp)


class SolutionArchiver:
    def __init__(self, archive_dir: Path) -> None:
        self.archive_dir = archive_dir
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.archive_dir / "archive_index.json"
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        if self.index_path.exists():
            with self.index_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return {"solutions": [], "metadata": {"created": datetime.now().isoformat(), "last_updated": None}}

    def _save_index(self) -> None:
        self._index["metadata"]["last_updated"] = datetime.now().isoformat()
        with self.index_path.open("w", encoding="utf-8") as handle:
            json.dump(self._index, handle, indent=2)

    def archive(
        self,
        solution_name: str,
        strategy: Dict[str, Any],
        result: Dict[str, Any],
        source_dir: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{solution_name}_{timestamp}"
        solution_dir = self.archive_dir / archive_name
        solution_dir.mkdir(exist_ok=True)

        with (solution_dir / "strategy.json").open("w", encoding="utf-8") as handle:
            json.dump(strategy, handle, indent=2)
        with (solution_dir / "result.json").open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)

        if source_dir and source_dir.exists():
            config_file = source_dir / "config.yaml"
            if config_file.exists():
                shutil.copy(config_file, solution_dir / "config.yaml")
            results_file = source_dir / "optimization_results.json"
            if results_file.exists():
                shutil.copy(results_file, solution_dir / "optimization_results.json")
            csv_files = list(source_dir.glob("*_evaluations.csv"))
            if csv_files:
                shutil.copy(csv_files[0], solution_dir / "evaluations.csv")
            plots_dir = source_dir / "plots"
            if plots_dir.exists():
                shutil.copytree(plots_dir, solution_dir / "plots", dirs_exist_ok=True)

        solution_metadata = {
            "solution_name": solution_name,
            "archive_name": archive_name,
            "archive_path": str(solution_dir),
            "best_objective": result.get("best_objective"),
            "timestamp": timestamp,
            "source_dir": str(source_dir) if source_dir else None,
            **(metadata or {}),
        }
        with (solution_dir / "metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(solution_metadata, handle, indent=2)

        self._index["solutions"].append(solution_metadata)
        self._save_index()
        return solution_dir
