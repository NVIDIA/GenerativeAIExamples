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

import logging
import time
import typing

import mrc
from mrc.core import operators as ops

from morpheus.config import Config
from morpheus.pipeline.pass_thru_type_mixin import PassThruTypeMixin
from morpheus.pipeline.single_port_stage import SinglePortStage
from morpheus.utils.column_info import DataFrameInputSchema
from morpheus.utils.column_info import process_dataframe

from ..messages.multi_dfp_message import MultiDFPMessage

logger = logging.getLogger("morpheus.{__name__}")


class DFPPreprocessingStage(PassThruTypeMixin, SinglePortStage):
    """
    This stage performs preprocessing on incoming DataFrame as defined by `input_schema` before training or inference.

    Parameters
    ----------
    config : `morpheus.config.Config`
        Pipeline configuration instance.
    input_schema : `morpheus.utils.column_info.DataFrameInputSchema`
        Input schema for the DataFrame.
    """

    def __init__(self, config: Config, input_schema: DataFrameInputSchema):
        super().__init__(config)

        self._input_schema = input_schema

    @property
    def name(self) -> str:
        return "dfp-preproc"

    def supports_cpp_node(self):
        return False

    def accepted_types(self) -> typing.Tuple:
        return (MultiDFPMessage, )

    def process_features(self, message: MultiDFPMessage):
        if (message is None):
            return None

        start_time = time.time()

        # Process the columns
        df_processed = process_dataframe(message.get_meta_dataframe(), self._input_schema)

        # Apply the new dataframe, only the rows in the offset
        message.set_meta_dataframe(list(df_processed.columns), df_processed)

        if logger.isEnabledFor(logging.DEBUG):
            duration = (time.time() - start_time) * 1000.0

            logger.debug("Preprocessed %s data for logs in %s to %s in %s ms",
                         message.mess_count,
                         message.get_meta(self._config.ae.timestamp_column_name).min(),
                         message.get_meta(self._config.ae.timestamp_column_name).max(),
                         duration)

        return message

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        node = builder.make_node(self.unique_name, ops.map(self.process_features))
        builder.make_edge(input_node, node)

        # node.launch_options.pe_count = self._config.num_threads

        return node
