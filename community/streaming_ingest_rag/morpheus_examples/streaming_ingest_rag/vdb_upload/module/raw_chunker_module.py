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

import logging
import os

from functools import partial

import mrc
import mrc.core.operators as ops
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import ValidationError

import cudf

from morpheus.messages import MessageMeta
from morpheus.utils.module_utils import ModuleLoaderFactory
from morpheus.utils.module_utils import register_module
from vdb_upload.schemas.raw_chunker_schema import RawChunkerSchema

logger = logging.getLogger(__name__)


RawChunkerLoaderFactory = ModuleLoaderFactory("raw_chunk", "morpheus_examples_llm", RawChunkerSchema)


def splitter(msg: MessageMeta, text_splitter, payload_column) -> MessageMeta:
    
    """
    Applies chunking strategy to raw text document. 
    Assumes each document has been preprocessed.
    """

    if (payload_column not in msg.get_column_names()):
        return None

    df = msg.copy_dataframe()

    if isinstance(df, cudf.DataFrame):
        df: pd.DataFrame = df.to_pandas()

    # Convert the dataframe into a list of dictionaries
    df_dicts = df.to_dict(orient="records")

    final_rows: list[dict] = []

    for row in df_dicts:

        split_text = text_splitter.split_text(
            row[payload_column])
        
        row["payload"] = "raw_source"

        for text in split_text:
            row_cp = row.copy()
            row_cp.update({"page_content": text})
            final_rows.append(row_cp)

    return MessageMeta(df=cudf.DataFrame(final_rows))


@register_module("raw_chunk", "morpheus_examples_llm")
def _raw_chunker(builder: mrc.Builder):
    module_config = builder.get_current_module_config()

    # Validate the module configuration using the contract
    try:
        raw_chunk_config = RawChunkerSchema(**module_config.get("raw_chunker_config", {}))
    except ValidationError as e:
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid raw chunker configuration: {error_messages}"
        logger.error(log_error_message)
        raise ValueError(log_error_message)

    payload_column = raw_chunk_config.payload_column
    chunk_size = raw_chunk_config.chunk_size

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                   chunk_overlap=chunk_size // 10,
                                                   length_function=len)


    op_func = partial(splitter, text_splitter=text_splitter, payload_column=payload_column)

    node = builder.make_node("raw_chunker", ops.map(op_func), ops.filter(lambda x: x is not None))

    builder.register_module_input("input", node)
    builder.register_module_output("output", node)
