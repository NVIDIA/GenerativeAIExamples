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
Download the latest OPM Flow Reference Manual automatically.

The manual is hosted on GitHub releases (same as the download on
https://opm-project.org/?page_id=955). This script fetches the latest
release via the GitHub API and downloads the compressed PDF.
"""

import json
import argparse
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# GitHub API and repo for OPM Flow manual
GITHUB_API_LATEST = "https://api.github.com/repos/OPM/opm-reference-manual/releases/latest"

SCRIPT_DIR = Path(__file__).resolve().parent


def _find_sim_root():
    """Find sim_agent root by walking up to a dir containing data/knowledge_base."""
    p = SCRIPT_DIR
    for _ in range(5):
        if (p / "data" / "knowledge_base").exists():
            return p
        p = p.parent
    return SCRIPT_DIR.parents[2]


SIM_ROOT = _find_sim_root()
DEFAULT_PAPERS_DIR = SIM_ROOT / "data" / "knowledge_base" / "papers"


def get_latest_manual_url(prefer_compressed=True):
    """
    Get the download URL for the latest OPM Flow manual from GitHub releases.

    Returns (download_url, filename) or (None, None) on failure.
    """
    req = Request(GITHUB_API_LATEST)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "OPM-Knowledge-Base-Downloader")

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        print(f"Error fetching latest release: {e}", file=sys.stderr)
        return None, None

    assets = data.get("assets") or []
    pdfs = [a for a in assets if (a.get("name") or "").lower().endswith(".pdf")]

    if not pdfs:
        print("No PDF assets found in latest release.", file=sys.stderr)
        return None, None

    # Prefer compressed version (same as the official page)
    if prefer_compressed:
        chosen = next((a for a in pdfs if "compressed" in (a.get("name") or "").lower()), None)
        if chosen is None:
            chosen = pdfs[0]
    else:
        chosen = pdfs[0]

    url = chosen.get("browser_download_url")
    name = chosen.get("name")
    if not url or not name:
        return None, None
    return url, name


def download_manual(dest_dir=None, dest_filename=None, prefer_compressed=True):
    """
    Download the latest OPM Flow manual into dest_dir.
    Returns the path to the downloaded file or None on failure.
    """
    dest_dir = Path(dest_dir) if dest_dir else DEFAULT_PAPERS_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    url, source_filename = get_latest_manual_url(prefer_compressed=prefer_compressed)
    if not url:
        return None

    out_name = dest_filename or source_filename
    out_path = dest_dir / out_name

    print(f"Downloading: {source_filename}")
    print(f"From: {url}")

    try:
        req = Request(url)
        req.add_header("User-Agent", "OPM-Knowledge-Base-Downloader")
        with urlopen(req, timeout=120) as resp:
            content = resp.read()
    except (URLError, HTTPError) as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return None

    out_path.write_bytes(content)
    print(f"Saved: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Download the latest OPM Flow Reference Manual from GitHub releases."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output path (default: data/knowledge_base/papers/ with auto filename)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: data/knowledge_base/papers)"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Knowledge base data directory (default: data/knowledge_base)"
    )
    parser.add_argument(
        "--no-compressed",
        action="store_true",
        help="Download full PDF instead of compressed"
    )
    parser.add_argument(
        "--print-url",
        action="store_true",
        help="Only print the download URL and exit"
    )
    args = parser.parse_args()

    data_dir = args.data_dir or SIM_ROOT / "data" / "knowledge_base"
    default_papers = data_dir / "papers"

    url, name = get_latest_manual_url(prefer_compressed=not args.no_compressed)
    if not url:
        return 1

    if args.print_url:
        print(url)
        return 0

    dest_dir = args.output_dir or default_papers
    dest_filename = args.output.name if args.output else None
    if args.output and args.output.parent != Path("."):
        dest_dir = args.output.parent
        dest_filename = args.output.name

    path = download_manual(
        dest_dir=dest_dir,
        dest_filename=dest_filename,
        prefer_compressed=not args.no_compressed,
    )
    return 0 if path else 1


if __name__ == "__main__":
    sys.exit(main())
