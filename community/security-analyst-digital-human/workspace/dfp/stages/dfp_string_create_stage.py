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

logger = logging.getLogger(f"morpheus.{__name__}")



class DFPStringCreateStage(PassThruTypeMixin, SinglePortStage):
    """
    Combines a user's anomalous events into a single row sampled to top_k events.

    Parameters
    ----------
    c : `morpheus.config.Config`
        Pipeline configuration instance.
    """

    def __init__(self, c: Config, top_k = 5, grouper='username', sort_key='max_abs_z'):
        super().__init__(c)
        self._needed_columns['event_time'] = TypeId.STRING
        self.top_k = top_k
        self.grouper = grouper
        self.sort_key = sort_key

    @property
    def name(self) -> str:
        """Stage name."""
        return "dfp-string-create"

    def supports_cpp_node(self):
        """Whether this stage supports a C++ node."""
        return False

    def accepted_types(self) -> typing.Tuple:
        """Accepted input types."""
        return (MessageMeta, )

    def _process_events(self, message: MessageMeta):
        # Assume that a filter stage preceedes this stage
        
        def get_top_k_events(group):
            return ' '.join(group.nlargest(self.top_k, self.sort_key)['event'])
        
        df = message._df
        df['event'] = df.apply(lambda row: str(row.to_dict()), axis=1).astype(str).str.replace(r'[^\x00-\x7F]', ' ', regex=True)
        df = df.groupby(self.grouper).apply(get_top_k_events).reset_index(name='event')
        
        return MessageMeta(df)
            
    def on_data(self, message: MessageMeta):
        """Process a message."""

        start_time = time.time()

        message = self._process_events(message)

        duration = (time.time() - start_time) * 1000.0

        return message

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        node = builder.make_node(self.unique_name, ops.map(self.on_data), ops.filter(lambda x: x is not None))
        builder.make_edge(input_node, node)

        return node