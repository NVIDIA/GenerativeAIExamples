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
LangGraph-based multi-agent workflow. Workflow-agnostic: the actual workflow
(optimization, history matching, etc.) runs as a separate subprocess via WorkflowExecutor.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from rich.console import Console

from .agents import (
    CriticAgent,
    KnowledgeRetrieverAgent,
    ReservoirAnalystAgent,
    ResultAnalystAgent,
    StrategyProposerAgent,
)
from .tools.workflow import (
    analyze_convergence_pattern,
    create_experiment_config,
    extract_convergence_with_populations,
)
from .utils import dump_yaml, ensure_serializable
from .workflow_executor import ExecutionResult, SubprocessWorkflowExecutor, WorkflowExecutor

LOG = logging.getLogger("workflow_agent.graph")
_console = Console()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class WorkflowState(TypedDict, total=False):
    """State passed through the LangGraph workflow."""

    # Input
    base_config: Dict[str, Any]
    base_config_path: str
    workflow_config: Dict[str, Any]
    workflow_paths: Dict[str, Any]  # serializable WorkflowPaths
    max_iterations: int
    execution_mode: str

    # Phase 1
    analysis: Dict[str, Any]
    knowledge: Dict[str, Any]
    strategy: Dict[str, Any]
    critique: Dict[str, Any]

    # Iteration loop
    current_iteration: int
    current_variant: int
    current_strategy: Dict[str, Any]
    iteration_dir: str
    execution_result: Dict[str, Any]

    # Accumulated
    all_solutions: List[Dict[str, Any]]
    best_solution: Optional[Dict[str, Any]]
    total_simulations: int
    experiment_name: str
    experiment_dir: str

    # Control
    should_continue: bool
    phase: str  # "initial" | "iterate" | "final" | "done"

    # Output
    report: Dict[str, Any]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def _get_executor(workflow_config: Dict[str, Any]) -> WorkflowExecutor:
    """Build workflow executor from config. Workflow-agnostic: uses run_command."""
    run_cmd = workflow_config.get("run_command")
    if not run_cmd:
        raise ValueError("workflow.run_command required in config")
    return SubprocessWorkflowExecutor(run_cmd)


def initial_analysis(state: WorkflowState) -> Dict[str, Any]:
    """Phase 1: reservoir analysis, knowledge retrieval, strategy proposal, critique."""
    _console.print("[bold cyan]Phase 1:[/bold cyan] Analysis & debate (reservoir analyst, strategy proposer, critic)...")
    base_config = state["base_config"]
    workflow_config = state["workflow_config"]
    team = _get_team(workflow_config)
    constraints = workflow_config.get("constraints", {})

    analyst = team.get("ReservoirAnalyst")
    strategy_agent = team.get("StrategyProposer")
    critic_agent = team.get("Critic")

    characteristics = ReservoirAnalystAgent.extract_characteristics(base_config)
    analysis_resp = analyst.execute({"characteristics": characteristics, "base_config": base_config})
    knowledge_resp = team.get("KnowledgeRetriever").execute({"analysis": analysis_resp.data})
    strategy_resp = strategy_agent.execute(
        {
            "analysis": analysis_resp.data,
            "knowledge": knowledge_resp.data.get("results", []),
            "base_config": base_config,
            "mode": "initial",
        }
    )
    critique_resp = critic_agent.execute(
        {"strategy": strategy_resp.data, "analysis": analysis_resp.data, "constraints": constraints}
    )

    return {
        "analysis": analysis_resp.data,
        "knowledge": knowledge_resp.data,
        "strategy": strategy_resp.data,
        "critique": critique_resp.data,
        "phase": "initial",
    }


def evolve_strategy(state: WorkflowState) -> Dict[str, Any]:
    """Evolve strategy for current iteration/variant; set iteration_dir for run_workflow."""
    best = state.get("best_solution") or {}
    base_strategy = best.get("strategy") or state.get("strategy") or {}
    prev_iteration = state.get("current_iteration")
    iteration = (prev_iteration if isinstance(prev_iteration, int) else 0) + 1
    variant = state.get("current_variant", 0)
    if not isinstance(variant, int):
        variant = 0
    phase = state.get("phase", "iterate")
    if phase == "final":
        _console.print("[bold cyan]Preparing final run[/bold cyan]...")
    else:
        _console.print(f"[bold cyan]Iteration {iteration}:[/bold cyan] Evolving strategy...")
    execution_mode = state.get("execution_mode", "serial")
    workflow_config = state["workflow_config"]
    team = _get_team(workflow_config)

    strategy_agent = team.get("StrategyProposer")
    response = strategy_agent.execute(
        {
            "base_strategy": base_strategy,
            "iteration": iteration,
            "variant": variant,
            "mode": "evolve_diverse" if execution_mode == "parallel" else "evolve",
        }
    )

    experiment_dir = Path(state["experiment_dir"])
    iteration_dir = experiment_dir / f"iter_{iteration:02d}_var_{variant:02d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)

    return {
        "current_strategy": response.data or base_strategy,
        "current_iteration": iteration,
        "current_variant": variant,
        "iteration_dir": str(iteration_dir),
        "phase": "iterate",
    }


def run_workflow(state: WorkflowState) -> Dict[str, Any]:
    """
    Run the workflow as a subprocess (optimization, history matching, etc.).
    Workflow-agnostic: executor is built from workflow.run_command.
    """
    base_config = state["base_config"]
    current_strategy = state["current_strategy"]
    iteration = state.get("current_iteration", 1)
    variant = state.get("current_variant", 0)
    iteration_dir = Path(state["iteration_dir"])
    experiment_name = state["experiment_name"]
    workflow_config = state["workflow_config"]
    base_workflow = workflow_config.get("workflow", {})
    execution_cfg = workflow_config.get("execution", {})
    evolution_cfg = workflow_config.get("evolution", {})

    is_final = state.get("phase") == "final"
    timeout = (
        execution_cfg.get("full_experiment_timeout", 14400)
        if is_final
        else execution_cfg.get("quick_experiment_timeout", 3600)
    )

    config = create_experiment_config(
        base_config=base_config,
        strategy=current_strategy,
        quick=not is_final,
        iteration=None if is_final else iteration,
        variant=None if is_final else variant,
        experiment_name=experiment_name,
        quick_generations_ratio=float(evolution_cfg.get("quick_generations_ratio", 0.25)),
    )
    config_path = iteration_dir / "config.yaml"
    dump_yaml(config, config_path)

    run_label = "Final optimization" if is_final else f"Iteration {iteration} optimization"
    _console.print(f"[bold yellow]Running {run_label}[/bold yellow] (timeout: {timeout}s)...")
    _console.print("[dim]--- workflow subprocess output below ---[/dim]")
    executor = _get_executor(base_workflow)
    result = executor.run(
        config_path=config_path,
        output_dir=iteration_dir,
        timeout=timeout,
        workflow_config=base_workflow,
        execution_config=execution_cfg,
    )

    _console.print("[dim]--- workflow subprocess complete ---[/dim]")
    if result.success:
        _console.print(f"[green]✓ {run_label} complete[/green] (best: {result.best_objective})")
    else:
        _console.print(f"[red]✗ {run_label} failed[/red]: {result.error}")

    execution_dict = _execution_result_to_dict(result)
    if result.success:
        execution_dict = _enhance_results_with_metrics(execution_dict, base_workflow)

    return {
        "execution_result": execution_dict,
        "current_iteration": iteration,
        "current_variant": variant,
    }


def _execution_result_to_dict(r: ExecutionResult) -> Dict[str, Any]:
    return {
        "success": r.success,
        "best_objective": r.best_objective,
        "best_solution": r.best_solution,
        "total_evaluations": r.total_evaluations,
        "convergence_history": r.convergence_history or [],
        "run_info": r.run_info or {},
        "results_file": r.results_file,
        "csv_file": r.csv_file,
        "error": r.error,
    }


def _enhance_results_with_metrics(
    execution: Dict[str, Any], workflow_config: Dict[str, Any]
) -> Dict[str, Any]:
    if not execution.get("success"):
        return execution
    convergence_history = execution.get("convergence_history", [])
    metrics: Dict[str, Any] = {}
    if convergence_history:
        metrics["convergence_pattern"] = analyze_convergence_pattern(convergence_history)

    results_file = execution.get("results_file")
    csv_file = execution.get("csv_file")
    if results_file and csv_file:
        try:
            from .tools.workflow import calculate_genotypic_diversity

            _, pop_gen0, pop_final = extract_convergence_with_populations(
                Path(results_file), Path(csv_file)
            )
            if pop_gen0 is not None and pop_final is not None:
                metrics["diversity"] = {
                    "gen0": calculate_genotypic_diversity(pop_gen0),
                    "final": calculate_genotypic_diversity(pop_final),
                }
        except Exception:
            pass
    execution["metrics"] = metrics
    return execution


def prepare_final(state: WorkflowState) -> Dict[str, Any]:
    """Prepare state for final workflow run: set phase=final, iteration_dir, strategy from best."""
    experiment_dir = Path(state["experiment_dir"])
    final_dir = experiment_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    best = state.get("best_solution") or {}
    strategy = best.get("strategy") or state.get("strategy", {})
    return {
        "phase": "final",
        "iteration_dir": str(final_dir),
        "current_strategy": strategy,
        "current_iteration": "final",
        "current_variant": "final",
    }


def update_best_and_continue(state: WorkflowState) -> Dict[str, Any]:
    """Update best solution from execution result; decide whether to continue."""
    execution_result = state.get("execution_result", {})
    candidate = {
        "iteration": state.get("current_iteration"),
        "variant": state.get("current_variant"),
        "strategy": state.get("current_strategy", {}),
        "execution_result": execution_result,
    }

    all_solutions = list(state.get("all_solutions", []))
    all_solutions.append(candidate)

    best_solution = state.get("best_solution")
    if execution_result.get("success"):
        cand_obj = execution_result.get("best_objective")
        if best_solution is None or (
            cand_obj is not None
            and (best_solution.get("execution_result", {}).get("best_objective") or -float("inf"))
            < cand_obj
        ):
            best_solution = candidate

    total_simulations = state.get("total_simulations", 0)
    if isinstance(execution_result.get("total_evaluations"), int):
        total_simulations += execution_result["total_evaluations"]

    max_iterations = state.get("max_iterations", 3)
    current_iteration = state.get("current_iteration", 1)
    max_total = state.get("workflow_config", {}).get("constraints", {}).get(
        "max_total_simulations", float("inf")
    )
    phase = state.get("phase", "iterate")

    # Continue if more iterations and under budget; skip final if we're already in final phase
    should_continue = (
        phase != "final"
        and current_iteration != "final"
        and current_iteration < max_iterations
        and total_simulations < max_total
    )

    return {
        "all_solutions": all_solutions,
        "best_solution": best_solution,
        "total_simulations": total_simulations,
        "should_continue": should_continue,
    }


def final_report(state: WorkflowState) -> Dict[str, Any]:
    """Generate final report."""
    _console.print("[bold cyan]Generating final report[/bold cyan]...")
    experiment_dir = state.get("experiment_dir", "")
    report = {
        "experiment_dir": experiment_dir,
        "execution_mode": state.get("execution_mode", "serial"),
        "total_iterations": len(state.get("all_solutions", [])),
        "total_simulations": state.get("total_simulations", 0),
        "best_solution": ensure_serializable(state.get("best_solution")),
        "all_solutions": ensure_serializable(state.get("all_solutions", [])),
        "timestamp": datetime.now().isoformat(),
    }
    report_path = Path(experiment_dir) / "final_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return {"report": report, "phase": "done"}


def _get_team(workflow_config: Dict[str, Any]):
    """Lazy-build agent team from config. Cached per graph invocation."""
    from .agents import AgentTeam

    llm_config = workflow_config.get("llm", {})
    agents_cfg = workflow_config.get("agents", {})
    team = AgentTeam()
    team.add_agent(ReservoirAnalystAgent(agents_cfg.get("reservoir_analyst", {}), llm_config))
    team.add_agent(StrategyProposerAgent(agents_cfg.get("strategy_proposer", {}), llm_config))
    team.add_agent(CriticAgent(agents_cfg.get("critic", {}), llm_config))
    team.add_agent(ResultAnalystAgent(agents_cfg.get("result_analyst", {}), llm_config))
    team.add_agent(KnowledgeRetrieverAgent(agents_cfg.get("knowledge_retriever", {}), llm_config))
    return team


# ---------------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------------


def _route_after_initial(state: WorkflowState) -> str:
    """After initial_analysis: go to first iteration or final run."""
    return "evolve_strategy"


def _route_after_run(state: WorkflowState) -> str:
    """After run_workflow + update: continue iterating, prepare final, or report."""
    if state.get("should_continue"):
        return "evolve_strategy"
    if state.get("phase") == "final":
        return "final_report"
    return "prepare_final"


# ---------------------------------------------------------------------------
# Graph build
# ---------------------------------------------------------------------------


def build_workflow_graph() -> Any:
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(WorkflowState)

    workflow.add_node("initial_analysis", initial_analysis)
    workflow.add_node("evolve_strategy", evolve_strategy)
    workflow.add_node("run_workflow", run_workflow)
    workflow.add_node("update_best", update_best_and_continue)
    workflow.add_node("prepare_final", prepare_final)
    workflow.add_node("final_report", final_report)

    workflow.set_entry_point("initial_analysis")

    workflow.add_edge("initial_analysis", "evolve_strategy")
    workflow.add_edge("evolve_strategy", "run_workflow")
    workflow.add_edge("run_workflow", "update_best")

    workflow.add_conditional_edges(
        "update_best",
        _route_after_run,
        {
            "evolve_strategy": "evolve_strategy",
            "prepare_final": "prepare_final",
            "final_report": "final_report",
        },
    )

    workflow.add_edge("prepare_final", "run_workflow")
    workflow.add_edge("final_report", END)

    return workflow.compile()
