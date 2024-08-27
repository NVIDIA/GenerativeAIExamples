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
import pickle
import time

import mrc
from mrc.core import operators as ops

from morpheus.messages import ControlMessage
from morpheus.messages import MessageMeta
from morpheus.utils.column_info import process_dataframe
from morpheus.utils.module_ids import MORPHEUS_MODULE_NAMESPACE
from morpheus.utils.module_utils import register_module

from ..utils.module_ids import DFP_DATA_PREP

logger = logging.getLogger(f"morpheus.{__name__}")


@register_module(DFP_DATA_PREP, MORPHEUS_MODULE_NAMESPACE)
def dfp_data_prep(builder: mrc.Builder):
    """
    Prepare data for either inference or model training.

    Parameters
    ----------
    builder : mrc.Builder
        Pipeline builder instance.

    Notes
    ----------
        Configurable parameters:
            - schema: Schema of the data
            - timestamp_column_name: Name of the timestamp column
    """

    config = builder.get_current_module_config()

    timestamp_column_name = config.get("timestamp_column_name", "timestamp")

    if ("schema" not in config):
        raise ValueError("Data prep module requires a defined schema")

    schema_config = config["schema"]
    schema_str = schema_config["schema_str"]
    encoding = schema_config["encoding"]

    schema = pickle.loads(bytes(schema_str, encoding))

    def process_features(message: ControlMessage):

        if (message is None):
            return None

        start_time = time.time()

        # Process the columns
        payload = message.payload()
        with payload.mutable_dataframe() as dfm:
            df_processed = process_dataframe(dfm, schema)

        # Apply the new dataframe, only the rows in the offset
        message.payload(MessageMeta(df_processed))

        if logger.isEnabledFor(logging.DEBUG):
            duration = (time.time() - start_time) * 1000.0

            logger.debug("Preprocessed %s data logs in %s to %s in %s ms",
                         len(df_processed),
                         df_processed[timestamp_column_name].min(),
                         df_processed[timestamp_column_name].max(),
                         duration)

        return message

    def node_fn(obs: mrc.Observable, sub: mrc.Subscriber):
        obs.pipe(ops.map(process_features)).subscribe(sub)

    node = builder.make_node(DFP_DATA_PREP, mrc.core.operators.build(node_fn))

    builder.register_module_input("input", node)
    builder.register_module_output("output", node)
