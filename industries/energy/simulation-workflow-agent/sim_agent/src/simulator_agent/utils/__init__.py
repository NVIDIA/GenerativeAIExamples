# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simulator agent utilities: paths, validators, builders, chat, plot.
"""

from .paths import (
    extract_data_file_from_sub_query,
    extract_data_files_from_sub_query,
    output_dir_from_context,
    resolve_data_path,
)
from .chat import chat_history_to_conversation, trim_chat_history
from .plot import infer_plot_metric_with_llm
from .builders import build_tool_input_for_step
from .validators import TOOL_VALIDATORS, valid_data_file_path, validate_args_and_get_update

__all__ = [
    "output_dir_from_context",
    "extract_data_file_from_sub_query",
    "extract_data_files_from_sub_query",
    "resolve_data_path",
    "trim_chat_history",
    "chat_history_to_conversation",
    "infer_plot_metric_with_llm",
    "build_tool_input_for_step",
    "valid_data_file_path",
    "validate_args_and_get_update",
    "TOOL_VALIDATORS",
]
