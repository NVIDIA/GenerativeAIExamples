# Copyright (c) 2023-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import zipfile
import io
import argparse
import json

from pathlib import Path

import jsonlines
import fitz

FILE_HOME = Path(__file__).parent


def extract_archive(archive_path, extract_path="pdf_dataset"):
    """
    Extract zip archive.

    Parameters
    ----------
    archive_path: pathlib.Path
        Path to archive.

    extract_path: pathlib.Path
        Path to extract archive.        
    """

    out_path = archive_path.parent.joinpath("dataset")

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(out_path)


def extract_text(pdf_stream):
    """
    Use PyMuPDF to extract text from a bytestream PDF.

    Parameters
    ----------
    pdf_stream : io.BytesIO
        A bytestream PDF.          

    Returns
    -------
    str
        A string of extracted text.
    """

    with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
        text_list = [page.get_text() for page in doc]

    text = "".join(text_list).replace('+', ' ')
    text = text.encode("ascii", errors="ignore").decode()

    return text


def main():

    """Generate jsonl dataset from compressed zip archive."""

    # Extract archive
    archive_path = FILE_HOME.joinpath("data", "dataset.zip")
    extracted_pdfs_path = FILE_HOME.joinpath("data", "dataset")
    extract_archive(archive_path, extract_path=extracted_pdfs_path)

    # Get all pdf paths
    paths = extracted_pdfs_path.glob('**/*')
    pdf_files = [x for x in paths if x.is_file()]

    # Generate jsonl dataset
    jsonl_output = extracted_pdfs_path.parent.joinpath("raw_sample.jsonl")

    with jsonlines.open(jsonl_output, mode='w') as jsonl_writer:

        for pdf_file in pdf_files:

            with open(pdf_file, "rb") as f:
                pdf_stream = io.BytesIO(f.read())
                extracted_text = extract_text(pdf_stream)

                extraction = {
                    "payload": extracted_text,
                    "metadata": {"callable": "raw_chunker"}
                }

                jsonl_writer.write(extraction)


if __name__ == "__main__":
    main()
