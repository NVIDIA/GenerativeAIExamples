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
"""Publishes models into MLflow"""

import logging
import typing

import mrc
from mrc.core import operators as ops

from morpheus.config import Config
from morpheus.controllers.mlflow_model_writer_controller import MLFlowModelWriterController
from morpheus.messages.multi_ae_message import MultiAEMessage
from morpheus.pipeline.pass_thru_type_mixin import PassThruTypeMixin
from morpheus.pipeline.single_port_stage import SinglePortStage

# Setup conda environment
conda_env = {
    'channels': ['defaults', 'conda-forge'],
    'dependencies': ['python=3.10', 'pip'],
    'pip': ['mlflow'],
    'name': 'mlflow-env'
}

logger = logging.getLogger(f"morpheus.{__name__}")


class DFPMLFlowModelWriterStage(PassThruTypeMixin, SinglePortStage):
    """
    This stage publishes trained models into MLflow.

    Parameters
    ----------
    c : `morpheus.config.Config`
        Pipeline configuration instance.
    model_name_formatter : str, optional
        Format string to control the name of models stored in MLflow. Currently available field names are: `user_id`
        and `user_md5` which is an md5 hexadecimal digest as returned by `hash.hexdigest`.
    experiment_name_formatter : str, optional
        Format string to control the experiment name for models stored in MLflow. Currently available field names are:
        `user_id`, `user_md5` and `reg_model_name` which is the model name as defined by `model_name_formatter` once
        the field names have been applied.
    databricks_permissions : dict, optional
        When not `None` sets permissions needed when using a databricks hosted MLflow server.
    timeout : float, optional
        Timeout for get requests.
    """

    def __init__(self,
                 c: Config,
                 model_name_formatter: str = "dfp-{user_id}",
                 experiment_name_formatter: str = "/dfp-models/{reg_model_name}",
                 databricks_permissions: dict = None,
                 timeout=1.0):
        super().__init__(c)

        self._controller = MLFlowModelWriterController(model_name_formatter=model_name_formatter,
                                                       experiment_name_formatter=experiment_name_formatter,
                                                       databricks_permissions=databricks_permissions,
                                                       conda_env=conda_env,
                                                       timeout=timeout,
                                                       timestamp_column_name=c.ae.timestamp_column_name)

    @property
    def name(self) -> str:
        """Stage name"""
        return "dfp-mlflow-model-writer"

    def supports_cpp_node(self):
        """Whether this stage supports a C++ node"""
        return False

    def accepted_types(self) -> typing.Tuple:
        """Types accepted by this stage"""
        return (MultiAEMessage, )

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        node = builder.make_node(self.unique_name, ops.map(self._controller.on_data))
        builder.make_edge(input_node, node)

        return node
