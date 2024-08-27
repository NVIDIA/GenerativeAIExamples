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

import os

from dfp.utils.dfp_arg_parser import DFPArgParser
from dfp.utils.dfp_arg_parser import pyobj2str
from dfp.utils.module_ids import DFP_DEPLOYMENT
from dfp.utils.regex_utils import iso_date_regex_pattern
from dfp.utils.schema_utils import Schema

from morpheus.cli.utils import get_package_relative_file
from morpheus.cli.utils import load_labels_file
from morpheus.config import Config
from morpheus.config import ConfigAutoEncoder
from morpheus.config import CppConfig
from morpheus.messages.multi_message import MultiMessage
from morpheus.utils.module_ids import MORPHEUS_MODULE_NAMESPACE


class ConfigGenerator:

    def __init__(self, config: Config, dfp_arg_parser: DFPArgParser, schema: Schema, encoding: str = "latin1"):
        self._config = config
        self._dfp_arg_parser = dfp_arg_parser
        self._encoding = encoding
        self._source_schema_str = pyobj2str(schema.source, encoding=encoding)
        self._preprocess_schema_str = pyobj2str(schema.preprocess, encoding=encoding)
        self._input_message_type = pyobj2str(MultiMessage, encoding)
        self._start_time_str = self._dfp_arg_parser.time_fields.start_time.isoformat()
        self._end_time_str = self._dfp_arg_parser.time_fields.end_time.isoformat()

    def get_module_conf(self):
        module_conf = {}

        module_conf["module_id"] = DFP_DEPLOYMENT
        module_conf["module_name"] = "dfp_deployment"
        module_conf["namespace"] = MORPHEUS_MODULE_NAMESPACE

        module_conf["training_options"] = self.train_module_conf()
        module_conf["inference_options"] = self.infer_module_conf()

        return module_conf

    def infer_module_conf(self):
        module_conf = {
            "num_output_ports": 2,
            "timestamp_column_name": self._config.ae.timestamp_column_name,
            "cache_dir": self._dfp_arg_parser.cache_dir,
            "batching_options": {
                "sampling_rate_s": self._dfp_arg_parser.sample_rate_s,
                "start_time": self._start_time_str,
                "end_time": self._end_time_str,
                "iso_date_regex_pattern": iso_date_regex_pattern,
                "parser_kwargs": {
                    "lines": False, "orient": "records"
                },
                "schema": {
                    "schema_str": self._source_schema_str, "encoding": self._encoding
                }
            },
            "monitor_options": {
                "silence_monitors": self._dfp_arg_parser.silence_monitors,
            },
            "user_splitting_options": {
                "fallback_username": self._config.ae.fallback_username,
                "include_generic": self._dfp_arg_parser.include_generic,
                "include_individual": self._dfp_arg_parser.include_individual,
                "only_users": self._dfp_arg_parser.only_users,
                "skip_users": self._dfp_arg_parser.skip_users,
                "userid_column_name": self._config.ae.userid_column_name
            },
            "stream_aggregation_options": {
                "aggregation_span": "1d",
                "cache_to_disk": False,
                "cache_mode": "streaming",
            },
            "preprocessing_options": {
                "schema": {
                    "schema_str": self._preprocess_schema_str, "encoding": self._encoding
                }
            },
            "inference_options": {
                "model_name_formatter": self._dfp_arg_parser.model_name_formatter,
                "fallback_username": self._config.ae.fallback_username,
                "timestamp_column_name": self._config.ae.timestamp_column_name,
            },
            "detection_criteria": {
                "schema": {
                    "input_message_type": self._input_message_type, "encoding": self._encoding
                }
            },
            "write_to_file_options": {
                "filename": f"dfp_detections_{self._dfp_arg_parser.source}.csv", "overwrite": True
            },
        }

        return module_conf

    def train_module_conf(self):
        module_conf = {
            "timestamp_column_name": self._config.ae.timestamp_column_name,
            "cache_dir": self._dfp_arg_parser.cache_dir,
            "batching_options": {
                "sampling_rate_s": self._dfp_arg_parser.sample_rate_s,
                "start_time": self._start_time_str,
                "end_time": self._end_time_str,
                "iso_date_regex_pattern": iso_date_regex_pattern,
                "parser_kwargs": {
                    "lines": False, "orient": "records"
                },
                "cache_dir": self._dfp_arg_parser.cache_dir,
                "schema": {
                    "schema_str": self._source_schema_str, "encoding": self._encoding
                }
            },
            "monitor_options": {
                "silence_monitors": self._dfp_arg_parser.silence_monitors,
            },
            "user_splitting_options": {
                "fallback_username": self._config.ae.fallback_username,
                "include_generic": self._dfp_arg_parser.include_generic,
                "include_individual": self._dfp_arg_parser.include_individual,
                "only_users": self._dfp_arg_parser.only_users,
                "skip_users": self._dfp_arg_parser.skip_users,
                "userid_column_name": self._config.ae.userid_column_name
            },
            "stream_aggregation_options": {
                "aggregation_span": "60d",
                "cache_to_disk": False,
                "cache_mode": "streaming",
                "trigger_on_min_history": 300,
                "trigger_on_min_increment": 300
            },
            "preprocessing_options": {
                "schema": {
                    "schema_str": self._preprocess_schema_str, "encoding": self._encoding
                }
            },
            "dfencoder_options": {
                "feature_columns": self._config.ae.feature_columns, "epochs": 30, "validation_size": 0.10
            },
            "mlflow_writer_options": {
                "source": self._dfp_arg_parser.source,
                "model_name_formatter": self._dfp_arg_parser.model_name_formatter,
                "experiment_name_formatter": self._dfp_arg_parser.experiment_name_formatter,
                "timestamp_column_name": self._config.ae.timestamp_column_name,
                "conda_env": {
                    'channels': ['defaults', 'conda-forge'],
                    'dependencies': ['python=3.10', 'pip'],
                    'pip': ['mlflow', 'dfencoder'],
                    'name': 'mlflow-env'
                }
            }
        }

        return module_conf


def generate_ae_config(source: str,
                       userid_column_name: str,
                       timestamp_column_name: str,
                       pipeline_batch_size: int = 0,
                       edge_buffer_size: int = 0,
                       use_cpp: bool = False,
                       num_threads: int = os.cpu_count()):
    config = Config()

    CppConfig.set_should_use_cpp(use_cpp)

    config.num_threads = num_threads

    if pipeline_batch_size > 0:
        config.pipeline_batch_size = pipeline_batch_size

    if edge_buffer_size > 0:
        config.edge_buffer_size = edge_buffer_size

    config.ae = ConfigAutoEncoder()

    labels_file = f"data/columns_ae_{source}.txt"
    config.ae.feature_columns = load_labels_file(get_package_relative_file(labels_file))
    config.ae.userid_column_name = userid_column_name
    config.ae.timestamp_column_name = timestamp_column_name

    return config
