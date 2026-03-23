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
RAG chain: run query_milvus_with_filters (with keyword-based metadata filter),
inject retrieval output into a prompt, and return an LLM response in markdown.

Uses LangChain runnable chain (LCEL):
  retrieval (subprocess + keyword extraction) -> prompt -> LLM -> markdown response.

Requires: NVIDIA_API_KEY, Milvus running. Run from glm-ocr-vllm directory or set
GLM_OCR_VLLM_ROOT to the path containing query_milvus_with_filters.py.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from openai import OpenAI
from openai import BadRequestError as OpenAIBadRequestError

# Import keyword extraction from the same project
from extract_capitalized_words import extract_all_caps_keywords

# Directory containing query_milvus_with_filters.py (for subprocess cwd)
SCRIPT_DIR = Path(__file__).resolve().parent
if os.getenv("GLM_OCR_VLLM_ROOT"):
    SCRIPT_DIR = Path(os.environ["GLM_OCR_VLLM_ROOT"])

QUERY_SCRIPT = SCRIPT_DIR / "query_milvus_with_filters.py"

SYSTEM_PROMPT = """You are an expert assistant for the OPEN POROUS MEDIA (OPM) software manual.
Use the following retrieved context from the manual to answer the user's question.
Answer in clear, well-structured markdown. Include relevant snippets, keyword names, and source references when helpful.

<RETRIEVED_CONTEXT>
{retrieval_output}
</RETRIEVED_CONTEXT>
"""

USER_PROMPT = """User question: {query}"""

# Model: prefer env override; fallbacks used when primary returns DEGRADED (400)
DEFAULT_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
FALLBACK_MODELS = [
    "nvidia/llama-3.2-3b-instruct",
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.1-70b-instruct",
]


# Tool names (simulator-agnostic) -> Milvus collection names
TOOL_NAMES = ("simulator_manual", "simulator_examples")
TOOL_TO_COLLECTION = {
    "simulator_manual": "docs",
    "simulator_examples": "simulator_input_examples",
}
# Actual Milvus collection names (created by setup.sh --full / ingest_papers.sh)
ALLOWED_COLLECTIONS = ("docs", "simulator_input_examples")


def run_milvus_query(
    query: str,
    metadata_contains: str | None = None,
    collection_name: str = "docs",
) -> str:
    """
    Call query_milvus_with_filters.py via subprocess and return its stdout (top-5 reranked results).
    collection_name: actual Milvus collection name (docs or simulator_input_examples).
    """
    if collection_name not in ALLOWED_COLLECTIONS:
        return f"[Error: collection_name must be one of {ALLOWED_COLLECTIONS}, got {collection_name!r}]"
    if not QUERY_SCRIPT.exists():
        return f"[Error: query script not found at {QUERY_SCRIPT}]"
    cmd = [
        sys.executable,
        str(QUERY_SCRIPT),
        "--query", query,
        "--collection", collection_name,
    ]
    if metadata_contains:
        cmd.extend(["--metadata-contains", metadata_contains])
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return f"[Error: query script exited with {result.returncode}]\n{result.stderr or ''}"
        return result.stdout or ""
    except subprocess.TimeoutExpired:
        return "[Error: query script timed out]"
    except Exception as e:
        return f"[Error: {e}]"


def retrieval_step(inputs: dict) -> dict:
    """
    From user query: run Milvus query script, return query + retrieval_output.
    For simulator_manual (docs): extract ALL-CAPS keywords and pass as metadata filter.
    For simulator_examples (simulator_input_examples): no keyword extraction and no metadata filtering.
    inputs may include "collection_name" (tool name or Milvus collection); default is "simulator_manual".
    """
    query = (inputs.get("query") or "").strip()
    tool_or_collection = (inputs.get("collection_name") or "simulator_manual").strip()
    # Map tool name -> Milvus collection
    collection_name = TOOL_TO_COLLECTION.get(tool_or_collection, tool_or_collection)
    if collection_name not in ALLOWED_COLLECTIONS:
        collection_name = "docs"  # fallback to the docs collection
    if collection_name == "simulator_input_examples":
        metadata_contains = None
    else:
        keywords = extract_all_caps_keywords(query)
        metadata_contains = keywords[0] if keywords else None
    retrieval_output = run_milvus_query(
        query, metadata_contains=metadata_contains, collection_name=collection_name
    )
    return {
        "query": query,
        "retrieval_output": retrieval_output,
    }


def get_llm_client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is required")
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )


def _chat_completion(client: OpenAI, model: str, openai_messages: list[dict]) -> str:
    """Single attempt: call API and return content, or raise."""
    completion = client.chat.completions.create(
        model=model,
        messages=openai_messages,
        temperature=0.3,
        max_tokens=4096,
    )
    return (completion.choices[0].message.content or "").strip()


def _get_rag_chain_model() -> str:
    """Primary model for RAG chain: config llm.model_name, else RAG_CHAIN_MODEL env, else default."""
    try:
        from simulator_agent.config import get_config
        return get_config().get_llm_model(use_for="tool")
    except Exception:
        pass
    return os.getenv("RAG_CHAIN_MODEL", "").strip() or DEFAULT_MODEL


def llm_step(prompt_value):
    """
    Runnable that takes ChatPromptValue from the prompt template and returns LLM response content.
    On 400 DEGRADED, retries with fallback models. Uses config llm.model_name or RAG_CHAIN_MODEL env.
    """
    client = get_llm_client()
    # ChatPromptTemplate.invoke() returns ChatPromptValue with .messages
    msg_list = getattr(prompt_value, "messages", [])
    if not msg_list and hasattr(prompt_value, "__iter__"):
        msg_list = list(prompt_value)
    openai_messages = []
    for m in msg_list:
        role = m.get("role", "user") if isinstance(m, dict) else getattr(m, "type", "user")
        if role == "system":
            openai_role = "system"
        elif role == "human" or role == "user":
            openai_role = "user"
        else:
            openai_role = "assistant"
        content = m.get("content", m.get("text", "")) if isinstance(m, dict) else getattr(m, "content", "")
        openai_messages.append({"role": openai_role, "content": content or ""})
    primary = _get_rag_chain_model()
    models_to_try = [primary] + [m for m in FALLBACK_MODELS if m != primary]
    last_error = None
    for model in models_to_try:
        try:
            raw = _chat_completion(client, model, openai_messages)
            break
        except OpenAIBadRequestError as e:
            last_error = e
            err_str = str(e).upper()
            if "DEGRADED" in err_str or "400" in err_str:
                print(f"Model {model} unavailable (DEGRADED), trying fallback...", file=sys.stderr)
                continue
            raise
    else:
        raise RuntimeError(
            "All models failed (DEGRADED or 400). Set RAG_CHAIN_MODEL to a working model, e.g.:\n"
            "  export RAG_CHAIN_MODEL=nvidia/llama-3.2-3b-instruct"
        ) from last_error
    # Strip <think>...</think> so the user gets clean markdown
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    return raw


def build_chain():
    """Build LCEL chain: retrieval -> prompt -> LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])
    retrieval_runnable = RunnableLambda(retrieval_step)
    llm_runnable = RunnableLambda(llm_step)
    chain = retrieval_runnable | prompt | llm_runnable
    return chain


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="RAG chain: retrieval + LLM for simulator manual or examples")
    parser.add_argument(
        "--query", "-q", type=str, default=None,
        help="Query (default: prompt or 'show me format of COMPDAT keyword')",
    )
    parser.add_argument(
        "--collection", "-c", type=str, default="simulator_manual",
        choices=list(TOOL_NAMES) + list(ALLOWED_COLLECTIONS),
        help="Tool name (simulator_manual, simulator_examples) or Milvus collection (docs, simulator_input_examples)",
    )
    args = parser.parse_args()
    query = args.query if args.query is not None else (input("Query: ").strip() or "show me format of COMPDAT keyword")
    chain = build_chain()
    print("\nRunning retrieval and LLM...\n")
    response = chain.invoke({"query": query, "collection_name": args.collection})
    print("--- Response (markdown) ---\n")
    print(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
