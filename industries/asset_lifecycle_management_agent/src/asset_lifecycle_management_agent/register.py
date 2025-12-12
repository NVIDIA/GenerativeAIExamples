# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# pylint: disable=unused-import
# flake8: noqa

# Import any tools which need to be automatically registered here
from .retrievers import generate_sql_query_and_retrieve_tool
from .predictors import predict_rul_tool
from .predictors import moment_predict_rul_tool
from .plotting import plot_distribution_tool
from .plotting import plot_comparison_tool
from .plotting import plot_line_chart_tool
from .plotting import plot_anomaly_tool
from .plotting import code_generation_assistant
from .predictors import moment_anomaly_detection_tool
from .predictors import nv_tesseract_anomaly_detection_tool
from .evaluators import llm_judge_evaluator_register
from .evaluators import multimodal_llm_judge_evaluator_register
