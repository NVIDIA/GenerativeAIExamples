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
Agentic reservoir workflow (LangGraph-based, workflow-agnostic).

Runs multi-agent workflow using LangGraph. The actual workflow (optimization,
history matching, etc.) runs as a separate subprocess via WorkflowExecutor.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel

from .utils import (
    WorkflowPaths,
    configure_logging,
    load_yaml,
    resolve_paths,
)
from .tools import ExperimentTracker
from .workflow_graph import WorkflowState, build_workflow_graph

LOG_NAME = "workflow_agent.agentic"
DEFAULT_WORKFLOW_CONFIG = "conf/config.yaml"

console = Console()


class AgenticWorkflow:
    """
    LangGraph-based multi-agent workflow. Workflow-agnostic: the actual
    workflow (e.g. optimization) runs as a separate subprocess.
    """

    def __init__(
        self,
        workflow_config: str = DEFAULT_WORKFLOW_CONFIG,
        execution_mode: str = "serial",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
    ) -> None:
        configure_logging(log_level, log_file)
        self.paths = resolve_paths(base_config=None, workflow_config=workflow_config)
        self.config = load_yaml(self.paths.workflow_config)
        # If max_parallel_experiments > 1, use parallel mode
        max_par = self.config.get("execution", {}).get("max_parallel_experiments", 1)
        self.execution_mode = "parallel" if max_par > 1 else execution_mode
        self.graph = build_workflow_graph()

    def run_complete_workflow(
        self, base_config_path: Optional[str], max_iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        paths = resolve_paths(
            base_config=base_config_path,
            workflow_config=str(self.paths.workflow_config),
        )
        base_config = load_yaml(paths.base_config)

        output_cfg = self.config.get("output", {})
        experiments_dir = Path(output_cfg.get("experiments_dir", "./experiments"))
        tracker = ExperimentTracker(experiments_dir)
        experiment = tracker.create("experiment")

        iteration_limit = max_iterations or int(
            self.config.get("evolution", {}).get("max_iterations", 3)
        )

        initial_state: WorkflowState = {
            "base_config": base_config,
            "base_config_path": str(paths.base_config),
            "workflow_config": self.config,
            "max_iterations": iteration_limit,
            "execution_mode": self.execution_mode,
            "experiment_name": experiment.name,
            "experiment_dir": str(experiment.path),
            "all_solutions": [],
            "best_solution": None,
            "total_simulations": 0,
            "phase": "initial",
        }

        console.print(
            Panel.fit(
                f"[bold green]Agentic Workflow (LangGraph)[/bold green]\n"
                f"Experiment: {experiment.name}\n"
                f"Mode: {self.execution_mode.upper()}",
                title="🤖 Starting",
            )
        )

        final_state = self.graph.invoke(initial_state)

        report = final_state.get("report", {})
        if not report:
            report = {
                "experiment_dir": str(experiment.path),
                "error": final_state.get("error", "No report generated"),
            }

        return {"experiment_dir": str(experiment.path), "report": report}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Agentic Reservoir Workflow (LangGraph)")
    parser.add_argument("config", nargs="?", default=None, help="Base workflow configuration file")
    parser.add_argument("--iterations", type=int, default=None, help="Maximum iterations")
    parser.add_argument("--mode", choices=["serial", "parallel"], default="serial")
    parser.add_argument("--workflow-config", default=DEFAULT_WORKFLOW_CONFIG)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--log-file", default=None)
    parser.add_argument("--print-config", action="store_true")
    args = parser.parse_args(argv)

    try:
        paths = resolve_paths(base_config=args.config, workflow_config=args.workflow_config)
        if args.print_config:
            config = load_yaml(paths.workflow_config)
            console.print(Panel.fit("Loaded workflow configuration", title="Config"))
            console.print(config)
            return 0
        runner = AgenticWorkflow(
            workflow_config=str(paths.workflow_config),
            execution_mode=args.mode,
            log_level=args.log_level,
            log_file=args.log_file,
        )
        result = runner.run_complete_workflow(
            base_config_path=str(paths.base_config), max_iterations=args.iterations
        )
        console.print(
            Panel.fit(
                "[bold green]✓ Workflow completed successfully[/bold green]\n"
                f"Results saved to: {result['experiment_dir']}",
                title="✅ Done",
            )
        )
        return 0
    except KeyboardInterrupt:
        console.print("[yellow]Workflow interrupted by user[/yellow]")
        return 1
    except Exception as exc:
        logging.getLogger(LOG_NAME).exception("Workflow failed")
        console.print(f"[red]Error: {exc}[/red]")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
