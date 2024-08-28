# Copyright (c) 2022-2024, NVIDIA CORPORATION.
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
"""Postprocessing stage for Digital Fingerprinting pipeline."""

import logging
import time
import typing
from datetime import datetime

import cudf
import pandas as pd

import mrc
import numpy as np
from mrc.core import operators as ops

from morpheus.common import TypeId
from morpheus.config import Config
from morpheus.messages.multi_ae_message import MultiAEMessage
from morpheus.pipeline.pass_thru_type_mixin import PassThruTypeMixin
from morpheus.pipeline.single_port_stage import SinglePortStage
from morpheus.messages.message_base import MessageData
from morpheus.messages.message_meta import MessageMeta
from dfp.llm.nemo_retriever_client import RetrieverClient


logger = logging.getLogger(f"morpheus.{__name__}")



class DFPRAGUploadStage(PassThruTypeMixin, SinglePortStage):
    """
    This stage uploads the response column of the prior stage to a new collection in NeMo Retriever.
    The collection is used as the knowledge source for a RAG chatbot.

    Parameters
    ----------
    c : `morpheus.config.Config`
        Pipeline configuration instance.
    """

    def __init__(self, c: Config):
        super().__init__(c)
        self._needed_columns['event_time'] = TypeId.STRING

    @property
    def name(self) -> str:
        """Stage name."""
        return "dfp-rag-upload"

    def supports_cpp_node(self):
        """Whether this stage supports a C++ node."""
        return False

    def accepted_types(self) -> typing.Tuple:
        """Accepted input types."""
        return (MessageMeta, )

    def _process_events(self, message: MessageMeta): #processes a "batch" of messages, same retriever client is used for all batches since it was passed in
        # Assume that a filter stage preceedes this stage
        
        with message.mutable_dataframe() as df:
            response_list = df['response'].to_pandas().tolist()
            documents = [
                {
                    "content" : response,
                    "format" : "txt"
                } for response in response_list
            ]
        
        file_path = '/workspace/examples/digital_fingerprinting/production/morpheus/workspace/upload_intel/intel/user_summaries/3.txt'
        
        with open(file_path, 'w') as file:
            for document in documents:
                # Write the content of each document to the file
                file.write(f"{document['content']}\n\n")

        print(f"Documents have been written to {file_path}")

    
    def on_data(self, message: MessageMeta):
        """Process a message."""

        start_time = time.time()

        self._process_events(message)

        duration = (time.time() - start_time) * 1000.0

        return message

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        node = builder.make_node(self.unique_name, ops.map(self.on_data), ops.filter(lambda x: x is not None))
        builder.make_edge(input_node, node)

        return node