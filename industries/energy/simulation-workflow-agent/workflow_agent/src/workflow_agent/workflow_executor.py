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
Workflow-agnostic executor: runs a workflow (optimization, history matching, etc.)
as a separate subprocess. Pluggable by workflow type.
"""

from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import load_yaml


@dataclass
class ExecutionResult:
    """Result of running a workflow subprocess."""

    success: bool
    best_objective: Optional[float] = None
    best_solution: Optional[Dict[str, Any]] = None
    total_evaluations: Optional[int] = None
    convergence_history: List[Dict[str, Any]] = None
    run_info: Dict[str, Any] = None
    results_file: Optional[str] = None
    csv_file: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.convergence_history is None:
            self.convergence_history = []
        if self.run_info is None:
            self.run_info = {}


class WorkflowExecutor(ABC):
    """Abstract base for workflow execution. Subclasses implement run() for specific workflow types."""

    @abstractmethod
    def run(
        self,
        config_path: Path,
        output_dir: Path,
        timeout: int,
        workflow_config: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute the workflow. Returns ExecutionResult with success and parsed outputs."""
        pass


class SubprocessWorkflowExecutor(WorkflowExecutor):
    """
    Runs a workflow via subprocess using a configurable run_command template.
    Workflow-agnostic: the command (e.g. optimization, history matching) is defined in config.
    """

    def __init__(self, run_command_template: str) -> None:
        if not run_command_template or "{config_path}" not in run_command_template:
            raise ValueError(
                "run_command must contain {config_path} placeholder, e.g. "
                "'python run_optimization.py {config_path}'"
            )
        self.run_command_template = run_command_template

    def run(
        self,
        config_path: Path,
        output_dir: Path,
        timeout: int,
        workflow_config: Dict[str, Any],
        execution_config: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        cmd = self._build_command(config_path, output_dir)
        env = dict(os.environ)
        env["PYTHONUNBUFFERED"] = "1"

        # Use workflow_config.run_cwd if set (e.g. workflow_agent root); else output_dir
        cwd = workflow_config.get("run_cwd")
        run_cwd = str(Path(cwd).resolve()) if cwd else str(output_dir)

        exec_cfg = execution_config or {}
        stream_output = exec_cfg.get("stream_workflow_output", True)

        try:
            if stream_output:
                # Stream subprocess stdout/stderr to terminal so user sees optimization progress
                result = subprocess.run(
                    cmd,
                    cwd=run_cwd,
                    stdout=None,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    env=env,
                )
            else:
                result = subprocess.run(
                    cmd,
                    cwd=run_cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                )

            if result.returncode != 0:
                err_msg = (
                    f"Exit code {result.returncode}"
                    if stream_output
                    else (result.stderr or result.stdout or f"Exit code {result.returncode}")
                )
                return ExecutionResult(success=False, error=err_msg)
        except subprocess.TimeoutExpired:
            return ExecutionResult(success=False, error="Workflow timed out")

        return self._parse_results(output_dir, config_path, workflow_config)

    def _build_command(self, config_path: Path, output_dir: Path) -> List[str]:
        # Use absolute paths so they work regardless of run_cwd
        abs_config = Path(config_path).resolve()
        formatted = self.run_command_template.format(
            config_path=str(abs_config),
            output_dir=str(output_dir),
        )
        return formatted.split()

    def _parse_results(
        self,
        output_dir: Path,
        config_path: Path,
        workflow_config: Dict[str, Any],
    ) -> ExecutionResult:
        """Parse workflow outputs. Override in subclasses for custom result formats."""
        from .tools.workflow import resolve_results_file, extract_results_summary, find_evaluations_csv

        results_file = resolve_results_file(output_dir, config_path, workflow_config)
        if not results_file or not results_file.exists():
            return ExecutionResult(success=False, error="No results file generated")

        summary = extract_results_summary(results_file)
        csv_file = find_evaluations_csv(results_file.parent)

        return ExecutionResult(
            success=True,
            best_objective=summary.get("best_objective"),
            best_solution=summary.get("best_solution"),
            total_evaluations=summary.get("total_evaluations"),
            convergence_history=summary.get("convergence_history", []),
            run_info=summary.get("run_info", {}),
            results_file=str(results_file),
            csv_file=str(csv_file) if csv_file else None,
        )
