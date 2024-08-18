# Copyright (c) 2024, NVIDIA CORPORATION.
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

import logging
import os
import pathlib

import nbformat
from langchain.docstore.document import Document
from langchain.document_loaders.parsers import LanguageParser
from langchain.text_splitter import Language
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain_community.document_loaders.blob_loaders.schema import Blob
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(f"__name__")


def _extract_python_code_from_ipynb(notebook_content: str, cell_type: str = "code"):
    """Extract python code from jupyter notebook

    Parameters
    ----------
    notebook_content : str
        notebook content location
    cell_type : str, optional
        _description_, by default "code"

    Returns
    -------
    str
        python codes
    """

    notebook = nbformat.read(notebook_content, as_version=nbformat.NO_CONVERT)

    python_code = []
    for cell in notebook.cells:
        if cell.cell_type == cell_type:
            python_code.append(cell.source)

    return "\n".join(python_code)


def _read_gitignore_exclusions(gitignore_file: str, base_dir: str) -> list[str]:
    exclusions = []

    # Load the gitignore file
    with open(os.path.join(base_dir, ".gitignore"), "r") as ignore_file:
        for line in ignore_file:
            # Remove any leading or trailing whitespace
            line = line.strip()

            # Ignore comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Unescape # characters
            if line[0] == '\\' and line[1] in ('#', '!'):
                line = line[1:]

            # Add the line to the list of exclusions
            if ("/" in line):
                exclusions.append(os.path.normpath(os.path.join(base_dir, line.removeprefix("/"))))
            else:
                exclusions.append(line)

    return exclusions


def create_code_embedding(code_dir: str,
                          embedding: Embeddings,
                          include: str = "**/*.py",
                          exclude: list[str] = None,
                          include_notebooks: bool = False):
    """
    Create code embedding from specified code directory.
    """
    documents: list[Document] = []
    logger.info(f"Generating embedding for source code in {code_dir}")

    # include notebooks
    if include_notebooks:

        for nb in pathlib.Path(code_dir).glob("**/[!.]*.ipynb"):
            content = _extract_python_code_from_ipynb(str(nb))
            if content:
                documents.append(Document(page_content=content, metadata={'source': nb, 'language': Language.PYTHON}))

    final_exclusions = exclude or []

    # # Load the gitignore file to pre-populate the exclude list
    # if (os.path.exists(os.path.join(code_dir, ".gitignore"))):
    #     # Load the gitignore file
    #     final_exclusions.extend(_read_gitignore_exclusions(os.path.join(code_dir, ".gitignore"), code_dir))

    code_path = pathlib.Path(code_dir)

    parser = LanguageParser(language=Language.PYTHON.value, parser_threshold=500)

    positive_matches = set(code_path.glob(include))

    for exclusion in final_exclusions:
        negative_matches = set(code_path.glob(exclusion))
        positive_matches -= negative_matches

    def build_documents(matches):

        for path in matches:

            blob = Blob.from_path(path)

            yield from parser.lazy_parse(blob)

    documents.extend(build_documents(sorted(positive_matches)))

    logger.info(f"Total {len(documents)} source code documents in {len(positive_matches)} files.")

    debug_file_path = f"{os.getenv('MORPHEUS_ROOT', '.')}/.tmp/embedding_file_list.txt"

    # Ensure the directory exists
    os.makedirs(os.path.dirname(debug_file_path), exist_ok=True)

    # Write out the list of files to disk to analyze
    with open(debug_file_path, mode="w", encoding="utf-8") as f:
        f.writelines([f".{doc.metadata['source'].removeprefix(code_dir)}\n" for doc in documents])

    python_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON,
                                                                   chunk_size=1000,
                                                                   chunk_overlap=200)
    code_documents = python_splitter.split_documents(documents)

    logger.info("Creating embeddings...")

    # create embeddings
    db = FAISS.from_documents(code_documents, embedding)

    logger.info("Creating embeddings... Complete")

    return db
