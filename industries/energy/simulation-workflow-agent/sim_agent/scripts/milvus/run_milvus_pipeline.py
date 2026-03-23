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
Run the full data preprocessing pipeline and insert into Milvus with parallel embedding:
  1. Create LangChain documents per page (from URL crawl or from directory)
  2. Preprocess
  3. (Optional) Extract metadata per txt file: LLM (llm_extract_metadata) or fast ALL-CAPS keywords (extract_capitalized_words)
  4. NVIDIA embeddings in parallel (nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1)
  5. Build id + chunk + source + vector + metadata and insert into MilvusDB

Uses ThreadPoolExecutor for concurrent embedding and metadata extraction (same pattern as ocr_client_vllm.py).

Requires: NVIDIA_API_KEY, Milvus at MILVUS_URI (default http://localhost:19530).
  In Docker (e.g. docker-compose-ocr.yml), set MILVUS_URI=http://standalone:19530.

Env:
  MILVUS_URI         Milvus connection URI (default: http://localhost:19530)
  MILVUS_MAX_WORKERS  Concurrent embedding workers (default: 2 to avoid 429)
  MILVUS_EMBED_BATCH  Texts per API call (default: 32)
  MILVUS_EMBED_MIN_INTERVAL_SEC  Min seconds between starting embedding batches (default: 2)
  MILVUS_META_WORKERS Concurrent metadata extraction calls (default: 2)
  MILVUS_RATE_LIMIT_SLEEP  Seconds to sleep on 429/500 before retry (default: 5)
  MILVUS_PROCESSED_LIST   Path to processed files list (default: processed_txt_files.md)
  MILVUS_METADATA_MODE    Metadata source: llm or keywords (default: llm)
  EMBED_RATE_LIMIT_SLEEP  Embedding API retry sleep on 429 (default: 10)
  EMBED_MAX_RETRIES       Embedding API max retries on 429 (default: 8)

Example (directory of .txt files):
  python run_milvus_pipeline.py --dir /path/to/txt/files --collection MyDocs
  MILVUS_MAX_WORKERS=8 python run_milvus_pipeline.py --dir /path/to/txt/files
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from milvus_preprocess_pipeline import (
    build_milvus_rows,
    documents_from_directory,
    documents_from_url_text_pairs,
    preprocess_documents,
)
from nvidia_embedding import EMBEDDING_DIM, embed_texts, get_client

# Metadata extraction (LLM) per txt file before embedding
from llm_extract_metadata import response as llm_extract_response
from llm_extract_metadata import strip_thinking_tags
from extract_capitalized_words import extract_all_caps_keywords
# Config from env (mirror ocr_client_vllm pattern)
MAX_WORKERS = int(os.environ.get("MILVUS_MAX_WORKERS", "2"))
EMBED_BATCH_SIZE = int(os.environ.get("MILVUS_EMBED_BATCH", "32"))
META_WORKERS = int(os.environ.get("MILVUS_META_WORKERS", "2"))
RATE_LIMIT_SLEEP = int(os.environ.get("MILVUS_RATE_LIMIT_SLEEP", "5"))
# Min seconds between starting embedding batch requests (reduces 429 from API)
EMBED_MIN_INTERVAL_SEC = float(os.environ.get("MILVUS_EMBED_MIN_INTERVAL_SEC", "2.0"))

# Throttle state for embedding: ensure we don't start batches too close together
_embed_throttle_lock = threading.Lock()
_embed_last_start_time = 0.0
PROCESSED_LIST_PATH = os.environ.get("MILVUS_PROCESSED_LIST", "processed_txt_files.md")
DEFAULT_META_RETRIES = 5
METADATA_MODE_DEFAULT = os.environ.get("MILVUS_METADATA_MODE", "keywords")
DEFAULT_MILVUS_URI = os.environ.get("MILVUS_URI", "http://localhost:19530")


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


def load_processed_paths(filepath: str | Path) -> set[str]:
    """Read processed_txt_files.md (or given path); return set of absolute paths."""
    path = Path(filepath)
    if not path.is_file():
        return set()
    seen: set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Support markdown list lines "- /path" or plain paths
            if line.startswith("- "):
                line = line[2:].strip()
            seen.add(line)
    return seen


def append_processed_paths(filepath: str | Path, paths: list[str]) -> None:
    """Append absolute paths to processed list file (one per line)."""
    if not paths:
        return
    path = Path(filepath)
    with open(path, "a", encoding="utf-8") as f:
        for p in paths:
            f.write(p + "\n")


def _keywords_to_metadata_list(keywords: list[str]) -> list[dict]:
    """Turn list of ALL-CAPS keywords into same shape as LLM metadata (list of dicts)."""
    return [{"keyword": kw} for kw in keywords]


def _extract_keywords_one_doc(page_content: str) -> list[dict]:
    """Extract unique ALL-CAPS keywords from text; return list of {'keyword': kw} dicts."""
    words = extract_all_caps_keywords(page_content, min_length=2)
    unique = list(dict.fromkeys(words))
    return _keywords_to_metadata_list(unique)


def extract_keywords_metadata(docs: list, log: logging.Logger | None = None) -> None:
    """
    Populate doc.metadata["extracted_metadata"] using ALL-CAPS keywords per doc (fast, no API).
    Same structure as LLM path so downstream (Milvus row) is unchanged.
    """
    log = log or logging.getLogger(__name__)
    total = len(docs)
    start = time.perf_counter()
    for i, doc in enumerate(docs):
        doc.metadata["extracted_metadata"] = _extract_keywords_one_doc(doc.page_content)
        if log and (i + 1) % 100 == 0:
            log.info("[%d/%d] keyword metadata extracted (%.1fs)", i + 1, total, time.perf_counter() - start)
            sys.stdout.flush()
    if log and total:
        log.info("Keyword metadata finished for %d docs in %.1fs", total, time.perf_counter() - start)
        sys.stdout.flush()


def _is_retryable_error(e: Exception) -> bool:
    """True if we should sleep and retry (429 rate limit, 500 server error)."""
    msg = str(e).lower()
    if "429" in msg or "too many requests" in msg:
        return True
    if "500" in msg or "internal server error" in msg:
        return True
    code = getattr(e, "status_code", None)
    if code in (429, 500):
        return True
    return False


def _extract_metadata_one_doc(
    doc_idx: int,
    page_content: str,
    log: logging.Logger | None = None,
    rate_limit_sleep: int = RATE_LIMIT_SLEEP,
    max_retries: int = DEFAULT_META_RETRIES,
) -> tuple[int, list[dict]]:
    """
    Run LLM metadata extraction on one document's content.
    On 429 (rate limit) or 500 (server error): sleep rate_limit_sleep seconds and retry.
    Returns (doc_idx, list of metadata dicts). Used by ThreadPoolExecutor.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            raw = llm_extract_response(page_content)
            meta_list = strip_thinking_tags(raw)
            return doc_idx, meta_list if isinstance(meta_list, list) else []
        except Exception as e:
            last_error = e
            if _is_retryable_error(e) and attempt < max_retries - 1:
                if log:
                    log.warning(
                        "Doc %d: rate limit/server error (attempt %d/%d), sleeping %ds: %s",
                        doc_idx,
                        attempt + 1,
                        max_retries,
                        rate_limit_sleep,
                        e,
                    )
                    sys.stdout.flush()
                time.sleep(rate_limit_sleep)
            else:
                break
    if log:
        log.warning("Metadata extraction failed for doc %d: %s", doc_idx, last_error)
    return doc_idx, []


def extract_metadata_parallel(
    docs: list,
    max_workers: int = META_WORKERS,
    log: logging.Logger | None = None,
    rate_limit_sleep: int = RATE_LIMIT_SLEEP,
    max_retries: int = DEFAULT_META_RETRIES,
) -> None:
    """
    Extract metadata for each doc via LLM in parallel; set doc.metadata["extracted_metadata"] in place.
    On 429/500, workers sleep rate_limit_sleep seconds and retry up to max_retries times.
    """
    if not docs:
        return
    log = log or logging.getLogger(__name__)
    total = len(docs)
    completed = 0
    start = time.perf_counter()
    workers = min(max_workers, total)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {
            executor.submit(
                _extract_metadata_one_doc,
                i,
                doc.page_content,
                log,
                rate_limit_sleep,
                max_retries,
            ): i
            for i, doc in enumerate(docs)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                doc_idx, meta_list = future.result()
                docs[doc_idx].metadata["extracted_metadata"] = meta_list
            except Exception as e:
                if log:
                    log.error("Doc %d metadata extraction error: %s", idx, e)
                docs[idx].metadata["extracted_metadata"] = []
            completed += 1
            if log and (completed % 5 == 0 or completed == total):
                log.info(
                    "[%d/%d] metadata extracted (%.1fs elapsed)",
                    completed,
                    total,
                    time.perf_counter() - start,
                )
                sys.stdout.flush()


def _embed_one_batch(
    batch_idx: int,
    texts: list[str],
    client,
    input_type: str = "passage",
    truncate: str = "NONE",
    rate_limit_sleep: int = RATE_LIMIT_SLEEP,
    min_interval_sec: float = EMBED_MIN_INTERVAL_SEC,
) -> tuple[int, list[np.ndarray]]:
    """
    Embed one batch of texts. Returns (batch_idx, list of normalized vectors).
    Used by ThreadPoolExecutor; client is shared and thread-safe for HTTP.
    Throttles: waits so at least min_interval_sec between batch starts. Retries on 429 via embed_texts.
    """
    global _embed_last_start_time
    if not texts:
        return batch_idx, []
    with _embed_throttle_lock:
        now = time.monotonic()
        wait = min_interval_sec - (now - _embed_last_start_time)
        if wait > 0:
            time.sleep(wait)
        _embed_last_start_time = time.monotonic()
    raw = embed_texts(
        client,
        texts,
        input_type=input_type,
        truncate=truncate,
        rate_limit_sleep=rate_limit_sleep,
    )
    vectors = []
    for v in raw:
        vec = np.array(v, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        vectors.append(vec)
    return batch_idx, vectors


def embed_docs_parallel(
    texts: list[str],
    client,
    batch_size: int = EMBED_BATCH_SIZE,
    max_workers: int = MAX_WORKERS,
    log: logging.Logger | None = None,
    rate_limit_sleep: int = RATE_LIMIT_SLEEP,
    min_interval_sec: float = EMBED_MIN_INTERVAL_SEC,
) -> list[np.ndarray]:
    """
    Embed all texts in parallel by batching and submitting each batch to a worker.
    Throttles batch starts by min_interval_sec to avoid 429. Retries on 429 via embed_texts.
    Results are reassembled in original order.
    """
    if not texts:
        return []
    batches: list[tuple[int, list[str]]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batches.append((len(batches), batch))
    total_batches = len(batches)
    # batch_idx -> list of vectors (preserve order when merging)
    results_by_idx: dict[int, list[np.ndarray]] = {}
    completed = 0
    start = time.perf_counter()
    workers = min(max_workers, total_batches)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_batch_idx = {
            executor.submit(
                _embed_one_batch,
                idx,
                batch_texts,
                client,
                "passage",
                "NONE",
                rate_limit_sleep,
                min_interval_sec,
            ): idx
            for idx, batch_texts in batches
        }
        for future in as_completed(future_to_batch_idx):
            batch_idx = future_to_batch_idx[future]
            try:
                idx, vectors = future.result()
                results_by_idx[idx] = vectors
            except Exception as e:
                if log:
                    log.error("Batch %d failed: %s", batch_idx, e)
                raise
            completed += 1
            if log and (completed % 5 == 0 or completed == total_batches):
                elapsed = time.perf_counter() - start
                log.info(
                    "[%d/%d] batches embedded (%.1fs elapsed)",
                    completed,
                    total_batches,
                    elapsed,
                )
                sys.stdout.flush()

    # Reassemble in order
    ordered: list[np.ndarray] = []
    for idx in range(total_batches):
        ordered.extend(results_by_idx[idx])
    return ordered


def run_pipeline_parallel(
    docs,
    *,
    collection_name: str = "docs",
    milvus_uri: str | None = None,
    embedding_batch_size: int = EMBED_BATCH_SIZE,
    max_workers: int = MAX_WORKERS,
    drop_collection_first: bool = False,
    extract_metadata: bool = True,
    metadata_mode: str = "llm",
    meta_workers: int = META_WORKERS,
    rate_limit_sleep: int = RATE_LIMIT_SLEEP,
    meta_retries: int = DEFAULT_META_RETRIES,
    embed_min_interval_sec: float = EMBED_MIN_INTERVAL_SEC,
    log: logging.Logger | None = None,
):
    """
    Run pipeline: preprocess -> (optional) metadata extraction -> parallel embed -> build rows -> insert.
    metadata_mode: "llm" (slow, rich) or "keywords" (fast, ALL-CAPS keywords from extract_capitalized_words).
    """
    from pymilvus import MilvusClient

    if milvus_uri is None:
        milvus_uri = DEFAULT_MILVUS_URI
    log = log or logging.getLogger(__name__)
    docs = preprocess_documents(docs)

    if extract_metadata:
        start_meta = time.perf_counter()
        if metadata_mode == "keywords":
            log.info("Extracting ALL-CAPS keyword metadata for %d docs (fast, no API)...", len(docs))
            sys.stdout.flush()
            extract_keywords_metadata(docs, log=log)
        else:
            log.info(
                "Extracting metadata for %d docs via LLM in parallel (workers=%d)...",
                len(docs),
                meta_workers,
            )
            sys.stdout.flush()
            extract_metadata_parallel(
                docs,
                max_workers=meta_workers,
                log=log,
                rate_limit_sleep=rate_limit_sleep,
                max_retries=meta_retries,
            )
        log.info("Metadata extraction finished in %.1fs", time.perf_counter() - start_meta)
        sys.stdout.flush()

    texts = [d.page_content for d in docs]
    log.info(
        "Embedding %d docs in parallel (workers=%d, batch_size=%d)",
        len(docs),
        max_workers,
        embedding_batch_size,
    )
    sys.stdout.flush()
    client = get_client()
    start_embed = time.perf_counter()
    embeddings = embed_docs_parallel(
        texts,
        client,
        batch_size=embedding_batch_size,
        max_workers=max_workers,
        log=log,
        rate_limit_sleep=rate_limit_sleep,
        min_interval_sec=embed_min_interval_sec,
    )
    embed_elapsed = time.perf_counter() - start_embed
    log.info("Embedding finished in %.1fs", embed_elapsed)
    sys.stdout.flush()

    ids = list(range(len(docs)))
    dict_list = build_milvus_rows(docs, embeddings, ids=ids)

    # Add extracted metadata to each row (JSON string) when present
    for i, doc in enumerate(docs):
        meta = doc.metadata.get("extracted_metadata")
        dict_list[i]["metadata"] = json.dumps(meta) if meta else "[]"

    milvus_client = MilvusClient(uri=milvus_uri)
    if drop_collection_first:
        try:
            milvus_client.drop_collection(collection_name)
        except Exception:
            pass
    if not milvus_client.has_collection(collection_name):
        milvus_client.create_collection(
            collection_name=collection_name,
            dimension=EMBEDDING_DIM,
            metric_type="IP",
        )

    log.info("Inserting %d entities into Milvus...", len(dict_list))
    sys.stdout.flush()
    start_insert = time.perf_counter()
    res = milvus_client.insert(
        collection_name=collection_name,
        data=dict_list,
        progress_bar=True,
    )
    insert_elapsed = time.perf_counter() - start_insert
    count = res.get("insert_count", len(dict_list))
    log.info(
        "Inserted %d entities in %.2fs (embed: %.1fs total)",
        count,
        insert_elapsed,
        embed_elapsed,
    )
    sys.stdout.flush()
    return dict_list, milvus_client


def main() -> int:
    setup_logging()
    log = logging.getLogger(__name__)
    ## MILVUS_META_WORKERS=4 python run_milvus_pipeline.py --dir /path/to/txt/files
    # MILVUS_META_WORKERS=10 python run_milvus_pipeline.py --dir ../ocr_read_png/ --drop 

    ap = argparse.ArgumentParser(
        description="Build docs, embed with NVIDIA (parallel), insert into Milvus"
    )
    ap.add_argument("--dir", type=str, help="Directory of .txt files (one doc per file)")
    ap.add_argument("--collection", type=str, default="docs")
    ap.add_argument("--uri", type=str, default=DEFAULT_MILVUS_URI, help="Milvus URI (default: MILVUS_URI env or http://localhost:19530)")
    ap.add_argument("--drop", action="store_true", help="Drop collection before creating")
    ap.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Concurrent embedding workers (default: MILVUS_MAX_WORKERS=%d; use 2 to avoid 429)" % MAX_WORKERS,
    )
    ap.add_argument(
        "--batch-size",
        type=int,
        default=EMBED_BATCH_SIZE,
        help="Texts per API batch (default: MILVUS_EMBED_BATCH=%d)" % EMBED_BATCH_SIZE,
    )
    ap.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip metadata extraction (no extracted_metadata per doc)",
    )
    ap.add_argument(
        "--metadata-mode",
        type=str,
        choices=("llm", "keywords"),
        default=METADATA_MODE_DEFAULT,
        help="Metadata source: 'llm' (slow, rich) or 'keywords' (fast, ALL-CAPS from extract_capitalized_words)",
    )
    ap.add_argument(
        "--meta-workers",
        type=int,
        default=None,
        help="Concurrent metadata extraction workers (default: MILVUS_META_WORKERS=%d)" % META_WORKERS,
    )
    ap.add_argument(
        "--processed-list",
        type=str,
        default=None,
        help="Path to list of already-processed file paths (default: MILVUS_PROCESSED_LIST=%s)" % PROCESSED_LIST_PATH,
    )
    ap.add_argument(
        "--rate-limit-sleep",
        type=int,
        default=None,
        help="Seconds to sleep on 429/500 before retry (default: MILVUS_RATE_LIMIT_SLEEP=%d)" % RATE_LIMIT_SLEEP,
    )
    ap.add_argument(
        "--embed-min-interval",
        type=float,
        default=None,
        help="Min seconds between embedding batch starts (default: MILVUS_EMBED_MIN_INTERVAL_SEC=%.1f)" % EMBED_MIN_INTERVAL_SEC,
    )
    args = ap.parse_args()

    max_workers = args.workers if args.workers is not None else MAX_WORKERS
    embed_min_interval = args.embed_min_interval if args.embed_min_interval is not None else EMBED_MIN_INTERVAL_SEC
    batch_size = args.batch_size if args.batch_size is not None else EMBED_BATCH_SIZE
    meta_workers = args.meta_workers if args.meta_workers is not None else META_WORKERS
    processed_list_path = args.processed_list if args.processed_list is not None else PROCESSED_LIST_PATH
    rate_limit_sleep = args.rate_limit_sleep if args.rate_limit_sleep is not None else RATE_LIMIT_SLEEP

    if args.dir:
        processed_set = load_processed_paths(processed_list_path)
        if processed_set:
            log.info("Skipping %d already-processed paths from %s", len(processed_set), processed_list_path)
        docs, _ = documents_from_directory(Path(args.dir))
        # Only process files not in the processed list (by absolute path)
        docs = [d for d in docs if d.metadata.get("source") not in processed_set]
        if not docs:
            log.warning(
                "No documents left to process under %s (all %d already in %s)",
                args.dir,
                len(processed_set) if processed_set else 0,
                processed_list_path,
            )
            return 0
        log.info("Loaded %d documents from %s (excluding already processed)", len(docs), args.dir)
        sys.stdout.flush()
    else:
        log.info(
            "Use --dir /path/to/txt/files to run pipeline from a directory.\n"
            "For URL-based pipeline, from Python:\n"
            "  from run_milvus_pipeline import run_pipeline_parallel\n"
            "  from milvus_preprocess_pipeline import documents_from_url_text_pairs\n"
            "  docs, _ = documents_from_url_text_pairs(zip(urls, results))\n"
            "  run_pipeline_parallel(docs, collection_name='...', max_workers=8)"
        )
        return 0

    run_pipeline_parallel(
        docs,
        collection_name=args.collection,
        milvus_uri=args.uri,
        embedding_batch_size=batch_size,
        max_workers=max_workers,
        drop_collection_first=args.drop,
        extract_metadata=not args.no_metadata,
        metadata_mode=args.metadata_mode,
        meta_workers=meta_workers,
        rate_limit_sleep=rate_limit_sleep,
        embed_min_interval_sec=embed_min_interval,
        log=log,
    )
    # Record processed file paths so next run skips them
    if args.dir and docs:
        sources = [d.metadata.get("source") for d in docs if d.metadata.get("source")]
        if sources:
            append_processed_paths(processed_list_path, sources)
            log.info("Appended %d paths to %s", len(sources), processed_list_path)
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    import time
    print("Starting Milvus pipeline...")
    start_time = time.time()
    sys.exit(main())
    end_time = time.time()
    print(f"Milvus pipeline finished in {end_time - start_time} seconds")
