# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import logging
from typing import Dict
from typing import Optional

from pydantic import BaseModel

from .task_base import Task

logger = logging.getLogger(__name__)


class CaptionTaskSchema(BaseModel):
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    prompt: Optional[str] = None

    class Config:
        extra = "forbid"


class CaptionTask(Task):
    def __init__(
        self,
        api_key: str = None,
        endpoint_url: str = None,
        prompt: str = None,
    ) -> None:
        super().__init__()

        self._api_key = api_key
        self._endpoint_url = endpoint_url
        self._prompt = prompt

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "Image Caption Task:\n"

        if self._api_key:
            info += "  api_key: [redacted]\n"
        if self._endpoint_url:
            info += f"  endpoint_url: {self._endpoint_url}\n"
        if self._prompt:
            info += f"  prompt: {self._prompt}\n"

        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis
        """
        task_properties = {}

        if self._api_key:
            task_properties["api_key"] = self._api_key

        if self._endpoint_url:
            task_properties["endpoint_url"] = self._endpoint_url

        if self._prompt:
            task_properties["prompt"] = self._prompt

        return {"type": "caption", "task_properties": task_properties}
