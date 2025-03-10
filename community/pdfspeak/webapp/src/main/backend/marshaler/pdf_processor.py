# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import fitz  # PyMuPDF
import re
from rapidfuzz import fuzz
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def preprocess_text(text):
    text = ' '.join(text.split())
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).strip()

def process_page(args):
    pdf_path, page_num, response_lines = args
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    text = page.get_text()
    text_lines = text.split("\n")
    highlights = []

    for text_line in text_lines:

        if not text_line.strip() or len(text_line.strip()) < 3:
            continue

        preprocessed_text_line = preprocess_text(text_line)
        if not preprocessed_text_line:
            continue

        for response_line in response_lines:
            if fuzz.partial_ratio(preprocessed_text_line, response_line) > 80:

                text_instances = page.search_for(text_line.strip(), quads=True)
                if text_instances:
                    highlights.extend([(page_num, inst) for inst in text_instances])
                break

    doc.close()
    return highlights


def pdf_highlighter(llm_response, pdf_path):

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    response_lines = [
        preprocess_text(line.strip()) for line in llm_response.split("\n")
        if line.strip() and len(line.strip()) > 2
    ]

    with ProcessPoolExecutor(
            max_workers=multiprocessing.cpu_count()) as executor:
        args = [(pdf_path, i, response_lines) for i in range(total_pages)]
        results = list(executor.map(process_page, args))

    all_highlights = [item for sublist in results for item in sublist]

    doc = fitz.open(pdf_path)
    for page_num, inst in all_highlights:
        page = doc[page_num]
        highlight = page.add_highlight_annot(inst)
        highlight.set_colors({"stroke": (1, 1, 0)})  # Yellow (1, 1, 0)
        highlight.update()

    highlighted_pdf_path = pdf_path.replace(".pdf", "_highlighted.pdf")
    doc.save(highlighted_pdf_path)
    doc.close()

    return highlighted_pdf_path
