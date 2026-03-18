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

from openai import OpenAI
import os
from typing import List, Optional, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage


class ChatOpenAI:
    def __init__(
        self,
        model: str = "nvidia/nemotron-3-nano-30b-a3b",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        api_key: Optional[str] = None,
        temperature: float = 0.6,
        top_p: float = 0.95,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        stream: bool = False
    ):
        self.model = model
        self.base_url = base_url.rstrip("/").removesuffix("/chat/completions")
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_completion_tokens if max_completion_tokens is not None else (max_tokens or 65536)
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stream = stream

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    @classmethod
    def from_config(cls, config: dict) -> "ChatOpenAI":
        cfg = config or {}
        key_env = cfg.get("api_key_env", "NVIDIA_API_KEY")
        return cls(
            model=cfg.get("model_name", cfg.get("model", "meta/llama-3.1-70b-instruct")),
            base_url=cfg.get("api_url", "https://integrate.api.nvidia.com/v1"),
            api_key=os.environ.get(key_env),
            temperature=float(cfg.get("temperature", 0.6)),
            top_p=float(cfg.get("top_p", 0.95)),
            max_tokens=int(cfg.get("max_tokens", 4096)),
        )

    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[dict]:
        openai_messages = []
        for message in messages:
            if isinstance(message, SystemMessage):
                openai_messages.append({"role": "system", "content": message.content})
            elif isinstance(message, HumanMessage):
                openai_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                openai_messages.append({"role": "assistant", "content": message.content})
            else:
                role = getattr(message, "type", "user")
                if role == "system":
                    role = "system"
                elif role in ("ai", "assistant"):
                    role = "assistant"
                else:
                    role = "user"
                content = getattr(message, "content", str(message))
                openai_messages.append({"role": role, "content": content})
        return openai_messages

    def invoke(self, messages, extra_body: Optional[dict] = None, **kwargs) -> AIMessage:
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
        elif isinstance(messages, list) and len(messages) > 0 and isinstance(messages[0], str):
            converted = [SystemMessage(content=messages[0])]
            for msg in messages[1:]:
                converted.append(HumanMessage(content=msg) if isinstance(msg, str) else msg)
            messages = converted

        openai_messages = self._convert_messages_to_openai_format(messages)
        create_kwargs: dict = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": self.stream,
        }
        if extra_body is not None:
            create_kwargs["extra_body"] = extra_body
        create_kwargs.update(kwargs)
        response = self.client.chat.completions.create(**create_kwargs)
        return AIMessage(content=response.choices[0].message.content)
