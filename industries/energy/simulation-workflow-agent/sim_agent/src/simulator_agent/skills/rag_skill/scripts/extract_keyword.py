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
Extract simulator summary (time series) output keyword from user query. Used by plot_skill for metrics like FOPT, FOPR, FWCT.

Flow: normalize → common list → RAG+LLM fallback. Raises AmbiguousQueryError when ambiguous.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

LOG = logging.getLogger(__name__)


class AmbiguousQueryError(Exception):
    """Query is ambiguous (e.g. "field oil production" without cumulative vs rate)."""


_RAG_CONTEXT_MAX_CHARS = 3000
_THINK_END_TAGS = ("</think>", "</THINK>")
_TYPO_FIXES = [("productin", "production"), ("producton", "production")]

_NORMALIZE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "normalized": {"type": "string"},
        "ambiguous": {"type": "boolean"},
    },
    "required": ["normalized"],
}

_NORMALIZE_PROMPT = """Normalize the metric request for reservoir simulation. Fix typos, expand abbreviations.
Output a canonical phrase (e.g. "field cumulative oil production", "field oil production rate").
If ambiguous (e.g. "field oil production" without cumulative vs rate), set "ambiguous": true.
JSON: {"normalized": "...", "ambiguous": false|true}. No other keys."""

_COMMON_METRIC_MAP = [
    ("field cumulative oil production", "FOPT"),
    ("field cumulative oil", "FOPT"),
    ("field total oil production", "FOPT"),
    ("field oil production rate", "FOPR"),
    ("field cumulative water production", "FWPT"),
    ("field water production total", "FWPT"),
    ("field water production rate", "FWPR"),
    ("field water cut", "FWCT"),
    ("field watercut", "FWCT"),
    ("field cumulative gas production", "FGPT"),
    ("field gas production rate", "FGPR"),
    ("field average pressure", "FPR"),
    ("bottom hole pressure", "WBHP"),
    ("well bottom hole pressure", "WBHP"),
    ("bhp", "WBHP"),
    ("well oil production rate", "WOPR"),
    ("well cumulative oil production", "WOPT"),
    ("well oil production total", "WOPT"),
    ("well water production rate", "WWPR"),
    ("well cumulative water production", "WWPT"),
    ("well water cut", "WWCT"),
    ("well gas oil ratio", "WGOR"),
    ("well gor", "WGOR"),
]

_KNOWN_SUMMARY_KEYWORDS = frozenset(kw for _, kw in _COMMON_METRIC_MAP)
_SUMMARY_KEYWORD_PATTERN = re.compile(r"^[FW][A-Z]{2,5}$")
_METRIC_JSON_SCHEMA = {"type": "object", "properties": {"metric": {"type": "string"}}, "required": ["metric"]}


def _is_valid_metric(kw: str) -> bool:
    return bool(kw and _SUMMARY_KEYWORD_PATTERN.match(kw))

_SUMMARY_METRIC_PROMPT = """Identify the metric keyword from the user query.
Format: F/W (field/well) + oil/water/gas (O/W/G) + production/injection (P/I) + total(T) or rate(R). Examples: FOPT, FOPR, FWPT, FWPR.
Exceptions include (but not limited to): ratios like watercut (WWCT, FWCT) and gas-oil ratio (WGOR); pressure: FPR (field), WBHP (well bottom-hole pressure), etc.
If ambiguous (e.g. "field oil production" without cumulative vs rate), respond {"metric": "UNKNOWN"}.
JSON: {"metric": "FOPT"|"UNKNOWN"}. No other keys."""


def _retrieve_manual_context(user_query: str, collection_name: str) -> str:
    """Retrieve relevant manual chunks. Returns empty string if RAG unavailable."""
    try:
        from .rag_chain import run_milvus_query

        retrieval = run_milvus_query(
            query=user_query,
            collection_name=collection_name,
        )
        if retrieval and not retrieval.strip().startswith("[Error"):
            return retrieval.strip()
    except Exception as e:
        LOG.debug("extract_keyword: RAG retrieval skipped: %s", e)
    return ""


def _match_common_list(user_query: str) -> Optional[str]:
    """Match query against common phrases. Returns keyword or None."""
    q = (user_query or "").lower().strip()
    if not q:
        return None
    q = re.sub(r"\s+", " ", q)
    for wrong, right in _TYPO_FIXES:
        q = q.replace(wrong, right)
    for phrase, keyword in _COMMON_METRIC_MAP:
        if phrase in q:
            return keyword
    return None


def _extract_keyword_via_rag_llm(query: str, raw: str) -> Optional[str]:
    """Fallback: RAG + LLM to extract metric. Returns None if ambiguous or invalid."""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from simulator_agent.config import get_config
        from llm_provider import ChatOpenAI
    except ImportError:
        return None
    if not os.environ.get("NVIDIA_API_KEY"):
        return None

    config = get_config()
    manual_context = _retrieve_manual_context(raw, config.get_manual_collection_name())
    prompt = _SUMMARY_METRIC_PROMPT
    if manual_context:
        prompt = f"""{prompt}

<RETRIEVED_CONTEXT>
{manual_context[:_RAG_CONTEXT_MAX_CHARS]}
</RETRIEVED_CONTEXT>

Use the context above. Map the query to one metric keyword. If ambiguous, {{"metric": "UNKNOWN"}}."""

    try:
        llm = ChatOpenAI(model=config.get_llm_model(use_for="plot_metric"), max_tokens=256, temperature=0.1)
        msg = llm.invoke(
            [SystemMessage(content=prompt), HumanMessage(content=query)],
            extra_body={"nvext": {"guided_json": _METRIC_JSON_SCHEMA}},
        )
        content = (getattr(msg, "content", None) or str(msg)).strip()

        try:
            data = json.loads(content)
            kw = (data.get("metric") or "").strip().upper()
            if kw not in ("UNKNOWN", "") and _is_valid_metric(kw):
                return kw
        except (json.JSONDecodeError, TypeError):
            pass

        search = content
        for end_tag in _THINK_END_TAGS:
            if end_tag in search:
                search = search.split(end_tag)[-1]
        search = search.strip().upper()
        candidates = [m.group(1) for m in re.finditer(r"\b([A-Z]{2,6})\b", search) if _is_valid_metric(m.group(1))]
        for kw in candidates:
            if kw in _KNOWN_SUMMARY_KEYWORDS:
                return kw
        return candidates[0] if candidates else None
    except Exception as e:
        LOG.warning("extract_keyword: LLM failed: %s", e)
        return None


def _normalize_query_with_llm(user_query: str) -> tuple[Optional[str], bool]:
    """Fix typos and normalize phrasing. Returns (normalized_str, is_ambiguous)."""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from simulator_agent.config import get_config
        from llm_provider import ChatOpenAI
    except ImportError:
        return (None, False)
    if not os.environ.get("NVIDIA_API_KEY"):
        return (None, False)
    try:
        llm = ChatOpenAI(model=get_config().get_llm_model(use_for="plot_metric"), max_tokens=128, temperature=0.0)
        msg = llm.invoke(
            [SystemMessage(content=_NORMALIZE_PROMPT), HumanMessage(content=(user_query or "").strip())],
            extra_body={"nvext": {"guided_json": _NORMALIZE_JSON_SCHEMA}},
        )
        data = json.loads((getattr(msg, "content", None) or str(msg)).strip())
        ambiguous = bool(data.get("ambiguous", False))
        normalized = (data.get("normalized") or "").strip()
        if ambiguous:
            return (normalized or None, True)
        if normalized:
            return (normalized, False)
    except Exception:
        pass
    return (None, False)


def extract_keyword(user_query: str, intent: str = "summary_metric") -> Optional[str]:
    """Extract simulator summary keyword (e.g. FOPT) from natural language. Raises AmbiguousQueryError when ambiguous."""
    raw = (user_query or "").strip()
    normalized, is_ambiguous = _normalize_query_with_llm(raw)
    if is_ambiguous:
        raise AmbiguousQueryError(
            "Your metric request is ambiguous. Please specify cumulative/total (e.g. FOPT, FWPT) or rate (e.g. FOPR, FWPR)."
        )
    query = normalized or raw
    kw = _match_common_list(query)
    if kw:
        return kw
    return _extract_keyword_via_rag_llm(query, raw)
