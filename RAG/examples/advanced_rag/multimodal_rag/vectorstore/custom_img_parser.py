# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import os

import cv2
import pytesseract
from langchain.docstore.document import Document

from RAG.examples.advanced_rag.multimodal_rag.vectorstore.custom_pdf_parser import (
    is_graph,
    process_graph,
    process_image,
)


def get_ocr_text(image_path, frame_num):
    img = cv2.imread(image_path)
    ocr_text = pytesseract.image_to_string(img)
    return ocr_text


def process_img_file(img_path):
    # convert to png file -> can check if this is needed
    # if 1 img -> send to NeVa and get caption + OCR needs to be performed -> save img doc in processed data
    # if giphy or gif image -> get all frames and save caption+OCR for each frame.
    processed_data = []
    ocr_text = get_ocr_text(img_path, 1)
    image_description = ""
    if is_graph(img_path):
        image_description = process_graph(img_path)
    else:
        image_description = process_image(img_path)
    caption = image_description + f"This image contains text: {ocr_text}"
    image_metadata = {
        "x1": 0,
        "y1": 0,
        "x2": 0,
        "x3": 0,
        "source": f"{os.path.basename(img_path)}",
        "image": img_path,
        "caption": caption,
        "type": "image",
        "page_num": 1,
    }
    processed_data.append(Document(page_content=caption, metadata=image_metadata))

    return processed_data
