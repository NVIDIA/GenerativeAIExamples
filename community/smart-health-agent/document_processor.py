
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import base64
import fitz
from io import BytesIO
from PIL import Image
import requests
from typing import List, Dict, Any, Union
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaLLM

# Ollama host configuration - can be set via environment variable or defaults to localhost
import os
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# Utility functions for image processing
def get_b64_image_from_content(image_content):
    """Convert image content to base64 encoded string."""
    img = Image.open(BytesIO(image_content))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def describe_image(image_content):
    """Generate a description of an image using Ollama."""
    try:
        image_b64 = get_b64_image_from_content(image_content)
        ollama_endpoint = f"{OLLAMA_HOST}/api/generate"
        
        payload = {
            "model": "gemma3:12b-it-q4_K_M",
            "prompt": "Describe what you see in this image in detail.",
            "images": [image_b64],
            "stream": False
        }
        
        response = requests.post(ollama_endpoint, json=payload)
        response_json = response.json()
        
        if "response" in response_json:
            return response_json["response"]
        else:
            print(f"Unexpected response format: {response_json}")
            return "Image description unavailable"
    except Exception as e:
        print(f"Error describing image: {e}")
        return "Image description unavailable"

def is_graph(image_content):
    """Determine if an image is a graph or chart."""
    try:
        res = describe_image(image_content)
        return any(keyword in res.lower() for keyword in ["graph", "plot", "chart", "table"])
    except Exception as e:
        print(f"Error checking if image is a graph: {e}")
        return False

def process_graph(image_content):
    """Process a graph image and generate a description."""
    try:
        llm = OllamaLLM(model="gemma3:12b-it-q4_K_M", temperature=0.2, base_url=OLLAMA_HOST)
        description = describe_image(image_content)
        
        # Get response from the LLM
        response = llm.invoke("Explain this chart in detail with health implications: " + description)
        return response
    except Exception as e:
        print(f"Error processing graph: {e}")
        return f"Chart or graph (Error during analysis: {str(e)})"

def extract_text_around_item(text_blocks, bbox, page_height, threshold_percentage=0.1):
    """Extract text above and below a given bounding box on a page."""
    before_text, after_text = "", ""
    vertical_threshold_distance = page_height * threshold_percentage
    
    for block in text_blocks:
        block_bbox = fitz.Rect(block[:4])
        if block_bbox.y1 < bbox.y0 and abs(block_bbox.y1 - bbox.y0) <= vertical_threshold_distance:
            before_text = block[4]
        elif block_bbox.y0 > bbox.y1 and abs(block_bbox.y0 - bbox.y1) <= vertical_threshold_distance:
            after_text = block[4]
            break
    return before_text, after_text

def process_text_blocks(text_blocks, char_count_threshold=500):
    """Group text blocks based on character count."""
    current_group = []
    grouped_blocks = []
    current_char_count = 0
    
    for block in text_blocks:
        if current_char_count + len(block[4]) <= char_count_threshold:
            current_group.append(block)
            current_char_count += len(block[4])
        else:
            if current_group:
                grouped_blocks.append((current_group[0], "\n".join([b[4] for b in current_group])))
            current_group = [block]
            current_char_count = len(block[4])
    
    if current_group:
        grouped_blocks.append((current_group[0], "\n".join([b[4] for b in current_group])))
    return grouped_blocks

def save_uploaded_file(uploaded_file):
    """Save an uploaded file temporarily."""
    temp_dir = os.path.join(os.getcwd(), "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())
    return temp_path

# Main document processing functions
def get_pdf_documents(pdf_file):
    """Process a PDF file and extract text, tables, and images."""
    all_pdf_documents = []
    ongoing_tables = {}

    try:
        f = fitz.open(stream=pdf_file.read(), filetype="pdf")
    except Exception as e:
        print(f"Error opening or processing the PDF file: {e}")
        return []

    for i in range(len(f)):
        page = f[i]
        text_blocks = [block for block in page.get_text("blocks", sort=True) 
                       if block[-1] == 0 and not (block[1] < page.rect.height * 0.1 or block[3] > page.rect.height * 0.9)]
        grouped_text_blocks = process_text_blocks(text_blocks)
        
        table_docs, table_bboxes, ongoing_tables = parse_all_tables(pdf_file.name, page, i, text_blocks, ongoing_tables)
        all_pdf_documents.extend(table_docs)

        image_docs = parse_all_images(pdf_file.name, page, i, text_blocks)
        all_pdf_documents.extend(image_docs)

        for text_block_ctr, (heading_block, content) in enumerate(grouped_text_blocks, 1):
            heading_bbox = fitz.Rect(heading_block[:4])
            if not any(heading_bbox.intersects(table_bbox) for table_bbox in table_bboxes):
                text_doc = Document(
                    page_content=f"{heading_block[4]}\\n{content}",
                    metadata={
                        "source": f"{pdf_file.name if hasattr(pdf_file, 'name') else 'unknown_pdf'}-page{i}-block{text_block_ctr}",
                        "type": "text",
                        "page_num": i,
                        "caption": "",
                        "x1": heading_block[0],
                        "y1": heading_block[1],
                        "x2": heading_block[2],
                        "x3": heading_block[3],
                        "dataframe_path": "",
                        "image_path": ""
                    }
                )
                all_pdf_documents.append(text_doc)

    f.close()
    return all_pdf_documents

def parse_all_tables(filename, page, pagenum, text_blocks, ongoing_tables):
    """Extract tables from a PDF page."""
    table_docs = []
    table_bboxes = []
    try:
        tables = page.find_tables(horizontal_strategy="lines_strict", vertical_strategy="lines_strict")
        for tab in tables:
            if not tab.header.external:
                pandas_df = tab.to_pandas()
                tablerefdir = os.path.join(os.getcwd(), "vectorstore/table_references")
                os.makedirs(tablerefdir, exist_ok=True)
                df_xlsx_path = os.path.join(tablerefdir, f"table{len(table_docs)+1}-page{pagenum}.xlsx")
                pandas_df.to_excel(df_xlsx_path)
                bbox = fitz.Rect(tab.bbox)
                table_bboxes.append(bbox)

                before_text, after_text = extract_text_around_item(text_blocks, bbox, page.rect.height)

                table_img = page.get_pixmap(clip=bbox)
                table_img_path = os.path.join(tablerefdir, f"table{len(table_docs)+1}-page{pagenum}.jpg")
                table_img.save(table_img_path)
                description = process_graph(table_img.tobytes())

                caption = before_text.replace("\n", " ") + description + after_text.replace("\n", " ")
                if before_text == "" and after_text == "":
                    caption = " ".join(tab.header.names)
                
                all_cols = ", ".join(list(pandas_df.columns.values))
                table_content = f"This is a table with the caption: {caption}\nThe columns are {all_cols}"
                
                table_metadata = {
                    "source": f"{filename[:-4] if isinstance(filename, str) else 'unknown'}-page{pagenum}-table{len(table_docs)+1}",
                    "type": "table",
                    "page_num": pagenum,
                    "caption": caption if caption else "",
                    "x1": -1.0,
                    "y1": -1.0,
                    "x2": -1.0,
                    "x3": -1.0,
                    "dataframe_path": df_xlsx_path if df_xlsx_path else "",
                    "image_path": table_img_path if table_img_path else ""
                }
                doc = Document(page_content=table_content, metadata=table_metadata)
                table_docs.append(doc)
    except Exception as e:
        print(f"Error during table extraction: {e}")
    return table_docs, table_bboxes, ongoing_tables

def parse_all_images(filename, page, pagenum, text_blocks):
    """Extract images from a PDF page."""
    image_docs = []
    image_info_list = page.get_image_info(xrefs=True)
    page_rect = page.rect

    for image_info in image_info_list:
        xref = image_info['xref']
        if xref == 0:
            continue

        img_bbox = fitz.Rect(image_info['bbox'])
        if img_bbox.width < page_rect.width / 20 or img_bbox.height < page_rect.height / 20:
            continue

        extracted_image = page.parent.extract_image(xref)
        image_data = extracted_image["image"]
        imgrefpath = os.path.join(os.getcwd(), "vectorstore/image_references")
        os.makedirs(imgrefpath, exist_ok=True)
        image_path = os.path.join(imgrefpath, f"image{xref}-page{pagenum}.png")
        with open(image_path, "wb") as img_file:
            img_file.write(image_data)

        before_text, after_text = extract_text_around_item(text_blocks, img_bbox, page.rect.height)
        if before_text == "" and after_text == "":
            continue

        image_description = " "
        if is_graph(image_data):
            image_description = process_graph(image_data)

        caption = before_text.replace("\n", " ") + image_description + after_text.replace("\n", " ")

        image_metadata = {
            "source": f"{filename[:-4] if isinstance(filename, str) else 'unknown'}-page{pagenum}-image{xref}",
            "type": "image",
            "page_num": pagenum,
            "caption": caption if caption else "",
            "x1": -1.0,
            "y1": -1.0,
            "x2": -1.0,
            "x3": -1.0,
            "dataframe_path": "",
            "image_path": image_path if image_path else ""
        }
        doc = Document(page_content=caption if caption else "Image content", metadata=image_metadata)
        image_docs.append(doc)
    return image_docs

# Primary functions for the health companion app integration
def process_health_documents(file_path, is_directory=False):
    """Process health documents from a file or directory."""
    all_docs = []
    if is_directory:
        print(f"[DOC_PROC] Processing directory: {file_path}")
        if not os.path.isdir(file_path):
            print(f"[DOC_PROC] Error: Provided path is not a directory: {file_path}")
            return []
        for filename in os.listdir(file_path):
            print(f"[DOC_PROC] Found file: {filename}")
            filepath = os.path.join(file_path, filename)
            if os.path.isfile(filepath) and filepath.lower().endswith('.pdf'):
                all_docs.extend(process_single_file(filepath))
            else:
                print(f"[DOC_PROC] Skipping non-PDF file: {filepath}")
    else:
        if os.path.isfile(file_path) and file_path.lower().endswith('.pdf'):
            print(f"[DOC_PROC] Processing single PDF file: {file_path}")
            all_docs.extend(process_single_file(file_path))
        else:
            print(f"[DOC_PROC] Error: Provided file path is not a PDF: {file_path}")

    return all_docs

def process_single_file(filepath):
    """Process a single PDF file."""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext != ".pdf":
        print(f"[DOC_PROC] Skipping non-PDF file: {filepath}")
        return []
        
    print(f"[DOC_PROC] Processing PDF file: {filepath}")

    docs = []
    try:
        with open(filepath, 'rb') as f:
            docs = get_pdf_documents(f)
        print(f"[DOC_PROC] Successfully processed PDF: {filepath}, extracted {len(docs)} documents.")
    except Exception as e:
        print(f"[DOC_PROC] Error processing PDF file {filepath}: {e}")

    return docs

def process_uploaded_files(files):
    """Process files uploaded through the Gradio interface."""
    documents = []
    for file in files:
        if hasattr(file, 'name') and file.name.lower().endswith('.pdf'):
            temp_path = save_uploaded_file(file)
            docs = process_single_file(temp_path)
            documents.extend(docs)
            # Clean up the temp file
            try:
                os.remove(temp_path)
            except:
                pass
        else:
            print(f"[DOC_PROC] Skipping non-PDF uploaded file: {file.name if hasattr(file, 'name') else 'unknown'}")
    return documents

def chunk_documents(documents, chunk_size=1000, chunk_overlap=100):
    """
    Split documents into smaller chunks for RAG.
    
    Args:
        documents: List of Document objects
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunked Document objects
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return text_splitter.split_documents(documents) 