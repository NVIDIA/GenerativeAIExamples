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

from morpheus.modules.general.monitor import MonitorLoaderFactory
from morpheus.utils.loader_ids import FILE_TO_DF_LOADER
from morpheus.utils.module_ids import DATA_LOADER
from morpheus.utils.module_ids import FILE_BATCHER
from morpheus.utils.module_ids import FILTER_CONTROL_MESSAGE
from morpheus.utils.module_ids import MORPHEUS_MODULE_NAMESPACE
from morpheus.utils.module_utils import merge_dictionaries
from morpheus.utils.module_utils import register_module

from ..utils.module_ids import DFP_PREPROC
from ..utils.module_ids import DFP_SPLIT_USERS

logger = logging.getLogger(f"morpheus.{__name__}")


@register_module(DFP_PREPROC, MORPHEUS_MODULE_NAMESPACE)
def dfp_preproc(builder: mrc.Builder):
    """
    This module function consolidates multiple dfp pipeline modules related to inference/training
    process into a single module.

    Parameters
    ----------
    builder : mrc.Builder
        Pipeline builder instance.

    Notes
    ----------
        Configurable parameters:
            - cache_dir (str): Directory for caching intermediate results
            - timestamp_column_name (str): Name of the column containing timestamps
            - pre_filter_options (dict): Options for pre-filtering control messages
            - batching_options (dict): Options for batching files
            - user_splitting_options (dict): Options for splitting data by user
            - supported_loaders (dict): Supported data loaders for different file types
            - monitor_options (dict): Options for monitoring throughput
    """

    #        MODULE_INPUT_PORT
    #                |
    #                v
    # +-------------------------------+
    # | filter_control_message_module |
    # +-------------------------------+
    #                |
    #                v
    # +-------------------------------+
    # |      file_batcher_module      |
    # +-------------------------------+
    #                |
    #                v
    # +-------------------------------+
    # | file_to_df_dataloader_module  |
    # +-------------------------------+
    #                |
    #                v
    # +-------------------------------+
    # |       monitor_module          |
    # +-------------------------------+
    #                |
    #                v
    # +-------------------------------+
    # |    dfp_split_users_module     |
    # +-------------------------------+
    #                |
    #                v
    # +-------------------------------+
    # |       monitor_module          |
    # +-------------------------------+
    #                |
    #                v
    #        MODULE_OUTPUT_PORT

    config = builder.get_current_module_config()

    cache_dir = config.get("cache_dir", None)
    ts_column_name = config.get("timestamp_column_name", None)

    monitor_options = config.get("monitor_options", {})
    pre_filter_options = config.get("pre_filter_options", {})
    task_type = pre_filter_options.get("filter_task_type")

    batching_opts = config.get("batching_options", {})
    batching_opts["cache_dir"] = cache_dir
    batching_opts["timestamp_column_name"] = ts_column_name

    splitting_opts = config.get("user_splitting_options", {})
    splitting_opts["cache_dir"] = cache_dir
    splitting_opts["timestamp_col_name"] = ts_column_name

    supported_loaders = config.get("supported_loaders", {})

    file_to_df_monitor_default = {"description": f"FileToDF [{task_type}_pipe]"}
    file_to_df_monitor_conf = merge_dictionaries(monitor_options, file_to_df_monitor_default)

    pre_filter_default = {}
    pre_filter_conf = merge_dictionaries(pre_filter_options, pre_filter_default)

    # Double check on how 'batcher_config' is used in the file_batcher module.
    batching_opts_default = {
        "file_type": "JSON",
        "filter_null": True,
        "parser_kwargs": {
            "lines": False, "orient": "records"
        },
    }
    file_batcher_conf = merge_dictionaries(batching_opts, batching_opts_default)

    file_to_df_defaults = {
        "loaders": [{
            "id": FILE_TO_DF_LOADER
        }],
    }
    file_to_df_conf = merge_dictionaries(supported_loaders, file_to_df_defaults)

    dfp_split_users_default = {"fallback_username": config.get("fallback_username", "generic_user")}
    dfp_split_users_conf = merge_dictionaries(splitting_opts, dfp_split_users_default)

    dfp_split_users_monitor_default = {"description": f"SplitUsers [{task_type}_pipe]"}
    dfp_split_users_monitor_conf = merge_dictionaries(monitor_options, dfp_split_users_monitor_default)

    filter_control_message_module = builder.load_module(FILTER_CONTROL_MESSAGE,
                                                        "morpheus",
                                                        "filter_control_message",
                                                        pre_filter_conf)
    file_batcher_module = builder.load_module(FILE_BATCHER, "morpheus", "file_batcher", file_batcher_conf)
    file_to_df_dataloader_module = builder.load_module(DATA_LOADER,
                                                       "morpheus",
                                                       "dfp_file_to_df_dataloader",
                                                       file_to_df_conf)

    file_to_df_monitor_loader = MonitorLoaderFactory.get_instance("file_to_df_monitor_loader",
                                                                  module_config=file_to_df_monitor_conf)
    file_to_df_monitor_module = file_to_df_monitor_loader.load(builder=builder)
    dfp_split_users_module = builder.load_module(DFP_SPLIT_USERS, "morpheus", "dfp_split_users", dfp_split_users_conf)

    dfp_split_users_monitor_loader = MonitorLoaderFactory.get_instance("dfp_split_users_monitor_loader",
                                                                       module_config=dfp_split_users_monitor_conf)
    dfp_split_users_monitor_module = dfp_split_users_monitor_loader.load(builder=builder)

    # Make an edge between the modules.
    builder.make_edge(filter_control_message_module.output_port("output"), file_batcher_module.input_port("input"))
    builder.make_edge(file_batcher_module.output_port("output"), file_to_df_dataloader_module.input_port("input"))
    builder.make_edge(file_to_df_dataloader_module.output_port("output"), file_to_df_monitor_module.input_port("input"))
    builder.make_edge(file_to_df_monitor_module.output_port("output"), dfp_split_users_module.input_port("input"))
    builder.make_edge(dfp_split_users_module.output_port("output"), dfp_split_users_monitor_module.input_port("input"))

    # Register input and output port for a module.
    builder.register_module_input("input", filter_control_message_module.input_port("input"))
    builder.register_module_output("output", dfp_split_users_monitor_module.output_port("output"))
