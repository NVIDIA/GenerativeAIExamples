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
Utility helpers for the agentic workflow.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency for serialization
    np = None


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def dump_yaml(data: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


@dataclass(frozen=True)
class WorkflowPaths:
    base_config: Path
    workflow_config: Path


def configure_logging(level: str, log_file: Optional[str] = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def resolve_paths(base_config: Optional[str], workflow_config: str) -> WorkflowPaths:
    workflow_dir = Path(__file__).resolve().parent
    workflow_path = _resolve_path(workflow_config, workflow_dir)
    if not base_config:
        config = load_yaml(workflow_path)
        base_config = config.get("workflow", {}).get("base_config_path")
    if not base_config:
        raise ValueError("Missing base workflow config path")
    base_path = _resolve_path(base_config, Path.cwd())
    return WorkflowPaths(base_config=base_path, workflow_config=workflow_path)


def _resolve_path(candidate: str, base_dir: Path) -> Path:
    path = Path(candidate)
    if path.exists():
        return path
    fallback = base_dir / candidate
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Could not resolve path: {candidate}")


def parse_jsonish(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def parse_yamlish(content: str) -> Dict[str, Any]:
    try:
        return yaml.safe_load(content) or {}
    except yaml.YAMLError:
        return {}


def ensure_serializable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: ensure_serializable(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [ensure_serializable(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(ensure_serializable(item) for item in obj)
    if np is not None:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    return obj


