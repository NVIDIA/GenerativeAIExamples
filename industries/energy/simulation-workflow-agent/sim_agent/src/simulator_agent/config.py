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
Simulator agent configuration: AgentConfig, get_config, init_config.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Optional


_DEFAULT_LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1.5"

_config: Optional["AgentConfig"] = None


class AgentConfig:
    """Holds shared config, paths, and env. Supports injection for testability."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.entry_dir = Path(__file__).resolve().parent
        self.project_root = self.entry_dir.parent.parent
        self._config: dict[str, Any] = {}
        self._config_path: Optional[Path] = None
        self._load(config_path)

    def _load(self, config_path: str | Path | None) -> None:
        env_val = os.environ.get("CONFIG_PATH", "").strip()
        path = Path(config_path) if config_path else (Path(env_val) if env_val else self.project_root / "config" / "config.yaml")
        if path and path.exists():
            try:
                with open(path, "r") as f:
                    self._config = yaml.safe_load(f) or {}
                self._config_path = Path(path).resolve()
                self._sync_to_env(path, explicit_path=config_path is not None)
            except Exception:
                pass

    def _sync_to_env(self, loaded_path: Path, *, explicit_path: bool = False) -> None:
        """Sync config to env for subprocesses. SIM_LLM_MODEL is never overwritten."""
        if explicit_path or not os.environ.get("CONFIG_PATH"):
            os.environ["CONFIG_PATH"] = str(loaded_path.resolve())
        if self._config and not os.environ.get("SIM_LLM_MODEL"):
            model = (self._config.get("llm") or {}).get("model_name")
            if model:
                os.environ["SIM_LLM_MODEL"] = model

    def get_llm_model(self, use_for: str = "tool") -> str:
        if self._config:
            llm_cfg = self._config.get("llm", {})
            agent_cfg = self._config.get("agent", {})
            if use_for == "plot_metric":
                model = agent_cfg.get("plot_metric_llm_model")
            else:
                model = None
            if not model:
                model = llm_cfg.get("model_name", _DEFAULT_LLM_MODEL)
            if model:
                return model
        return os.environ.get("SIM_LLM_MODEL", _DEFAULT_LLM_MODEL)

    def get_reranker_config(self) -> tuple[str, str]:
        """Return (url, model) for reranker. Used when rag.use_reranker is true."""
        default_url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-3_2-nv-rerankqa-1b-v2/reranking"
        default_model = "nvidia/llama-3.2-nv-rerankqa-1b-v2"
        if self._config:
            rag = self._config.get("rag", {})
            url = (rag.get("reranker_url") or "").strip() or default_url
            model = (rag.get("reranker_model") or "").strip() or default_model
            return (url, model)
        return (default_url, default_model)

    def get_manual_collection_name(self) -> str:
        """Milvus collection for simulator_manual (from config or default)."""
        name = (self._config.get("retrievers", {}).get("simulator_manual", {}).get("collection_name") or "").strip()
        if name in ("simulator_manual", "simulator_input_examples", "docs"):
            return name
        return "docs"

    def get_project_roots(self) -> list[Path]:
        roots: list[Path] = [Path.cwd()]
        env_root = os.environ.get("SIM_PROJECT_ROOT") or os.environ.get("OPM_PROJECT_ROOT")
        if env_root and Path(env_root).is_dir():
            roots.append(Path(env_root).resolve())
        if self.project_root.is_dir():
            roots.append(self.project_root)
        return roots


def get_config() -> AgentConfig:
    """Return the shared config. Call init_config() before first use if custom path needed."""
    global _config
    if _config is None:
        _config = AgentConfig()
    return _config


def init_config(config_path: str | Path | None = None) -> AgentConfig:
    """Initialize config (e.g. from CLI --config). Supports injection for tests."""
    global _config
    _config = AgentConfig(config_path)
    return _config


def set_config(config: AgentConfig) -> None:
    """Inject config (e.g. for tests)."""
    global _config
    _config = config
