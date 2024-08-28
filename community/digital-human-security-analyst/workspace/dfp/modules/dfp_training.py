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

import mrc
from mrc.core import operators as ops
from sklearn.model_selection import train_test_split

import cudf

from morpheus.messages import ControlMessage
from morpheus.messages.multi_ae_message import MultiAEMessage
from morpheus.models.dfencoder import AutoEncoder
from morpheus.utils.module_ids import MORPHEUS_MODULE_NAMESPACE
from morpheus.utils.module_utils import register_module

from ..messages.multi_dfp_message import DFPMessageMeta
from ..messages.multi_dfp_message import MultiDFPMessage
from ..utils.module_ids import DFP_TRAINING

logger = logging.getLogger(f"morpheus.{__name__}")


@register_module(DFP_TRAINING, MORPHEUS_MODULE_NAMESPACE)
def dfp_training(builder: mrc.Builder):
    """
    This module function is used for model training.

    Parameters
    ----------
    builder : mrc.Builder
        Pipeline builder instance.

    Notes
    -----
        Configurable Parameters:
            - feature_columns (list): List of feature columns to train on; Example: ["column1", "column2", "column3"]
            - epochs (int): Number of epochs to train for; Example: 50
            - model_kwargs (dict): Keyword arguments to pass to the model; Example: {"encoder_layers": [64, 32],
            "decoder_layers": [32, 64], "activation": "relu", "swap_p": 0.1, "lr": 0.001, "lr_decay": 0.9,
            "batch_size": 32, "verbose": 1, "optimizer": "adam", "scalar": "min_max", "min_cats": 10,
            "progress_bar": false, "device": "cpu"}
            - validation_size (float): Size of the validation set; Example: 0.1
    """

    config = builder.get_current_module_config()

    if ("feature_columns" not in config):
        raise ValueError("Training module requires feature_columns to be configured")

    epochs = config.get("epochs", 1)
    feature_columns = config["feature_columns"]
    model_kwargs = config.get("model_kwargs", {})
    validation_size = config.get("validation_size", 0.0)

    if (validation_size < 0.0 or validation_size > 1.0):
        raise ValueError(f"validation_size={validation_size} should be a positive float in the "
                         "(0, 1) range")

    def on_data(control_message: ControlMessage):
        if (control_message is None):
            return None

        output_messages = []
        while (control_message.has_task("training")):
            control_message.remove_task("training")

            user_id = control_message.get_metadata("user_id")
            message_meta = control_message.payload()

            with message_meta.mutable_dataframe() as dfm:
                final_df = dfm.to_pandas()

            model = AutoEncoder(**model_kwargs)

            # Only train on the feature columns
            train_df = final_df[final_df.columns.intersection(feature_columns)]

            validation_df = None
            run_validation = False

            # Split into training and validation sets
            if validation_size > 0.0:
                train_df, validation_df = train_test_split(train_df, test_size=validation_size, shuffle=False)
                run_validation = True

            logger.debug("Training AE model for user: '%s'...", user_id)
            model.fit(train_df, epochs=epochs, validation_data=validation_df, run_validation=run_validation)
            logger.debug("Training AE model for user: '%s'... Complete.", user_id)

            dfp_mm = DFPMessageMeta(cudf.from_pandas(final_df), user_id=user_id)
            multi_message = MultiDFPMessage(meta=dfp_mm, mess_offset=0, mess_count=len(final_df))
            output_message = MultiAEMessage(meta=multi_message.meta,
                                            mess_offset=multi_message.mess_offset,
                                            mess_count=multi_message.mess_count,
                                            model=model,
                                            train_scores_mean=0.0,
                                            train_scores_std=1.0)

            output_messages.append(output_message)

        return output_messages

    def node_fn(obs: mrc.Observable, sub: mrc.Subscriber):
        obs.pipe(ops.map(on_data), ops.flatten(), ops.filter(lambda x: x is not None)).subscribe(sub)

    node = builder.make_node(DFP_TRAINING, mrc.core.operators.build(node_fn))

    builder.register_module_input("input", node)
    builder.register_module_output("output", node)
