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
Path resolution utilities for simulator input files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ..config import get_config
from ..state import GlobalState


def output_dir_from_context(state: GlobalState, tool_input: dict, data_file: str = "") -> str:
    out = (tool_input.get("output_dir") or "").strip() or (state.get("output_dir") or "").strip()
    if out:
        return out
    if data_file:
        return str(Path(data_file).parent)
    base = (state.get("base_simulation_file") or "").strip()
    if base:
        return str(Path(base).parent)
    for u in (state.get("uploaded_files") or []):
        uu = (u or "").strip().upper()
        if uu.endswith(".DATA") or uu.endswith(".SMSPEC"):
            return str(Path(u.strip()).parent)
    return "."


def extract_data_file_from_sub_query(sub_query: str) -> Optional[str]:
    if not (sub_query or "").strip():
        return None
    match = re.search(r"[\w./\-\\]+\.DATA", sub_query, re.IGNORECASE)
    return match.group(0).strip() if match else None


def extract_data_files_from_sub_query(sub_query: str) -> list[str]:
    if not (sub_query or "").strip():
        return []
    return re.findall(r"[\w./\-\\]+\.DATA", sub_query, re.IGNORECASE)


def resolve_data_path(path: str, preferred_paths: Optional[list[str]] = None) -> str:
    if not (path or "").strip():
        return path
    path = path.strip()
    p = Path(path)
    path_name = p.name

    def _usable(candidate: Path) -> bool:
        c = candidate.resolve()
        return c.exists() or c.parent.exists()

    preferred = list(preferred_paths or [])
    for pref in preferred:
        if not (pref or "").strip():
            continue
        pref_path = Path(pref.strip()).resolve()
        if pref_path.name == path_name and _usable(pref_path):
            return str(pref_path)
        if path in pref or pref.endswith(path) or str(pref_path) == str(Path(path).resolve()):
            if _usable(pref_path):
                return str(pref_path)
    for pref in preferred:
        if not (pref or "").strip():
            continue
        pref_path = Path(pref.strip()).resolve()
        if pref_path.parent.exists() and path_name != pref_path.name:
            out_candidate = pref_path.parent / path_name
            if _usable(out_candidate):
                return str(out_candidate.resolve())

    if p.is_absolute() and _usable(p):
        return str(p.resolve())
    roots = get_config().get_project_roots()
    for root in roots:
        candidate = (root / path).resolve()
        if _usable(candidate):
            return str(candidate)
    if p.is_absolute():
        return str(p.resolve())
    cfg = get_config()
    fallback_root = cfg.project_root if cfg.project_root.is_dir() else Path.cwd()
    return str((fallback_root / path).resolve())
