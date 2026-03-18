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
Download the OPM datasets repository (opm-data) from GitHub.

Contains test cases and example DATA files (e.g. spe1, spe3, norne).
See: https://github.com/OPM/opm-data

Downloads the default branch as a zip and extracts it (no git required).
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import zipfile

# GitHub repo and default branch (opm-data uses master)
OPM_DATA_REPO = "OPM/opm-data"
DEFAULT_BRANCH = "master"

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
DEFAULT_DEST = SIM_ROOT / "data" / "knowledge_base" / "repos" / "opm-data"


def download_opm_data(dest_dir=None, branch=DEFAULT_BRANCH, skip_existing=False):
    """
    Download opm-data from GitHub and extract into dest_dir.

    Returns the path to the extracted repo root, or None on failure.
    """
    dest_dir = Path(dest_dir) if dest_dir else DEFAULT_DEST

    if dest_dir.exists() and skip_existing:
        print(f"✓ Destination already exists (--skip-existing): {dest_dir}")
        return dest_dir

    zip_url = f"https://github.com/{OPM_DATA_REPO}/archive/refs/heads/{branch}.zip"
    print(f"Downloading: {zip_url}")

    try:
        req = Request(zip_url)
        req.add_header("User-Agent", "OPM-Knowledge-Base-Downloader")
        with urlopen(req, timeout=120) as resp:
            zip_content = resp.read()
    except (URLError, HTTPError) as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return None

    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "opm-data.zip"
        zip_path.write_bytes(zip_content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            # Archive has one top-level dir: opm-data-<branch>
            names = zf.namelist()
            if not names:
                print("Empty archive.", file=sys.stderr)
                return None
            top = names[0].split("/")[0]
            zf.extractall(tmpdir)

        extracted = Path(tmpdir) / top
        if not extracted.is_dir():
            print(f"Unexpected archive layout: {top}", file=sys.stderr)
            return None

        shutil.move(str(extracted), str(dest_dir))

    print(f"Saved: {dest_dir}")
    return dest_dir


def main():
    parser = argparse.ArgumentParser(
        description="Download the OPM opm-data repository (datasets and example DATA files)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=None,
        help="Directory to extract into (default: data/knowledge_base/repos/opm-data)"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Knowledge base data directory (default: data/knowledge_base)"
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Branch to download (default: {DEFAULT_BRANCH})"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Do nothing if output directory already exists"
    )
    parser.add_argument(
        "--print-url",
        action="store_true",
        help="Only print the zip URL and exit"
    )
    args = parser.parse_args()

    data_dir = args.data_dir or SIM_ROOT / "data" / "knowledge_base"
    default_dest = data_dir / "repos" / "opm-data"
    dest_dir = args.output_dir or default_dest

    if args.print_url:
        print(f"https://github.com/{OPM_DATA_REPO}/archive/refs/heads/{args.branch}.zip")
        return 0

    path = download_opm_data(
        dest_dir=dest_dir,
        branch=args.branch,
        skip_existing=args.skip_existing,
    )
    return 0 if path else 1


if __name__ == "__main__":
    sys.exit(main())
