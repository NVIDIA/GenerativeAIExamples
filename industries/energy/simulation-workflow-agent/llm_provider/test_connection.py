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

"""Run from repo root: python -m llm_provider.test_connection"""
import os
import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))


def main():
    from llm_provider import ChatOpenAI
    from langchain_core.messages import HumanMessage

    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("NVIDIA_API_KEY is not set. Set it to test the live connection.")
        print("Running initialization and message-format checks only.\n")

    print("Testing ChatOpenAI LLM provider connection")
    print("=" * 50)

    print("1. Initializing ChatOpenAI...")
    llm = ChatOpenAI(
        model="nvidia/llama-3.3-nemotron-super-49b-v1.5",
        max_tokens=64,
        temperature=0.1,
    )
    print("   OK: Client initialized")

    if not api_key:
        print("\nSkipping live invoke (no API key).")
        return 0

    print("\n2. Sending test request to API...")
    try:
        response = llm.invoke([HumanMessage(content="Reply with exactly: OK")])
        content = (response.content or "").strip()
        print(f"   OK: Got response ({len(content)} chars)")
        print(f"   Content: {content[:200]}")
        return 0
    except Exception as e:
        print(f"   FAIL: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
