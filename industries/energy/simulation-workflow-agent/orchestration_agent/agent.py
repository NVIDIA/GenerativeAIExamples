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
Orchestration agent: routes user queries to sim_agent (interactive) or workflow_agent (deterministic).
Calls agents via their Python APIs. Both agents remain runnable standalone.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

# Repo root (orchestration_agent/agent.py -> parent=orchestration_agent, parent.parent=repo)
REPO_ROOT = Path(__file__).resolve().parent.parent
SIM_DIR = REPO_ROOT / "sim_agent"
WORKFLOW_DIR = REPO_ROOT / "workflow_agent"
DEFAULT_ORCH_CONFIG = REPO_ROOT / "config" / "orchestration_config.yaml"


def _ensure_import_paths() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    for d in (SIM_DIR / "src", WORKFLOW_DIR / "src"):
        if d.exists() and str(d) not in sys.path:
            sys.path.insert(0, str(d))


def _looks_like_workflow_config(cfg: dict[str, Any]) -> bool:
    """Return True if cfg has sections typical of workflow_agent config (llm, agents, workflow, etc.)."""
    if not isinstance(cfg, dict):
        return False
    required = {"llm", "agents", "workflow"}
    if not required.issubset(cfg.keys()):
        return False
    wf = cfg.get("workflow", {})
    if not isinstance(wf, dict):
        return False
    if "base_config_path" not in wf and "run_command" not in wf:
        return False
    return True


def _find_workflow_config(
    query: str,
    files: list[str],
    default_path: str | None,
) -> tuple[Path | None, str]:
    """Find workflow config from query, uploaded files, or default. Returns (resolved_path, source) or (None, "")."""
    extracted = _extract_workflow_config_from_query(query)
    if extracted:
        p = resolve_path(extracted)
        if p.exists():
            return (p, "query")

    for f in files or []:
        p = Path(f)
        if not p.exists():
            continue
        try:
            cfg = load_yaml(p)
            if _looks_like_workflow_config(cfg):
                return (p.resolve(), "uploaded")
        except Exception:
            continue

    if default_path:
        p = resolve_path(default_path)
        if p.exists():
            return (p, "default")

    return (None, "")


def _validate_and_resolve_workflow_config(
    query: str,
    files: list[str],
    default_path: str | None,
) -> tuple[Path | None, str]:
    """Two-step check: (1) find config, (2) validate content. Returns (resolved_path, source) or (None, "")."""
    path, source = _find_workflow_config(query, files, default_path)
    if path is None:
        return (None, "")
    try:
        cfg = load_yaml(path)
        if not _looks_like_workflow_config(cfg):
            return (None, "")
    except Exception:
        return (None, "")
    return (path, source)


def route_query_llm(query: str, llm_cfg: dict[str, Any]) -> str:
    if not query.strip():
        return "sim"
    if not os.environ.get("NVIDIA_API_KEY", "").strip():
        raise RuntimeError(
            "NVIDIA_API_KEY is not set. Set it before running:\n"
            "  export NVIDIA_API_KEY=\"your_key_here\"\n"
            "Get an API key at https://build.nvidia.com/explore/discover"
        )

    from llm_provider import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    system = llm_cfg.get("routing_system_prompt", "").strip()
    if not system:
        raise RuntimeError(
            "routing_system_prompt is missing in orchestration config.\n"
            f"Add it under llm.routing_system_prompt in {DEFAULT_ORCH_CONFIG}"
        )

    llm = ChatOpenAI.from_config(llm_cfg)
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=query)])
    content = (resp.content or "").strip().lower()
    if "workflow" in content:
        return "workflow"
    return "sim"


def _extract_workflow_config_from_query(query: str) -> str | None:
    """Extract workflow config path from query if present."""
    clean = query.replace("`", "")
    match = re.search(r"workflow_agent/conf/(config[\w\-]*\.yaml)", clean, re.IGNORECASE)
    if match:
        return f"workflow_agent/conf/{match.group(1)}"
    match = re.search(r"workflow/optimization/conf/([\w\-]+\.yaml)", clean, re.IGNORECASE)
    if match:
        return f"workflow/optimization/conf/{match.group(1)}"
    return None


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_path(candidate: str, base: Path = REPO_ROOT) -> Path:
    """Resolve path: absolute or relative to base."""
    p = Path(candidate)
    if p.is_absolute():
        return p
    return (base / candidate).resolve()


def run_sim_agent(
    query: str,
    *,
    config_path: Path | None = None,
    files: list[str] | None = None,
    interactive: bool = False,
    output_dir: str = ".",
    base_file: str = "",
) -> int:
    """Call sim_agent via its Python API."""
    from simulator_agent.runner import SimulatorAgent

    config_str = str(config_path) if config_path and config_path.exists() else None
    agent = SimulatorAgent(config_path=config_str)

    if interactive:
        agent.run_interactive(
            output_dir=output_dir,
            base_simulation_file=base_file,
            uploaded_files=files,
        )
        return 0

    out = agent.run_single(
        query,
        uploaded_files=files or [],
        output_dir=output_dir,
        base_simulation_file=base_file,
    )
    print("\n--- Result ---")
    print(out.get("agent_final_output", ""))
    return 0


@contextmanager
def _workflow_cwd() -> Generator[None, None, None]:
    """Change to workflow dir for config resolution, then restore."""
    orig = os.getcwd()
    try:
        os.chdir(WORKFLOW_DIR)
        yield
    finally:
        os.chdir(orig)


def run_workflow_agent(
    base_config_path: str | None = None,
    *,
    workflow_config_path: str,
    iterations: int | None = None,
) -> int:
    """Call workflow_agent via its Python API."""
    from workflow_agent.runner import AgenticWorkflow

    wf_config = str(resolve_path(workflow_config_path))
    with _workflow_cwd():
        runner = AgenticWorkflow(workflow_config=wf_config)
        result = runner.run_complete_workflow(
            base_config_path=base_config_path,
            max_iterations=iterations,
        )
    return 0 if result.get("report") else 1


def load_orchestration_config(config_path: Path | None) -> dict[str, Any]:
    """Load top-level orchestration config. Returns empty dict if not found."""
    path = config_path or DEFAULT_ORCH_CONFIG
    if not path.exists():
        return {}
    return load_yaml(path)


def _run_orchestrator_interactive(
    sim_config_path: Path | None,
    sim_output_dir: str,
    sim_base_file: str,
    workflow_config_resolved: str,
    workflow_config_display: str,
    workflow_iterations: int | None,
    workflow_base_config: str | None,
    llm_cfg: dict[str, Any],
    files: list[str],
) -> int:
    """Run orchestrator-level interactive loop: route each query via LLM."""
    print("Simulation Workflow Assistant — Interactive mode", file=sys.stderr)
    print("Type your query and press Enter. Commands: 'quit' or 'exit' to stop.", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    while True:
        try:
            line = input("\nYou: ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line.lower() in ("quit", "exit"):
            break

        try:
            target = route_query_llm(line, llm_cfg)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            continue

        wf_path, wf_source = None, ""
        if target == "workflow":
            wf_path, wf_source = _validate_and_resolve_workflow_config(
                line, files, workflow_config_display
            )
            if wf_path is None:
                print(
                    "[Orchestrator] No valid workflow config in query or uploaded files; routing to sim_agent",
                    file=sys.stderr,
                )
                target = "sim"
            else:
                print(
                    f"[Orchestrator] Using workflow config (from {wf_source}): {wf_path}",
                    file=sys.stderr,
                )

        print(f"[Orchestrator] Routing to {target}_agent", file=sys.stderr)

        if target == "workflow":
            base_config_raw = files[0] if files else workflow_base_config
            base_config = str(resolve_path(base_config_raw)) if base_config_raw else None
            run_workflow_agent(
                base_config,
                workflow_config_path=str(wf_path),
                iterations=workflow_iterations,
            )
        else:
            out = run_sim_agent(
                line,
                config_path=sim_config_path,
                files=files or None,
                interactive=False,
                output_dir=sim_output_dir,
                base_file=sim_base_file,
            )
            if out != 0:
                return out

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Orchestration agent: routes to sim_agent or workflow_agent"
    )
    parser.add_argument(
        "--config",
        "-c",
        metavar="PATH",
        default=None,
        help=f"Orchestration config (default: {DEFAULT_ORCH_CONFIG})",
    )
    parser.add_argument("query", nargs="?", help="User query (optional if --interactive)")
    parser.add_argument(
        "--uploaded-files",
        "-f",
        metavar="PATH",
        nargs="*",
        default=[],
        dest="files",
        help="File path(s). Sim: .DATA files. Workflow: base config YAML.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive mode: route each query to sim or workflow via LLM.",
    )

    args = parser.parse_args()
    query = (args.query or "").strip()

    if not query and not args.interactive:
        parser.print_help()
        print("\nProvide a query or use --interactive for sim chat mode.")
        return 1

    _ensure_import_paths()
    config_path = Path(args.config) if args.config else DEFAULT_ORCH_CONFIG
    orch = load_orchestration_config(config_path)

    sim_cfg = orch.get("sim", {})
    workflow_cfg = orch.get("workflow", {})

    sim_config_path = resolve_path(sim_cfg["config"]) if sim_cfg.get("config") else None

    workflow_config_path = workflow_cfg.get("config", "workflow_agent/conf/config.yaml")
    workflow_config_resolved = str(resolve_path(workflow_config_path))
    workflow_iterations = workflow_cfg.get("iterations")
    workflow_base_config = workflow_cfg.get("base_config")

    llm_cfg = orch.get("llm", {})

    if args.interactive and not query:
        return _run_orchestrator_interactive(
            sim_config_path=sim_config_path,
            sim_output_dir=".",
            sim_base_file=sim_cfg.get("base_file", ""),
            workflow_config_resolved=workflow_config_resolved,
            workflow_config_display=workflow_config_path,
            workflow_iterations=workflow_iterations,
            workflow_base_config=workflow_base_config,
            llm_cfg=llm_cfg,
            files=args.files or [],
        )

    try:
        target = route_query_llm(query, llm_cfg) if query else "sim"
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if target == "workflow":
        wf_path, wf_source = _validate_and_resolve_workflow_config(
            query, args.files or [], workflow_config_path
        )
        if wf_path is None:
            print(
                "[Orchestrator] No valid workflow config in query or uploaded files; routing to sim_agent",
                file=sys.stderr,
            )
            target = "sim"
        else:
            workflow_config_resolved = str(wf_path)
            print(
                f"[Orchestrator] Using workflow config (from {wf_source}): {wf_path}",
                file=sys.stderr,
            )

    print(f"[Orchestrator] Routing to {target}_agent", file=sys.stderr)

    if target == "workflow":
        base_config_raw = args.files[0] if args.files else workflow_base_config
        base_config = str(resolve_path(base_config_raw)) if base_config_raw else None

        return run_workflow_agent(
            base_config,
            workflow_config_path=workflow_config_resolved,
            iterations=workflow_iterations,
        )

    return run_sim_agent(
        query or "Hello! How can I help you with simulation?",
        config_path=sim_config_path,
        files=args.files or None,
        interactive=False,
        output_dir=".",
        base_file=sim_cfg.get("base_file", ""),
    )
