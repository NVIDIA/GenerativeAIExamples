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

from morpheus.modules.general.monitor import MonitorLoaderFactory
from morpheus.utils.module_ids import FILTER_DETECTIONS
from morpheus.utils.module_ids import MORPHEUS_MODULE_NAMESPACE
from morpheus.utils.module_ids import SERIALIZE
from morpheus.utils.module_ids import WRITE_TO_FILE
from morpheus.utils.module_utils import merge_dictionaries
from morpheus.utils.module_utils import register_module

from ..utils.module_ids import DFP_DATA_PREP
from ..utils.module_ids import DFP_INFERENCE
from ..utils.module_ids import DFP_INFERENCE_PIPE
from ..utils.module_ids import DFP_POST_PROCESSING
from ..utils.module_ids import DFP_PREPROC
from ..utils.module_ids import DFP_ROLLING_WINDOW

logger = logging.getLogger(f"morpheus.{__name__}")


@register_module(DFP_INFERENCE_PIPE, MORPHEUS_MODULE_NAMESPACE)
def dfp_inference_pipe(builder: mrc.Builder):
    """
    This module function consolidates multiple dfp pipeline modules relevant to the inference process into a single
    module.

    Parameters
    ----------
    builder : mrc.Builder
        Pipeline builder instance.

    Notes
    ----------
        Configurable parameters:
            - batching_options (dict): Options for batching the data; Example: See Below
            - cache_dir (str): Directory to cache the rolling window data; Example: "/path/to/cache/dir";
            Default: ./.cache
            - detection_criteria (dict): Criteria for filtering detections; Example: See Below
            - fallback_username (str): User ID to use if user ID not found; Example: "generic_user";
            Default: "generic_user"
            - inference_options (dict): Options for the inference module; Example: See Below
            - model_name_formatter (str): Format string for the model name; Example: "model_{timestamp}";
            Default: `[Required]`
            - timestamp_column_name (str): Name of the timestamp column in the input data; Example: "timestamp";
            Default: "timestamp"
            - stream_aggregation_options (dict): Options for aggregating the data by stream; Example: See Below
            - user_splitting_options (dict): Options for splitting the data by user; Example: See Below
            - write_to_file_options (dict): Options for writing the detections to a file; Example: See Below
            - monitor_options (dict): Options for monitoring throughput; Example: See Below

        batching_options:
            - end_time (datetime/str): End time of the time window; Example: "2023-03-14T23:59:59"; Default: None
            - iso_date_regex_pattern (str): Regex pattern for ISO date matching;
            Example: "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}"; Default: <iso_date_regex_pattern>
            - parser_kwargs (dict): Additional arguments for the parser; Example: {}; Default: {}
            - period (str): Time period for grouping files; Example: "1d"; Default: "1d"
            - sampling_rate_s (int): Sampling rate in seconds; Example: 0; Default: None
            - start_time (datetime/str): Start time of the time window; Example: "2023-03-01T00:00:00";
            Default: None

        detection_criteria:
            - copy (bool): Whether to copy the rows or slice them; Example: true; Default: true
            - field_name (str): Name of the field to filter on; Example: `probs`; Default: probs
            - filter_source (str): Source of the filter field; Example: `AUTO`; Default: AUTO
            - schema (dict): Schema configuration; See Below; Default: -
            - threshold (float): Threshold value to filter on; Example: 0.5; Default: 0.5

            schema:
                - encoding (str): Encoding; Example: "latin1"; Default: "latin1"
                - input_message_type (str): Pickled message type; Example: `pickle_message_type`; Default: `[Required]`
                - schema_str (str): Schema string; Example: "string"; Default: `[Required]`

        inference_options:
            - model_name_formatter (str): Formatter for model names; Example: "user_{username}_model";
            Default: `[Required]`
            - fallback_username (str): Fallback user to use if no model is found for a user; Example: "generic_user";
            Default: generic_user
            - timestamp_column_name (str): Name of the timestamp column; Example: "timestamp"; Default: timestamp

        stream_aggregation_options:
            - cache_mode (str): The user ID to use if the user ID is not found; Example: 'batch'; Default: 'batch'
            - trigger_on_min_history (int): Minimum history to trigger a new training event; Example: 1; Default: 1
            - trigger_on_min_increment (int): Minimum increment from the last trained to new training event;
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
            - include_individual (bool): Whether to include individual user IDs in the output; Example: true;
            Default: False
            - only_users (list): List of user IDs to include; others will be excluded;
            Example: ["user1", "user2", "user3"];
             Default: []
            - skip_users (list): List of user IDs to exclude from the output; Example: ["user4", "user5"]; Default: []
            - timestamp_column_name (str): Name of the column containing timestamps; Example: "timestamp";
            Default: 'timestamp'
            - userid_column_name (str): Name of the column containing user IDs; Example: "username"; Default: 'username'

        monitor_options:
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
            - determine_count_fn_schema (str): Custom function for determining the count in a message. Gets called
            for each message. Allows for correct counting of batched and sliced messages.; Example: func_str;
            Default: None
            - log_level (str): Enable this stage when the configured log level is at `log_level` or lower;
            Example: 'DEBUG'; Default: INFO

        write_to_file_options:
            - filename (str): Path to the output file; Example: `output.csv`; Default: None
            - file_type (FileTypes): Type of file to write; Example: `FileTypes.CSV`; Default: `FileTypes.Auto`
            - flush (bool): If true, flush the file after each write; Example: `false`; Default: false
            - include_index_col (bool): If true, include the index column; Example: `false`; Default: true
            - overwrite (bool): If true, overwrite the file if it exists; Example: `true`; Default: false
    """

    #           MODULE_INPUT_PORT
    #                   |
    #                   v
    # +-------------------------------------+
    # |           preproc_module            |
    # |              (NESTED)               |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |      dfp_rolling_window_module      |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |         dfp_data_prep_module        |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |            monitor_module           |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |         dfp_inference_module        |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |             monitor_module          |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |        filter_detections_module     |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |        dfp_post_proc_module         |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |          serialize_module           |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |         write_to_file_module        |
    # +-------------------------------------+
    #                    |
    #                    v
    # +-------------------------------------+
    # |            monitor_module           |
    # +-------------------------------------+
    #                   |
    #                   v
    #           MODULE_OUTPUT_PORT

    config = builder.get_current_module_config()

    cache_dir = config.get("cache_dir")
    ts_column_name = config.get("timestamp_column_name")
    monitor_options = config.get("monitor_options", {})

    preproc_options = {
        "batching_options": config.get("batching_options", {}),
        "cache_dir": cache_dir,
        "monitor_options": monitor_options,
        "pre_filter_options": {
            "enable_task_filtering": True, "filter_task_type": "inference"
        },
        "timestamp_column_name": ts_column_name,
        "user_splitting_options": config.get("user_splitting_options", {}),
    }

    stream_aggregation_options = config.get("stream_aggregation_options", {})
    stream_aggregation_options = merge_dictionaries(stream_aggregation_options, {
        "cache_dir": cache_dir,
        "timestamp_column_name": ts_column_name,
    })

    data_prep_options = config.get("preprocessing_options", {})
    data_prep_options = merge_dictionaries(data_prep_options, {
        "timestamp_column_name": ts_column_name,
    })

    inference_model_options = config.get("inference_options", {})

    detection_criteria = config.get("detection_criteria", {})

    post_processing_options = {
        "timestamp_column_name": ts_column_name,
    }

    serialize_options = config.get("serialize_options", {})

    write_to_file_options = config.get("write_to_file_options", {})

    preproc_defaults = {}  # placeholder for future defaults
    preproc_conf = merge_dictionaries(preproc_options, preproc_defaults)

    stream_aggregation_defaults = {
        "cache_mode": "batch",
        "trigger_on_min_history": 1,
        "trigger_on_min_increment": 0,
    }
    dfp_rolling_window_conf = merge_dictionaries(stream_aggregation_options, stream_aggregation_defaults)

    data_prep_defaults = {}  # placeholder for future defaults
    dfp_data_prep_conf = merge_dictionaries(data_prep_options, data_prep_defaults)

    data_prep_monitor_options = {"description": "Preprocessed [inference_pipe]"}
    data_prep_monitor_module_conf = merge_dictionaries(data_prep_monitor_options, monitor_options)

    inference_model_defaults = {}  # placeholder for future defaults
    dfp_inference_conf = merge_dictionaries(inference_model_options, inference_model_defaults)

    inference_monitor_options = {"description": "Inferenced [inference_pipe]"}
    inference_monitor_module_conf = merge_dictionaries(inference_monitor_options, monitor_options)

    detection_criteria_defaults = {"field_name": "mean_abs_z", "threshold": 2.0, "filter_source": "DATAFRAME"}
    filter_detections_conf = merge_dictionaries(detection_criteria, detection_criteria_defaults)

    post_processing_defaults = {}  # placeholder for future defaults
    dfp_post_proc_conf = merge_dictionaries(post_processing_options, post_processing_defaults)

    serialize_defaults = {"exclude": ['batch_count', 'origin_hash', '_row_hash', '_batch_id'], "use_cpp": True}
    serialize_conf = merge_dictionaries(serialize_options, serialize_defaults)

    write_to_file_defaults = {
        "filename": "dfp_inference_output.csv",
    }
    write_to_file_conf = merge_dictionaries(write_to_file_options, write_to_file_defaults)

    write_to_file_monitor_options = {"description": "Saved [inference_pipe]"}
    write_to_fm_conf = merge_dictionaries(write_to_file_monitor_options, monitor_options)

    # Load modules
    preproc_module = builder.load_module(DFP_PREPROC, "morpheus", "dfp_preproc", preproc_conf)
    dfp_rolling_window_module = builder.load_module(DFP_ROLLING_WINDOW,
                                                    "morpheus",
                                                    "dfp_rolling_window",
                                                    dfp_rolling_window_conf)
    dfp_data_prep_module = builder.load_module(DFP_DATA_PREP, "morpheus", "dfp_data_prep", dfp_data_prep_conf)

    dfp_data_prep_loader = MonitorLoaderFactory.get_instance("dfp_inference_data_prep_monitor",
                                                             module_config=data_prep_monitor_module_conf)

    dfp_data_prep_monitor_module = dfp_data_prep_loader.load(builder=builder)
    dfp_inference_module = builder.load_module(DFP_INFERENCE, "morpheus", "dfp_inference", dfp_inference_conf)

    dfp_inference_monitor_loader = MonitorLoaderFactory.get_instance("dfp_inference_monitor",
                                                                     module_config=inference_monitor_module_conf)
    dfp_inference_monitor_module = dfp_inference_monitor_loader.load(builder=builder)
    filter_detections_module = builder.load_module(FILTER_DETECTIONS,
                                                   "morpheus",
                                                   "filter_detections",
                                                   filter_detections_conf)
    dfp_post_proc_module = builder.load_module(DFP_POST_PROCESSING,
                                               "morpheus",
                                               "dfp_post_processing",
                                               dfp_post_proc_conf)
    serialize_module = builder.load_module(SERIALIZE, "morpheus", "serialize", serialize_conf)
    write_to_file_module = builder.load_module(WRITE_TO_FILE, "morpheus", "write_to_file", write_to_file_conf)

    dfp_write_to_file_monitor_loader = MonitorLoaderFactory.get_instance("dfp_inference_write_to_file_monitor",
                                                                         module_config=write_to_fm_conf)
    dfp_write_to_file_monitor_module = dfp_write_to_file_monitor_loader.load(builder=builder)

    # Make an edge between the modules.
    builder.make_edge(preproc_module.output_port("output"), dfp_rolling_window_module.input_port("input"))
    builder.make_edge(dfp_rolling_window_module.output_port("output"), dfp_data_prep_module.input_port("input"))
    builder.make_edge(dfp_data_prep_module.output_port("output"), dfp_data_prep_monitor_module.input_port("input"))
    builder.make_edge(dfp_data_prep_monitor_module.output_port("output"), dfp_inference_module.input_port("input"))
    builder.make_edge(dfp_inference_module.output_port("output"), dfp_inference_monitor_module.input_port("input"))
    builder.make_edge(dfp_inference_monitor_module.output_port("output"), filter_detections_module.input_port("input"))
    builder.make_edge(filter_detections_module.output_port("output"), dfp_post_proc_module.input_port("input"))
    builder.make_edge(dfp_post_proc_module.output_port("output"), serialize_module.input_port("input"))
    builder.make_edge(serialize_module.output_port("output"), write_to_file_module.input_port("input"))
    builder.make_edge(write_to_file_module.output_port("output"), dfp_write_to_file_monitor_module.input_port("input"))

    # Register input and output port for a module.
    builder.register_module_input("input", preproc_module.input_port("input"))
    builder.register_module_output("output", dfp_write_to_file_monitor_module.output_port("output"))
