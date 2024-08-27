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

import mrc
from mrc.core.node import Broadcast

from morpheus.utils.loader_ids import FSSPEC_LOADER
from morpheus.utils.module_ids import DATA_LOADER
from morpheus.utils.module_ids import MORPHEUS_MODULE_NAMESPACE
from morpheus.utils.module_utils import merge_dictionaries
from morpheus.utils.module_utils import register_module

from ..utils.module_ids import DFP_DEPLOYMENT
from ..utils.module_ids import DFP_INFERENCE_PIPE
from ..utils.module_ids import DFP_TRAINING_PIPE

logger = logging.getLogger(f"morpheus.{__name__}")


@register_module(DFP_DEPLOYMENT, MORPHEUS_MODULE_NAMESPACE)
def dfp_deployment(builder: mrc.Builder):
    """
    Parameters
    ----------
    builder : mrc.Builder
        Pipeline builder instance.

    Notes
    -----
    Configurable Parameters:
        - inference_options (dict): Options for the inference pipeline module; Example: See Below; Default: `[Required]`
        - training_options (dict): Options for the training pipeline module; Example: See Below; Default: `[Required]`

    Training Options Parameters:
        - batching_options (dict): Options for batching the data; Example: See Below
        - cache_dir (str): Directory to cache the rolling window data; Example: "/path/to/cache/dir"; Default: ./.cache
        - dfencoder_options (dict): Options for configuring the data frame encoder; Example: See Below
        - mlflow_writer_options (dict): Options for the MLflow model writer; Example: See Below
        - preprocessing_options (dict): Options for preprocessing the data; Example: See Below
        - stream_aggregation_options (dict): Options for aggregating the data by stream; Example: See Below
        - timestamp_column_name (str): Name of the timestamp column used in the data; Example: "my_timestamp"; Default:
        "timestamp"
        - user_splitting_options (dict): Options for splitting the data by user; Example: See Below

    Inference Options Parameters:
        - batching_options (dict): Options for batching the data; Example: See Below
        - cache_dir (str): Directory to cache the rolling window data; Example: "/path/to/cache/dir"; Default: ./.cache
        - detection_criteria (dict): Criteria for filtering detections; Example: See Below
        - fallback_username (str): User ID to use if user ID not found; Example: "generic_user"; Default: "generic_user"
        - inference_options (dict): Options for the inference module; Example: See Below
        - model_name_formatter (str): Format string for the model name; Example: "model_{timestamp}";
        Default: `[Required]`
        - num_output_ports (int): Number of output ports for the module; Example: 3
        - timestamp_column_name (str): Name of the timestamp column in the input data; Example: "timestamp";
        Default: "timestamp"
        - stream_aggregation_options (dict): Options for aggregating the data by stream; Example: See Below
        - user_splitting_options (dict): Options for splitting the data by user; Example: See Below
        - write_to_file_options (dict): Options for writing the detections to a file; Example: See Below

    batching_options:
        - end_time (datetime/str): Endtime of the time window; Example: "2023-03-14T23:59:59"; Default: None
        - iso_date_regex_pattern (str): Regex pattern for ISO date matching;
        Example: "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}"; Default: <iso_date_regex_pattern>
        - parser_kwargs (dict): Additional arguments for the parser; Example: {}; Default: {}
        - period (str): Time period for grouping files; Example: "1d"; Default: "1d"
        - sampling_rate_s (int):: Sampling rate in seconds; Example: 0; Default: None
        - start_time (datetime/string): Start time of the time window; Example: "2023-03-01T00:00:00"; Default: None

    dfencoder_options:
        - feature_columns (list): List of feature columns to train on; Example: ["column1", "column2", "column3"]
        - epochs (int): Number of epochs to train for; Example: 50
        - model_kwargs (dict): Keyword arguments to pass to the model; Example: {"encoder_layers": [64, 32],
        "decoder_layers": [32, 64], "activation": "relu", "swap_p": 0.1, "lr": 0.001, "lr_decay": 0.9,
        "batch_size": 32, "verbose": 1, "optimizer": "adam", "scalar": "min_max", "min_cats": 10,
        "progress_bar": false, "device": "cpu"}
        - validation_size (float): Size of the validation set; Example: 0.1

    mlflow_writer_options:
        - conda_env (str): Conda environment for the model; Example: `path/to/conda_env.yml`; Default: `[Required]`
        - databricks_permissions (dict): Permissions for the model; Example: See Below; Default: None
        - experiment_name_formatter (str): Formatter for the experiment name; Example: `experiment_name_{timestamp}`;
         Default: `[Required]`
        - model_name_formatter (str): Formatter for the model name; Example: `model_name_{timestamp}`;
        Default: `[Required]`
        - timestamp_column_name (str): Name of the timestamp column; Example: `timestamp`; Default: timestamp

    stream_aggregation_options:
        - cache_mode (str): The user ID to use if the user ID is not found; Example: 'batch'; Default: 'batch'
        - trigger_on_min_history (int): Minimum history to trigger a new training event; Example: 1; Default: 1
        - trigger_on_min_increment (int): Minmum increment from the last trained to new training event;
        Example: 0; Default: 0
        - timestamp_column_name (str): Name of the column containing timestamps; Example: 'timestamp';
        Default: 'timestamp'
        - aggregation_span (str): Lookback timespan for training data in a new training event; Example: '60d';
        Default: '60d'
        - cache_to_disk (bool): Whether to cache streaming data to disk; Example: false; Default: false
        - cache_dir (str): Directory to use for caching streaming data; Example: './.cache'; Default: './.cache'

    user_splitting_options:
        - fallback_username (str): The user ID to use if the user ID is not found; Example: "generic_user";
        Default: 'generic_user'
        - include_generic (bool): Whether to include a generic user ID in the output; Example: false; Default: False
        - include_individual (bool): Whether to include individual user IDs in the output; Example: true; Default: False
        - only_users (list): List of user IDs to include; others will be excluded; Example: ["user1", "user2", "user3"];
         Default: []
        - skip_users (list): List of user IDs to exclude from the output; Example: ["user4", "user5"]; Default: []
        - timestamp_column_name (str): Name of the column containing timestamps; Example: "timestamp";
        Default: 'timestamp'
        - userid_column_name (str): Name of the column containing user IDs; Example: "username"; Default: 'username'

    detection_criteria:
        - threshold (float): Threshold for filtering detections; Example: 0.5; Default: 0.5
        - field_name (str): Name of the field to filter by threshold; Example: "score"; Default: probs

    inference_options:
        - model_name_formatter (str): Formatter for model names; Example: "user_{username}_model";
        Default: `[Required]`
        - fallback_username (str): Fallback user to use if no model is found for a user; Example: "generic_user";
        Default: generic_user
        - timestamp_column_name (str): Name of the timestamp column; Example: "timestamp"; Default: timestamp

    write_to_file_options:
        - filename (str): Path to the output file; Example: `output.csv`; Default: None
        - file_type (FileTypes): Type of file to write; Example: `FileTypes.CSV`; Default: `FileTypes.Auto`
        - flush (bool): If true, flush the file after each write; Example: `false`; Default: false
        - include_index_col (bool): If true, include the index column; Example: `false`; Default: true
        - overwrite (bool): If true, overwrite the file if it exists; Example: `true`; Default: false

    monitoring_options:
        - description (str): Name to show for this Monitor Stage in the console window; Example: 'Progress';
        Default: 'Progress'
        - silence_monitors (bool): Slience the monitors on the console; Example: True; Default: False
        - smoothing (float): Smoothing parameter to determine how much the throughput should be averaged.
        0 = Instantaneous, 1 = Average.; Example: 0.01; Default: 0.05
        - unit (str): Units to show in the rate value.; Example: 'messages'; Default: 'messages'
        - delayed_start (bool): When delayed_start is enabled, the progress bar will not be shown until the first
        message is received. Otherwise, the progress bar is shown on pipeline startup and will begin timing
        immediately. In large pipelines, this option may be desired to give a more accurate timing;
        Example: True; Default: False
        - determine_count_fn_schema (str): Custom function for determining the count in a message. Gets called for
        each message. Allows for correct counting of batched and sliced messages.; Example: func_str; Default: None
        - log_level (str): Enable this stage when the configured log level is at `log_level` or lower;
        Example: 'DEBUG'; Default: INFO
    """

    #                                 MODULE_INPUT_PORT
    #                                        |
    #                                        v
    #                     +-------------------------------------+
    #                     |          fsspec_loader_module       |
    #                     +-------------------------------------+
    #                                        |
    #                                        v
    #                     +-------------------------------------+
    #                     |              broadcast              |
    #                     +-------------------------------------+
    #                               /                   \
    #                              /                     \
    #                             /                       \
    #                            v                         v
    # +-------------------------------------+      +-------------------------------------+
    # |      dfp_trianing_pipe_module       |      |       dfp_inference_pipe_module     |
    # |              (NESTED)               |      |               (NESTED)              |
    # +-------------------------------------+      +-------------------------------------+
    #                   |                                              |
    #                   v                                              v
    #          MODULE_OUTPUT_PORT_0                           MODULE_OUTPUT_PORT_1

    module_config = builder.get_current_module_config()

    num_output_ports = 2

    supported_loaders = {}
    fsspec_loader_defaults = {
        "loaders": [{
            "id": FSSPEC_LOADER
        }],
    }

    fsspec_dataloader_conf = merge_dictionaries(supported_loaders, fsspec_loader_defaults)

    dfp_training_pipe_conf = module_config["training_options"]
    dfp_inference_pipe_conf = module_config["inference_options"]

    fsspec_dataloader_module = builder.load_module(DATA_LOADER, "morpheus", "fsspec_dataloader", fsspec_dataloader_conf)
    dfp_training_pipe_module = builder.load_module(DFP_TRAINING_PIPE,
                                                   "morpheus",
                                                   "dfp_training_pipe",
                                                   dfp_training_pipe_conf)
    dfp_inference_pipe_module = builder.load_module(DFP_INFERENCE_PIPE,
                                                    "morpheus",
                                                    "dfp_inference_pipe",
                                                    dfp_inference_pipe_conf)

    # Create broadcast node to fork the pipeline.
    broadcast = Broadcast(builder, "broadcast")

    # Make an edge between modules
    builder.make_edge(fsspec_dataloader_module.output_port("output"), broadcast)
    builder.make_edge(broadcast, dfp_training_pipe_module.input_port("input"))
    builder.make_edge(broadcast, dfp_inference_pipe_module.input_port("input"))

    out_nodes = [dfp_training_pipe_module.output_port("output"), dfp_inference_pipe_module.output_port("output")]

    # Register input port for a module.
    builder.register_module_input("input", fsspec_dataloader_module.input_port("input"))

    # Register output ports for a module.
    for i in range(num_output_ports):
        # Output ports are registered in increment order.
        builder.register_module_output(f"output_{i}", out_nodes[i])
