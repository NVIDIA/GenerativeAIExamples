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
"""Training stage for the DFP pipeline."""
import base64
import logging
import pickle
import typing

import mrc
from mrc.core import operators as ops
from sklearn.model_selection import train_test_split

from morpheus.config import Config
from morpheus.messages import ControlMessage
from morpheus.messages.multi_ae_message import MultiAEMessage
from morpheus.models.dfencoder import AutoEncoder
from morpheus.pipeline.single_port_stage import SinglePortStage
from morpheus.pipeline.stage_schema import StageSchema

from ..messages.multi_dfp_message import DFPMessageMeta
from ..messages.multi_dfp_message import MultiDFPMessage

logger = logging.getLogger(f"morpheus.{__name__}")


class DFPTraining(SinglePortStage):
    """
    Performs training of the DFP model using `AutoEncoder`. The trained model is then attached to output messages.

    Parameters
    ----------
    c : `morpheus.config.Config`
        Pipeline configuration instance.
    model_kwargs : dict
        Keyword arguments to pass to the `AutoEncoder` constructor.
    epochs : int
        Number of epochs to train the model for.
    validation_size : float
        Fraction of the training data to use for validation. Must be in the (0, 1) range.
    """

    def __init__(self, c: Config, model_kwargs: dict = None, epochs=30, validation_size=0.0):
        super().__init__(c)

        self._model_kwargs = {
            "encoder_layers": [512, 500],  # layers of the encoding part
            "decoder_layers": [512],  # layers of the decoding part
            "activation": 'relu',  # activation function
            "swap_probability": 0.2,  # noise parameter
            "learning_rate": 0.001,  # learning rate
            "learning_rate_decay": .99,  # learning decay
            "batch_size": 512,
            "verbose": False,
            "optimizer": 'sgd',  # SGD optimizer is selected(Stochastic gradient descent)
            "scaler": 'standard',  # feature scaling method
            "min_cats": 1,  # cut off for minority categories
            "progress_bar": False,
            "device": "cuda",
            "patience": -1,
        }

        # Update the defaults
        self._model_kwargs.update(model_kwargs if model_kwargs is not None else {})

        self._epochs = epochs

        if (0.0 <= validation_size < 1.0):
            self._validation_size = validation_size
        else:
            raise ValueError(f"validation_size={validation_size} should be a positive float in the (0, 1) range")

    @property
    def name(self) -> str:
        """Stage name."""
        return "dfp-training"

    def supports_cpp_node(self):
        """Whether this stage supports a C++ node."""
        return False

    def accepted_types(self) -> typing.Tuple:
        """Indicate which input message types this stage accepts."""
        return (
            ControlMessage,
            MultiDFPMessage,
        )

    def compute_schema(self, schema: StageSchema):
        output_type = schema.input_type
        if (output_type == MultiDFPMessage):
            output_type = MultiAEMessage
        schema.output_schema.set_type(output_type)

    def _dfp_multimessage_from_control_message(self,
                                               control_message: ControlMessage) -> typing.Union[MultiDFPMessage, None]:
        """Create a MultiDFPMessage from a ControlMessage."""
        ctrl_msg_user_id = control_message.get_metadata("user_id")
        message_meta = control_message.payload()

        if (ctrl_msg_user_id is None or message_meta is None):
            return None

        with message_meta.mutable_dataframe() as dfm:
            msg_meta_df = dfm.to_pandas()

        msg_meta = DFPMessageMeta(msg_meta_df, user_id=str(ctrl_msg_user_id))
        message = MultiDFPMessage(meta=msg_meta, mess_offset=0, mess_count=len(msg_meta_df))

        return message

    @typing.overload
    def on_data(self, message: ControlMessage) -> ControlMessage:
        ...

    @typing.overload
    def on_data(self, message: MultiDFPMessage) -> MultiAEMessage:
        ...

    def on_data(self, message):
        """Train the model and attach it to the output message."""
        received_control_message = False
        if (isinstance(message, ControlMessage)):
            message = self._dfp_multimessage_from_control_message(message)
            received_control_message = True

        if (message is None or message.mess_count == 0):
            return None

        user_id = message.user_id

        model = AutoEncoder(**self._model_kwargs)

        train_df = message.get_meta_dataframe()

        # Only train on the feature columns
        train_df = train_df[train_df.columns.intersection(self._config.ae.feature_columns)]
        validation_df = None
        run_validation = False

        # Split into training and validation sets
        if self._validation_size > 0.0:
            train_df, validation_df = train_test_split(train_df, test_size=self._validation_size, shuffle=False)
            run_validation = True

        logger.debug("Training AE model for user: '%s'...", user_id)
        model.fit(train_df, epochs=self._epochs, validation_data=validation_df, run_validation=run_validation)
        logger.debug("Training AE model for user: '%s'... Complete.", user_id)

        if (received_control_message):
            output_message = ControlMessage(message.meta)
            output_message.set_metadata("user_id", user_id)

            pickled_model_bytes = pickle.dumps(model)
            pickled_model_base64_str = base64.b64encode(pickled_model_bytes).decode('utf-8')
            output_message.set_metadata("model", pickled_model_base64_str)
        else:
            output_message = MultiAEMessage(meta=message.meta,
                                            mess_offset=message.mess_offset,
                                            mess_count=message.mess_count,
                                            model=model)

        return output_message

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        node = builder.make_node(self.unique_name, ops.map(self.on_data), ops.filter(lambda x: x is not None))
        builder.make_edge(input_node, node)

        return node
