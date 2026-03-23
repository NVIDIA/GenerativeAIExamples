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
OCR client: sends PNGs to a vLLM (OpenAI-compatible) instance.

When run by the orchestrator (run_ocr_vllm.sh), OCR_IMAGE_LIST and a single
OCR_VLLM_URLS are set so this process handles one chunk of images for one instance.

Env:
  OCR_VLLM_URLS    Base URL for this worker (single URL when used with OCR_IMAGE_LIST)
  OCR_INPUT_DIR    Directory containing *.png (used only when OCR_IMAGE_LIST is unset)
  OCR_IMAGE_LIST  Optional: path to file listing image paths (one per line) for this chunk
  OCR_OUTPUT_DIR   Directory for *.txt outputs
  OCR_MAX_WORKERS  Concurrent requests to vLLM (default: 8; increase for throughput on single instance)
  OCR_MODEL_NAME   Model name for API (default: zai-org/GLM-OCR)
  OCR_MAX_TOKENS   Max tokens per response (default: 2048)
"""
import base64
import logging
import os
import glob
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

# Config from env
DEFAULT_URLS = "http://localhost:8080/v1"
INPUT_DIR = os.environ.get("OCR_INPUT_DIR", "/home/ubuntu/output")
OUTPUT_DIR = os.environ.get("OCR_OUTPUT_DIR", "/home/ubuntu/ocr_read_png")
VLLM_URLS = [u.strip() for u in os.environ.get("OCR_VLLM_URLS", DEFAULT_URLS).split(",") if u.strip()]
# Default 8 for single-instance: more concurrent requests to maximize GPU utilization
MAX_WORKERS = int(os.environ.get("OCR_MAX_WORKERS", "8"))
MODEL_NAME = os.environ.get("OCR_MODEL_NAME", "zai-org/GLM-OCR")
MAX_TOKENS = int(os.environ.get("OCR_MAX_TOKENS", "2048"))
# GLM-OCR expects this prompt for text recognition (vLLM docs)
PROMPT = "Text Recognition:"


def load_image_base64(image_path: str) -> str:
    """Read PNG and return base64 string (no data URL prefix)."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("ascii")


def _worker_prefix() -> str:
    idx = os.environ.get("OCR_WORKER_INDEX", "")
    if idx == "":
        return ""
    try:
        return f"[Worker {int(idx) + 1}] "
    except (ValueError, TypeError):
        return ""


def wait_for_vllm_ready(base_url: str, log: logging.Logger, timeout_sec: float = 300, poll_interval: float = 5) -> bool:
    """Wait until vLLM /v1/models returns 200 (model loaded). Returns True if ready."""
    import urllib.request
    import urllib.error
    prefix = _worker_prefix()
    # base_url is already .../v1, so append /models only (avoid /v1/v1/models)
    url = f"{base_url.rstrip('/')}/models"
    deadline = time.perf_counter() + timeout_sec
    last_log = 0.0
    log.info("%sWaiting for vLLM at %s (timeout %.0fs, polling every %.0fs)", prefix, base_url, timeout_sec, poll_interval)
    sys.stdout.flush()
    while time.perf_counter() < deadline:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    log.info("%svLLM ready at %s", prefix, base_url)
                    sys.stdout.flush()
                    return True
        except Exception as e:
            now = time.perf_counter()
            if now - last_log >= 15.0:  # log every 15s while waiting
                elapsed = now - (deadline - timeout_sec)
                log.info("%sStill waiting for vLLM at %s (%.0fs elapsed): %s", prefix, base_url, elapsed, e)
                sys.stdout.flush()
                last_log = now
        time.sleep(poll_interval)
    log.error("%svLLM at %s did not become ready within %.0fs", prefix, base_url, timeout_sec)
    sys.stdout.flush()
    return False


def ocr_one_image(image_path: str, index: int, client, log: logging.Logger) -> tuple[str, str | None, str | None]:
    """
    Run OCR on one image via the vLLM API (single client for this worker).
    Returns (image_path, extracted_text or None, error_msg or None).
    """
    try:
        from openai import OpenAI
    except ImportError:
        return image_path, None, "openai package required: pip install openai"
    try:
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
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        text = (resp.choices[0].message.content or "").strip()
        return image_path, text or None, None
    except Exception as e:
        return image_path, None, str(e)


def main():
    setup_logging()
    log = logging.getLogger(__name__)
    prefix = _worker_prefix()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    image_list_file = os.environ.get("OCR_IMAGE_LIST")
    if image_list_file and os.path.isfile(image_list_file):
        with open(image_list_file, "r", encoding="utf-8") as f:
            image_paths = [line.strip() for line in f if line.strip()]
        image_paths = [p for p in image_paths if p.lower().endswith(".png")]
    else:
        pattern = os.path.join(INPUT_DIR, "*.png")
        image_paths = sorted(glob.glob(pattern))
    total = len(image_paths)

    if not image_paths:
        log.warning("%sNo images to process (OCR_IMAGE_LIST=%s or INPUT_DIR=%s)", prefix, image_list_file or "", INPUT_DIR)
        return

    log.info("%sStarted: %d images to process → %s", prefix, len(image_paths), OUTPUT_DIR)
    sys.stdout.flush()

    try:
        from openai import OpenAI
    except ImportError:
        log.error("Install openai: pip install openai")
        sys.exit(1)

    # Single client (orchestrator assigns one URL per worker). No retries: fail fast.
    if not VLLM_URLS:
        log.error("OCR_VLLM_URLS is empty")
        sys.exit(1)
    base_url = VLLM_URLS[0]
    wait_sec = float(os.environ.get("OCR_VLLM_READY_WAIT", "300"))
    if not wait_for_vllm_ready(base_url, log, timeout_sec=wait_sec):
        log.error("%sAborting: vLLM instance not ready. Start containers and wait for model load, or increase OCR_VLLM_READY_WAIT.", prefix)
        sys.stdout.flush()
        sys.exit(1)
    client = OpenAI(
        base_url=base_url,
        api_key="EMPTY",
        timeout=3600,
        max_retries=0,
    )
    log.info(
        "%sConfig: output_dir=%s total=%d url=%s max_workers=%d",
        prefix, OUTPUT_DIR, total, base_url, MAX_WORKERS,
    )
    log.info("%sStarting OCR requests...", prefix)
    sys.stdout.flush()

    completed = 0
    failed = 0
    start_all = time.perf_counter()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_path = {
            executor.submit(ocr_one_image, path, i, client, log): path
            for i, path in enumerate(image_paths)
        }
        done = 0
        for future in as_completed(future_to_path):
            image_path = future_to_path[future]
            base = os.path.splitext(os.path.basename(image_path))[0]
            try:
                _, text, err = future.result()
            except Exception as e:
                err = str(e)
                text = None
            done += 1
            if err is not None:
                failed += 1
                log.error("%s[%d/%d] FAILED %s: %s", prefix, done, total, base, err)
                continue
            out_path = os.path.join(OUTPUT_DIR, f"{base}.txt")
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text or "")
                completed += 1
                if done % 10 == 0 or done == total:
                    log.info(
                        "%s[%d/%d] Progress (%.1fs elapsed)",
                        prefix, done, total, time.perf_counter() - start_all,
                    )
                    sys.stdout.flush()
            except Exception as e:
                failed += 1
                log.error("%s[%d/%d] FAILED writing %s: %s", prefix, done, total, out_path, e)

    elapsed = time.perf_counter() - start_all
    log.info(
        "%sFinished: %d succeeded, %d failed, %d total in %.1fs",
        prefix, completed, failed, total, elapsed,
    )
    sys.stdout.flush()


if __name__ == "__main__":
    main()