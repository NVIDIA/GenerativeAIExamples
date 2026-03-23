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
Find and extract ALL-CAPS keywords from a text document.
Keywords are words that are entirely uppercase (and optionally digits),
e.g. SWOF, SWAT, KRW, KRO, PCWO, TABDIMS, RUNSPEC.
Ignores normal sentence words like The, Description, No.
"""

import re
import sys
from pathlib import Path


def extract_all_caps_keywords(text: str, min_length: int = 2) -> list[str]:
    """
    Extract all ALL-CAPS words (keywords) from text.
    Matches sequences of 2+ uppercase letters/digits only, e.g. SWOF, SWAT, KRW, PCWO.
    """
    pattern = rf"\b([A-Z][A-Z0-9]{{{min_length - 1},}})\b"
    return re.findall(pattern, text)


def has_all_caps_keywords(text: str) -> bool:
    """Return True if the document contains at least one ALL-CAPS keyword."""
    return bool(extract_all_caps_keywords(text))


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_capitalized_words.py <path_to_file.txt>")
        print("Example: python extract_capitalized_words.py ocr_read_png/OPM_Manual_page_1284.txt")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    text = filepath.read_text(encoding="utf-8", errors="replace")
    words = extract_all_caps_keywords(text)

    if not words:
        print("No ALL-CAPS keywords found in the document.")
        sys.exit(0)

    print(f"Found {len(words)} ALL-CAPS keyword(s) (with duplicates):")
    print(words)
    print()
    unique = list(dict.fromkeys(words))
    print(f"Unique ALL-CAPS keywords ({len(unique)}):")
    print(unique)


if __name__ == "__main__":
    main()
