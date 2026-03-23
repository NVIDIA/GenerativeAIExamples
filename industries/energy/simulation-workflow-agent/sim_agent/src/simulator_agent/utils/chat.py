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
Chat history utilities.
"""

from __future__ import annotations

from typing import Any, List

from langchain_core.messages import BaseMessage

from ..state import CHAT_HISTORY_MAX_TURNS


def trim_chat_history(history: list[BaseMessage], max_turns: int = CHAT_HISTORY_MAX_TURNS) -> list[BaseMessage]:
    if not history:
        return []
    max_msgs = max_turns * 2
    if len(history) <= max_msgs:
        return list(history)
    return list(history[-max_msgs:])


def chat_history_to_conversation(chat_history: list[BaseMessage]) -> List[dict[str, Any]]:
    out: List[dict[str, Any]] = []
    for msg in chat_history or []:
        role = getattr(msg, "type", None) or getattr(msg, "role", "user")
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"
        content = getattr(msg, "content", None) or ""
        if isinstance(content, list):
            content = " ".join(getattr(part, "text", str(part)) for part in content if hasattr(part, "text"))
        d: dict[str, Any] = {"role": role, "content": content}
        if hasattr(msg, "name") and getattr(msg, "name"):
            d["tool_name"] = getattr(msg, "name")
        out.append(d)
    return out
