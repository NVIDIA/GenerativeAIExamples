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

import io
import logging
import os
import typing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import wraps
from typing import Dict
from typing import List

import fitz
import fsspec
import mrc
import mrc.core.operators as ops
import pandas as pd
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pydantic import Field
from pydantic import ValidationError
from pydantic import validator

from morpheus.messages import MessageMeta
from morpheus.utils.module_utils import ModuleLoaderFactory
from morpheus.utils.module_utils import register_module


class CSVConverterSchema(BaseModel):
    chunk_overlap: int = 102  # Example default value
    chunk_size: int = 1024
    text_column_names: List[str]

    class Config:
        extra = "forbid"


class ContentExtractorSchema(BaseModel):
    batch_size: int = 32
    chunk_overlap: int = 51
    chunk_size: int = 512
    converters_meta: Dict[str, Dict] = Field(default_factory=dict)
    num_threads: int = 10

    @validator('converters_meta', pre=True, allow_reuse=True)
    def val_converters_meta(cls, to_validate: Dict[str, Dict]) -> Dict[str, Dict]:  # pylint: disable=no-self-argument
        validated_meta = {}
        for key, value in to_validate.items():
            if key.lower() == 'csv':
                validated_meta[key] = CSVConverterSchema(**value)
            else:
                validated_meta[key] = value
        return validated_meta

    class Config:
        extra = "forbid"


logger = logging.getLogger(__name__)

ContentExtractorLoaderFactory = ModuleLoaderFactory("file_content_extractor",
                                                    "morpheus_examples_llm",
                                                    ContentExtractorSchema)


@dataclass
class FileMeta:
    file_path: str
    file_name: str
    file_type: str


@dataclass
class ConverterInputInfo:
    io_bytes: io.BytesIO
    meta: dict


def get_file_meta(open_file: fsspec.core.OpenFile) -> FileMeta:
    """
    Extract file metadata from the given open file.

    Parameters
    ----------
    open_file: fsspec.core.OpenFile
        OpenFile object

    Returns
    -------
    FileMeta
        Returns FileMeta instance.
    """
    try:
        file_path = open_file.path
        file_name = os.path.basename(file_path)
        _, file_type = os.path.splitext(file_name)

        if len(file_type) > 0:
            file_type = file_type.lstrip('.')
        else:
            file_type = 'none'

        return FileMeta(file_path=file_path, file_name=file_name, file_type=file_type)

    except Exception as e:
        logger.error("Error retrieving file metadata for %s: %s", open_file.path, e)
        raise


def read_file_to_bytesio(file_path: str) -> io.BytesIO:
    """
    Read the content of the file and return it as an io.BytesIO object.

    Parameters
    ----------
    file_path: str
        Path to the file.

    Returns
    -------
    io.BytesIO or None
        Returns io.BytesIO object if the file is successfully read. Returns
        None if there is an error reading the file.
    """

    io_bytes = None

    try:
        with open(file_path, 'rb') as file:
            io_bytes = io.BytesIO(file.read())
    except FileNotFoundError:
        logger.error("Error: File not found - %s", file_path)
    except PermissionError:
        logger.error("Error: Permission denied - %s", file_path)
    except Exception as e:
        logger.error("Error reading file %s: %s", file_path, e)

    return io_bytes


def _converter_error_handler(func: typing.Callable) -> typing.Callable:

    @wraps(func)
    def wrapper(input_info: ConverterInputInfo, *args, **kwargs):
        try:
            # Common logic for instance check
            if not isinstance(input_info.io_bytes, io.BytesIO):
                raise ValueError("Invalid input type. Supported type: io.BytesIO.")

            return func(input_info, *args, **kwargs)
        except Exception as exec_info:
            logger.error("Error in %s: %s", func.__name__, exec_info)
            return func.__annotations__.get("return_type", None)()

    return wrapper


@_converter_error_handler
def _pdf_to_text_converter(input_info: ConverterInputInfo) -> str:
    text = ""
    pdf_document = fitz.open(stream=input_info.io_bytes, filetype="pdf")
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text += page.get_text()
    return text


@_converter_error_handler
def _docx_to_text_converter(input_info: ConverterInputInfo) -> str:
    text = ""
    doc = Document(io.BytesIO(input_info.io_bytes.read()))
    text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    return text


@_converter_error_handler
def _csv_to_text_converter(input_info: ConverterInputInfo) -> list[str]:
    text_arr = []
    text_column_names = set("content")
    if input_info.meta is not None:
        text_column_names = set(input_info.meta.get("csv", {}).get("text_column_names", text_column_names))
    df = pd.read_csv(input_info.io_bytes)
    if len(df.columns) == 0 or (not text_column_names.issubset(set(df.columns))):
        raise ValueError("The CSV file must either include a 'content' column or have a "
                         "columns specified in the meta configuration with key 'text_column_names'.")
    df.fillna(value='', inplace=True)
    text_arr = df[sorted(text_column_names)].apply(lambda x: ' '.join(map(str, x)), axis=1).tolist()
    return text_arr


@_converter_error_handler
def _text_converter(input_info: ConverterInputInfo) -> str:
    text = ""
    convertor_conf = input_info.meta.get("txt", {})
    encoding = convertor_conf.get("encoding", "utf-8")
    input_info.io_bytes.seek(0)
    text = input_info.io_bytes.read().decode(encoding)
    return text


def process_content(docs: str | list[str], file_meta: FileMeta, chunk_size: int, chunk_overlap: int) -> list[dict]:
    """
    Processes the content of a file and splits it into chunks.

    Parameters
    ----------
    docs : str | list[str]
        Documents content.
    file_meta: FileMeta
        FileMeta parsed information of a file path.
    chunk_size : int
        Size of each chunk.
    chunk_overlap : int
        Overlap between consecutive chunks.

    Returns
    -------
    list of dicts
        A list of dictionaries, each with a chunk of content and file metadata.
    """

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                   chunk_overlap=chunk_overlap,
                                                   length_function=len)

    processed_data = []

    if isinstance(docs, str):
        docs = [docs]

    for document in docs:
        try:
            split_text = text_splitter.split_text(document)

            for chunk in split_text:
                processed_data.append({
                    'title': file_meta.file_name,
                    'source': f"{file_meta.file_type}:{file_meta.file_path}",
                    'summary': 'none',
                    'content': chunk
                })

        except Exception as e:
            logger.error("Error processing file %s content: %s", file_meta.file_path, e)
            continue

    return processed_data


@register_module("file_content_extractor", "morpheus_examples_llm")
def file_content_extractor(builder: mrc.Builder):
    """
    Extracts text from PDF and TXT files and constructs a DataFrame with the extracted content.

    This module processes a batch of files, reading their contents and extracting text data to form a DataFrame.
    It can handle both PDF and TXT files. The module uses a ThreadPoolExecutor for parallel file reading.

    Parameters
    ----------
    builder : mrc.Builder
        The Morpheus builder instance to attach this module to.

    Notes
    -----
    The `module_config` should contain:
    - 'batch_size': int, the number of files to process in parallel.
    - 'num_threads': int, the number of threads to use for parallel file reading.
    - 'chunk_size' : int, size of each chunk of document.
    - 'chunk_overlap' : int, overlap between consecutive chunks.
    - 'converters_meta' : dict, converters configuration.

    The function reads files in parallel but processes the content serially within each batch to prevent CPU contention.

    Example `module_config`
    -----------------------
    {
        "batch_size": 32,
        "num_threads": 10
    }
    """
    module_config = builder.get_current_module_config()

    try:
        extractor_config = ContentExtractorSchema(**module_config)
    except ValidationError as e:
        # Format the error message for better readability
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid configuration for file_content_extractor: {error_messages}"
        logger.error(log_error_message)

        raise

    # Use validated configurations
    batch_size = extractor_config.batch_size
    num_threads = extractor_config.num_threads
    chunk_size = extractor_config.chunk_size
    chunk_overlap = extractor_config.chunk_overlap
    converters_meta = extractor_config.converters_meta

    converters = {
        "pdf": _pdf_to_text_converter,
        "csv": _csv_to_text_converter,
        "docx": _docx_to_text_converter,
        "txt": _text_converter
    }

    chunk_params = {
        file_type: {
            "chunk_size": converters_meta.get(file_type, {}).get("chunk_size", chunk_size),
            "chunk_overlap": converters_meta.get(file_type, {}).get("chunk_overlap", chunk_overlap)
        }
        for file_type in converters
    }

    def parse_files(open_files: typing.List[fsspec.core.OpenFile]) -> MessageMeta:
        data = []
        _fs = fsspec.filesystem(protocol='file')

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i in range(0, len(open_files), batch_size):
                batch = open_files[i:i + batch_size]
                futures = []
                files_meta = []

                for open_file in batch:
                    # Check if file exists
                    if (not _fs.exists(open_file.path)):
                        logger.warning("File does not exist: %s. Skipping...", open_file.path)
                        continue

                    if (_fs.isdir(open_file.path)):
                        logger.warning("File is a directory: %s. Skipping...", open_file.path)
                        continue

                    try:
                        file_meta: FileMeta = get_file_meta(open_file=open_file)
                        futures.append(executor.submit(read_file_to_bytesio, file_meta.file_path))
                        files_meta.append(file_meta)

                    except Exception as e:
                        logger.error("Error processing file %s: %s", open_file.path, e)

                for file_meta, future in zip(files_meta, futures):
                    io_bytes = future.result()

                    if io_bytes:
                        converter = converters.get(file_meta.file_type, _text_converter)
                        input_info = ConverterInputInfo(io_bytes=io_bytes, meta=converters_meta)
                        result = converter(input_info)
                        # Get chunk params for the file type, default to txt
                        file_type_chunk_params = chunk_params[
                            file_meta.file_type] if file_meta.file_type in chunk_params else chunk_params['txt']
                        result = process_content(result,
                                                 file_meta,
                                                 file_type_chunk_params["chunk_size"],
                                                 file_type_chunk_params["chunk_overlap"])
                        if result:
                            data.extend(result)

        df_final = pd.DataFrame(data)

        return MessageMeta(df=df_final)

    node = builder.make_node("text_extractor", ops.map(parse_files), ops.filter(lambda x: x is not None))
    builder.register_module_input("input", node)
    builder.register_module_output("output", node)