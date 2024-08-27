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

import mrc
from dfp.utils.model_cache import ModelCache
from dfp.utils.model_cache import ModelManager
from mlflow.tracking.client import MlflowClient
from mrc.core import operators as ops

import cudf

from morpheus.messages import ControlMessage
from morpheus.utils.module_ids import MORPHEUS_MODULE_NAMESPACE
from morpheus.utils.module_utils import register_module

from ..messages.multi_dfp_message import DFPMessageMeta
from ..messages.multi_dfp_message import MultiDFPMessage
from ..utils.module_ids import DFP_INFERENCE

logger = logging.getLogger(f"morpheus.{__name__}")


@register_module(DFP_INFERENCE, MORPHEUS_MODULE_NAMESPACE)
def dfp_inference(builder: mrc.Builder):
    """
    Inference module function.

    Parameters
    ----------
    builder : mrc.Builder
        Pipeline builder instance.

    Notes
    ----------
        Configurable parameters:
            - model_name_formatter (str): Formatter for model names; Example: "user_{username}_model";
            Default: `[Required]`
            - fallback_username (str): Fallback user to use if no model is found for a user; Example: "generic_user";
            Default: generic_user
            - timestamp_column_name (str): Name of the timestamp column; Example: "timestamp"; Default: timestamp
    """

    config = builder.get_current_module_config()

    if ("model_name_formatter" not in config):
        raise ValueError("Inference module requires model_name_formatter to be configured")

    if ("fallback_username" not in config):
        raise ValueError("Inference module requires fallback_username to be configured")

    model_name_formatter = config.get("model_name_formatter", None)
    fallback_user = config.get("fallback_username", "generic_user")
    model_fetch_timeout = config.get("model_fetch_timeout", 1.0)
    timestamp_column_name = config.get("timestamp_column_name", "timestamp")

    client = MlflowClient()

    model_manager = None

    def get_model(user: str) -> ModelCache:
        nonlocal model_manager

        if not model_manager:
            model_manager = ModelManager(model_name_formatter=model_name_formatter)

        return model_manager.load_user_model(client,
                                             user_id=user,
                                             fallback_user_ids=[fallback_user],
                                             timeout=model_fetch_timeout)

    def process_task(control_message: ControlMessage):
        start_time = time.time()

        user_id = control_message.get_metadata("user_id")
        payload = control_message.payload()

        with payload.mutable_dataframe() as dfm:
            df_user = dfm.to_pandas()

        try:
            model_cache: ModelCache = get_model(user_id)

            if (model_cache is None):
                raise RuntimeError(f"Could not find model for user {user_id}")

            loaded_model = model_cache.load_model(client)

        # TODO(Devin): Recovery strategy should be more robust/configurable in practice
        except Exception as exec_info:
            logger.exception("Error retrieving model for user %s, discarding training message. %s", user_id, exec_info)
            return None

        post_model_time = time.time()

        results_df = cudf.from_pandas(loaded_model.get_results(df_user, return_abs=True))

        results_cols = list(set(results_df.columns) - set(df_user.columns))

        output_df = cudf.concat([payload.df, results_df[results_cols]], axis=1)

        # Create an output message to allow setting meta
        output_message = MultiDFPMessage(meta=DFPMessageMeta(output_df, user_id=user_id),
                                         mess_offset=0,
                                         mess_count=payload.count)

        output_message.set_meta('model_version', f"{model_cache.reg_model_name}:{model_cache.reg_model_version}")

        if logger.isEnabledFor(logging.DEBUG):
            load_model_duration = (post_model_time - start_time) * 1000.0
            get_anomaly_duration = (time.time() - post_model_time) * 1000.0

            logger.debug("Completed inference for user %s. Model load: %s ms, Model infer: %s ms. Start: %s, End: %s",
                         user_id,
                         load_model_duration,
                         get_anomaly_duration,
                         df_user[timestamp_column_name].min(),
                         df_user[timestamp_column_name].max())

        return output_message

    def on_data(control_message: ControlMessage):
        if (control_message is None):
            return None

        task_results = []
        while (control_message.has_task("inference")):
            task_results.append(process_task(control_message))
            # After the inference task is completed, we remove it from the control messages.
            control_message.remove_task("inference")
            logger.debug("Removed inference task from the control message")

        return task_results

    def node_fn(obs: mrc.Observable, sub: mrc.Subscriber):
        obs.pipe(ops.map(on_data), ops.flatten()).subscribe(sub)

    node = builder.make_node(DFP_INFERENCE, mrc.core.operators.build(node_fn))

    builder.register_module_input("input", node)
    builder.register_module_output("output", node)
