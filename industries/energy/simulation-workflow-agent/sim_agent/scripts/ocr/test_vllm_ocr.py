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
Test that vLLM OCR instances are reachable and return OCR results.
Uses GLM-OCR API: image + text prompt (see https://docs.vllm.ai/projects/recipes/en/latest/GLM/GLM-OCR.html).

Usage:
  python test_vllm_ocr.py [--image PATH] [--url BASE_URL]
  OCR_VLLM_URLS=http://localhost:8080/v1,http://localhost:8081/v1 python test_vllm_ocr.py

Defaults: image=opm_manual_test1.png in script dir, url=first from OCR_VLLM_URLS or http://localhost:8080/v1

Inside Docker (docker compose --profile ocr): OCR_VLLM_URLS is set to http://ocr-vllm:8080/v1
by the compose file, so you can run: python scripts/ocr/test_vllm_ocr.py (no --url or env override needed).
"""
import argparse
import base64
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMAGE = os.path.join(SCRIPT_DIR, "opm_manual_test1.png")
DEFAULT_URLS = os.environ.get("OCR_VLLM_URLS", "http://localhost:8080/v1")
MODEL_NAME = os.environ.get("OCR_MODEL_NAME", "zai-org/GLM-OCR")
# GLM-OCR expects this prompt for text recognition (from vLLM docs)
PROMPT = "Text Recognition:"


def load_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("ascii")


def test_one_url(base_url: str, image_path: str) -> tuple[bool, str]:
    """Call one vLLM instance with one image. Returns (success, message)."""
    try:
        from openai import OpenAI
    except ImportError:
        return False, "openai package required: pip install openai"

    if not os.path.isfile(image_path):
        return False, f"Image not found: {image_path}"

    client = OpenAI(
        api_key="EMPTY",
        base_url=base_url.rstrip("/"),
        timeout=3600,
    )
    b64 = load_image_base64(image_path)
    data_uri = f"data:image/png;base64,{b64}"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": PROMPT},
            ],
        }
    ]
    try:
        start = time.time()
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=2048,
            temperature=0.0,
        )
        elapsed = time.time() - start
        text = (resp.choices[0].message.content or "").strip()
        return True, f"OK ({elapsed:.1f}s): {text[:200]}{'...' if len(text) > 200 else ''}"
    except Exception as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser(description="Test vLLM OCR endpoints")
    ap.add_argument("--image", default=DEFAULT_IMAGE, help="Path to PNG image")
    ap.add_argument("--url", help="Single base URL (default: first from OCR_VLLM_URLS)")
    args = ap.parse_args()

    if args.url:
        urls = [args.url.strip()]
    else:
        urls = [u.strip() for u in DEFAULT_URLS.split(",") if u.strip()]
    if not urls:
        print("No URL given. Set OCR_VLLM_URLS or use --url", file=sys.stderr)
        sys.exit(1)

    image_path = os.path.abspath(args.image)
    if not os.path.isfile(image_path):
        print(f"Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Testing {len(urls)} URL(s) with image: {image_path}")
    print(f"Prompt: {PROMPT!r}")
    all_ok = True
    for base_url in urls:
        ok, msg = test_one_url(base_url, image_path)
        status = "PASS" if ok else "FAIL"
        print(f"  {base_url} -> {status}: {msg}")
        if not ok:
            all_ok = False
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
