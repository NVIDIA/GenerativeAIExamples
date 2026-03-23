#!/usr/bin/env python3
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
Query MilvusDB with optional metadata filtering.

Uses the same NVIDIA embedding as the pipeline (nvidia_embedding.get_embedding_for_query
and embed_texts with input_type="query") and supports
Milvus filtered search: scalar filter expressions are applied before/during
vector similarity search so only entities matching the filter are considered.

Collection fields (from run_milvus_pipeline): id, chunk, source, vector, metadata.
- source: VARCHAR (file path or URL)
- metadata: VARCHAR (JSON string from LLM extraction)

Filter expression syntax (Milvus boolean expressions):
  https://milvus.io/docs/boolean.md
  https://milvus.io/docs/filtered-search.md

Examples:
  source == "exact_path"
  source like "%/subfolder/%"
  source in ["path1", "path2"]
  id >= 0 and id < 100
  metadata like "%keyword%"

Requires: NVIDIA_API_KEY, Milvus at MILVUS_URI (default http://localhost:19530).

Usage:
  python query_milvus_with_filters.py --query "how to set up well" --collection docs
  python query_milvus_with_filters.py --query "COMPDAT examples" --collection simulator_input_examples
  python query_milvus_with_filters.py --query "keywords" --filter 'source like "%/deck/%"'
  python query_milvus_with_filters.py --query "..." --source-prefix /path/to/opm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import numpy as np
from pymilvus import MilvusClient

from nvidia_embedding import (
    EMBEDDING_DIM,
    NvidiaEmbeddingModel,
    get_embedding_for_query,
)
from nvidia_reranker import call_reranker

# Defaults (match run_milvus_pipeline; use MILVUS_URI in Docker e.g. http://standalone:19530)
DEFAULT_URI = os.environ.get("MILVUS_URI", "http://localhost:19530")
DEFAULT_TOP_K = 10
# When reranking: fetch this many from Milvus, then rerank and return RERANK_TOP_K
RERANK_CANDIDATES = DEFAULT_TOP_K
RERANK_TOP_K = 5
SEARCH_PARAMS = {"metric_type": "IP", "params": {"nprobe": 1024}}
OUTPUT_FIELDS = ["id", "chunk", "source", "metadata"]


def build_filter_by_source(
    *,
    exact: str | None = None,
    prefix: str | None = None,
    substring: str | None = None,
    in_list: list[str] | None = None,
) -> str:
    """
    Build a Milvus filter expression on the 'source' field.

    Only one of exact, prefix, substring, in_list should be set.
    Returns empty string if none set (no filter).
    """
    if exact is not None:
        # Escape double quotes in path
        safe = exact.replace('\\', '\\\\').replace('"', '\\"')
        return f'source == "{safe}"'
    if prefix is not None:
        safe = prefix.replace('\\', '\\\\').replace('"', '\\"').replace("%", "\\%")
        return f'source like "{safe}%"'
    if substring is not None:
        safe = substring.replace('\\', '\\\\').replace('"', '\\"').replace("%", "\\%")
        return f'source like "%{safe}%"'
    if in_list is not None and len(in_list) > 0:
        # source in ["path1", "path2"]
        escaped = [p.replace("\\", "\\\\").replace('"', '\\"') for p in in_list]
        parts = ", ".join(f'"{p}"' for p in escaped)
        return f"source in [{parts}]"
    return ""


def build_filter_metadata_contains(keyword: str) -> str:
    """
    Build a filter that matches entities whose metadata (VARCHAR JSON string)
    contains the given keyword (substring). Requires Milvus 2.5+ (%keyword% pattern).
    """
    if not keyword:
        return ""
    safe = keyword.replace("\\", "\\\\").replace('"', '\\"').replace("%", "\\%")
    return f'metadata like "%{safe}%"'


def search(
    client: MilvusClient,
    embedding_model: NvidiaEmbeddingModel,
    query: str,
    *,
    collection_name: str,
    limit: int = DEFAULT_TOP_K,
    filter_expr: str = "",
    output_fields: list[str] | None = None,
) -> list[list[dict]]:
    """
    Run vector similarity search with optional scalar filter.

    Uses get_embedding_for_query (same embedding path as run_milvus_pipeline:
    embed_texts with input_type="query", L2-normalized for IP).

    filter_expr: Milvus boolean expression (e.g. 'source like "%/deck/%"').
                 Empty string = no filtering.
    Returns: list of lists (one list per query vector); each element is
             {"id", "distance", "entity": {output_fields}}.
    """
    query_vec = get_embedding_for_query(embedding_model, query)
    query_vec = np.float32(query_vec)
    output_fields = output_fields or OUTPUT_FIELDS

    results = client.search(
        collection_name=collection_name,
        data=[query_vec],
        limit=limit,
        filter=filter_expr,
        search_params=SEARCH_PARAMS,
        output_fields=output_fields,
        consistency_level="Eventually",
    )
    return results


def format_hit(hit: dict) -> str:
    """Format a single search hit for readable output."""
    entity = hit.get("entity", {})
    chunk = (entity.get("chunk") or "")[:500]
    source = entity.get("source", "")
    meta = entity.get("metadata", "[]")
    try:
        meta_parsed = json.loads(meta) if isinstance(meta, str) else meta
        meta_str = json.dumps(meta_parsed, ensure_ascii=False)[:300]
    except Exception:
        meta_str = str(meta)[:300]
    return (
        f"  id={hit.get('id')} distance={hit.get('distance', 0):.4f}\n"
        f"  source: {source}\n"
        f"  chunk: {chunk}...\n"
        f"  metadata: {meta_str}...\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query Milvus with optional metadata/source filtering"
    )
    parser.add_argument("--query", "-q", type=str, required=True, help="Search query text")
    parser.add_argument(
        "--collection", "-c",
        type=str,
        default="docs",
        choices=["docs", "simulator_input_examples"],
        help="Milvus collection name: docs (manual/papers) or simulator_input_examples (OPM examples)",
    )
    parser.add_argument("--uri", type=str, default=DEFAULT_URI, help="Milvus URI")
    parser.add_argument(
        "--topk", "-k", type=int, default=DEFAULT_TOP_K, help="Max results to return"
    )
    parser.add_argument(
        "--filter", "-f", type=str, default="", help="Raw Milvus filter expression (e.g. 'source like \"%/deck/%\"')"
    )
    parser.add_argument(
        "--source-exact", type=str, default=None, help="Filter by exact source path"
    )
    parser.add_argument(
        "--source-prefix", type=str, default=None, help="Filter by source path prefix"
    )
    parser.add_argument(
        "--source-substring", type=str, default=None, help="Filter by source path substring"
    )
    parser.add_argument(
        "--source-in",
        type=str,
        default=None,
        metavar="PATH1,PATH2,...",
        help="Filter by source in comma-separated list",
    )
    parser.add_argument(
        "--metadata-contains",
        type=str,
        default=None,
        metavar="KEYWORD",
        help="Filter by metadata JSON string containing this keyword (substring)",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Do not request metadata in output (faster if not needed)",
    )
    args = parser.parse_args()

    # Build filter: raw expr, or combine source + metadata filters
    filter_expr = args.filter.strip()
    if not filter_expr:
        in_list = None
        if args.source_in:
            in_list = [p.strip() for p in args.source_in.split(",") if p.strip()]
        source_filter = build_filter_by_source(
            exact=args.source_exact,
            prefix=args.source_prefix,
            substring=args.source_substring,
            in_list=in_list,
        )
        meta_filter = build_filter_metadata_contains(args.metadata_contains or "")
        parts = [f for f in (source_filter, meta_filter) if f]
        filter_expr = " and ".join(parts) if len(parts) > 1 else (parts[0] if parts else "")

    output_fields = ["id", "chunk", "source"]
    if not args.no_metadata:
        output_fields.append("metadata")

    client = MilvusClient(uri=args.uri)
    if not client.has_collection(args.collection):
        print(f"Error: collection '{args.collection}' does not exist.", file=sys.stderr)
        return 1

    embedding_model = NvidiaEmbeddingModel()
    limit = RERANK_CANDIDATES
    results = search(
        client,
        embedding_model,
        args.query,
        collection_name=args.collection,
        limit=limit,
        filter_expr=filter_expr,
        output_fields=output_fields,
    )

    hits = results[0] if results else []
    if hits:
        passages = [h.get("entity", {}).get("chunk") or "" for h in hits]
        rerank_resp = call_reranker(args.query, passages)
        rankings = rerank_resp.get("rankings", [])
        # rankings: list of {index, logit}, higher logit = more relevant
        rankings_sorted = sorted(rankings, key=lambda x: x.get("logit", 0), reverse=True)
        top_indices = [r["index"] for r in rankings_sorted[:RERANK_TOP_K]]
        hits = [hits[i] for i in top_indices if i < len(hits)]

    print(f"Query: {args.query!r}")
    if filter_expr:
        print(f"Filter: {filter_expr}")
    label = f"Top-{len(hits)} results (reranked)"
    print(f"{label}:\n")
    for hit in hits:
        print(format_hit(hit))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
