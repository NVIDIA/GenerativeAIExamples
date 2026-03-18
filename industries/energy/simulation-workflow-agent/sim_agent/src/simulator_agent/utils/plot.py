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
Plot metric inference utilities.
"""

from __future__ import annotations

from typing import Optional

__all__ = ["infer_plot_metric_with_llm"]


def infer_plot_metric_with_llm(user_query: str) -> Optional[str]:
    """
    Infer OPM summary metric keyword from user query (e.g. "plot field oil" -> FOPT).

    Delegates to rag_skill extract_keyword with intent=summary_metric.
    """
    from ..skills.rag_skill.scripts.extract_keyword import extract_keyword

    return extract_keyword(user_query, intent="summary_metric")
