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
Split one large PDF into per-page PNG images using pypdfium2.
Useful for 1000+ page PDFs: each page is rendered and saved as a separate PNG.
"""
import argparse
import os
import time

import pypdfium2 as pdfium


def render_pdf_to_images(input_path, output_dir, scale=2, progress_interval=100):
    """
    Render each page of a single PDF to a PNG file.
    Saves: output_dir/<basename>_page_1.png, _page_2.png, ...
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"PDF not found: {input_path}")

    pdf = pdfium.PdfDocument(input_path)
    total_pages = len(pdf)
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_prefix = os.path.join(output_dir, base_name)

    for page_number in range(total_pages):
        page = pdf[page_number]
        pil_image = page.render(scale=scale).to_pil()
        output_path = f"{output_prefix}_page_{page_number + 1}.png"
        pil_image.save(output_path)

        if (page_number + 1) % progress_interval == 0 or page_number == total_pages - 1:
            print(f"  Page {page_number + 1}/{total_pages}")

    return total_pages


def main():
    parser = argparse.ArgumentParser(
        description="Split a large PDF into one PNG per page."
    )
    parser.add_argument(
        "--input-pdf",
        help="Path to the input PDF file (e.g. large_doc.pdf)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Directory for output PNGs. Default: <input_basename>_page_images next to the PDF",
    )
    parser.add_argument(
        "-s", "--scale",
        type=float,
        default=2,
        help="Render scale (higher = sharper, larger files). Default: 2",
    )
    parser.add_argument(
        "-p", "--progress-interval",
        type=int,
        default=100,
        help="Print progress every N pages. Default: 100",
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_pdf)
    if args.output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(input_path),
            os.path.splitext(os.path.basename(input_path))[0] + "_page_images",
        )
    else:
        output_dir = os.path.abspath(args.output_dir)

    print(f"Input:  {input_path}")
    print(f"Output: {output_dir}")
    print(f"Scale:  {args.scale}")
    t0 = time.time()
    try:
        n = render_pdf_to_images(
            input_path,
            output_dir,
            scale=args.scale,
            progress_interval=args.progress_interval,
        )
        elapsed = time.time() - t0
        print(f"Done: {n} pages -> PNG in {elapsed:.2f}s")
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
