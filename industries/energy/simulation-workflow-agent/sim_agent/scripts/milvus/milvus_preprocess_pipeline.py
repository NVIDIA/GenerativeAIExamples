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
Data preprocessing pipeline for MilvusDB:
  1. Create LangChain Document per page (from URLs or local text files)
  2. Preprocess (dedupe, clean)
  3. Generate embeddings via NVIDIA API (nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1)
  4. Build data + embedding + id + metadata and insert into Milvus

Requires: NVIDIA_API_KEY, pymilvus, langchain-core, openai
"""
from __future__ import annotations

import os
import re
import uuid
import time
from pathlib import Path
from typing import Sequence

import numpy as np
from langchain_core.documents import Document
from pymilvus import MilvusClient

from nvidia_embedding import NvidiaEmbeddingModel, EMBEDDING_DIM


# ---------- 1. Create LangChain documents per page ----------


def document_from_page(content: str, source: str, metadata: dict | None = None) -> Document:
    """Build a single LangChain Document from page text and source."""
    meta = {"source": source}
    if metadata:
        meta.update(metadata)
    return Document(page_content=content.strip(), metadata=meta)


def documents_from_url_text_pairs(
    pairs: Sequence[tuple[str, str]],
    dedupe_sources: bool = True,
    namespace: uuid.UUID | None = None,
) -> tuple[list[Document], list[uuid.UUID]]:
    """
    Create one LangChain Document per (source, text) pair.
    If dedupe_sources is True, only the first occurrence of each source is kept.

    Returns:
        (docs, ids): list of Documents and list of deterministic UUIDs per doc.
    """
    namespace = namespace or uuid.uuid4()
    seen_sources: set[str] = set()
    docs: list[Document] = []
    ids: list[uuid.UUID] = []

    for source, text in pairs:
        if isinstance(text, tuple):
            text = text[0]
        if not isinstance(text, str) or not text.strip():
            continue
        if dedupe_sources and source in seen_sources:
            continue
        if dedupe_sources:
            seen_sources.add(source)
        doc_id = uuid.uuid3(namespace, source)
        doc = document_from_page(text, source)
        docs.append(doc)
        ids.append(doc_id)
    return docs, ids


def documents_from_directory(
    directory: str | Path,
    glob: str = "**/*.txt",
    source_key: str = "file_path",
) -> tuple[list[Document], list[str]]:
    """
    Load text files from a directory into LangChain Documents (one per file).
    Returns (docs, list of source paths).
    """
    directory = Path(directory)
    docs = []
    sources = []
    for path in sorted(directory.glob(glob)):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        source = str(path.resolve())
        doc = Document(
            page_content=text.strip(),
            metadata={source_key: source, "source": source},
        )
        docs.append(doc)
        sources.append(source)
    return docs, sources


# ---------- 2. Preprocess ----------


def preprocess_text(text: str) -> str:
    """Optional cleanup: normalize whitespace, strip."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def preprocess_documents(docs: list[Document]) -> list[Document]:
    """Preprocess page_content of each document in place; returns the same list."""
    for doc in docs:
        doc.page_content = preprocess_text(doc.page_content)
    return docs


# ---------- 3. Embeddings + 4. Prepare for Milvus ----------


def build_milvus_rows(
    docs: list[Document],
    embeddings: list[np.ndarray],
    ids: Sequence[int] | None = None,
) -> list[dict]:
    """
    Build list of dicts for Milvus insert: id, chunk, source, vector.
    If ids is None, use range(len(docs)).
    """
    if ids is None:
        ids = list(range(len(docs)))
    if len(ids) != len(docs) or len(embeddings) != len(docs):
        raise ValueError("docs, embeddings, and ids length must match")
    dict_list = []
    for i, (doc, vector) in enumerate(zip(docs, embeddings)):
        chunk_dict = {
            "id": np.int64(ids[i]),
            "chunk": doc.page_content,
            "source": doc.metadata.get("source", ""),
            "vector": np.float32(vector),
        }
        dict_list.append(chunk_dict)
    return dict_list


def run_pipeline(
    docs: list[Document],
    *,
    collection_name: str = "Quantum_Docs",
    milvus_uri: str | None = None,
    embedding_batch_size: int = 32,
    drop_collection_first: bool = False,
) -> tuple[list[dict], MilvusClient]:
    """
    Run full pipeline: preprocess -> embed with NVIDIA -> build rows -> (optional) create collection and insert.

    Returns:
        (dict_list, client) so caller can insert or inspect.
    """
    if milvus_uri is None:
        milvus_uri = os.environ.get("MILVUS_URI", "http://localhost:19530")
    docs = preprocess_documents(docs)
    model = NvidiaEmbeddingModel()
    embeddings = model.get_embeddings_batch(
        [d.page_content for d in docs],
        input_type="passage",
        batch_size=embedding_batch_size,
    )
    ids = list(range(len(docs)))
    dict_list = build_milvus_rows(docs, embeddings, ids=ids)

    client = MilvusClient(uri=milvus_uri)
    if drop_collection_first:
        try:
            client.drop_collection(collection_name)
        except Exception:
            pass
    if not client.has_collection(collection_name):
        client.create_collection(
            collection_name=collection_name,
            dimension=EMBEDDING_DIM,
            metric_type="IP",
        )
    start = time.perf_counter()
    res = client.insert(
        collection_name=collection_name,
        data=dict_list,
        progress_bar=True,
    )
    elapsed = time.perf_counter() - start
    print(f"Inserted {res.get('insert_count', len(dict_list))} entities in {elapsed:.2f}s")
    return dict_list, client


# ---------- Query-time: use same embedding with input_type="query" ----------


def get_query_embedding(model: NvidiaEmbeddingModel, query: str) -> np.ndarray:
    """Embed a search query (input_type='query') for Milvus search."""
    return model.get_embeddings(query, input_type="query")
