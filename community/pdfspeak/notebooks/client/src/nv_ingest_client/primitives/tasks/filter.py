# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import logging
from typing import Dict
from typing import Literal
from typing import Union

from pydantic import BaseModel
from pydantic import validator

from .task_base import Task

logger = logging.getLogger(__name__)


class FilterTaskSchema(BaseModel):
    content_type: str = "image"
    min_size: int = 128
    max_aspect_ratio: Union[float, int] = 5.0
    min_aspect_ratio: Union[float, int] = 0.2
    filter: bool = False

    @validator("content_type")
    def content_type_must_be_valid(cls, v):
        valid_criteria = ["image"]
        if v not in valid_criteria:
            raise ValueError(f"content_type must be one of {valid_criteria}")
        return v

    class Config:
        extra = "forbid"


class FilterTask(Task):
    """
    Object for document filter task
    """

    _TypeContentType = Literal["image"]

    def __init__(
        self,
        content_type: _TypeContentType = "image",
        min_size: int = 128,
        max_aspect_ratio: Union[int, float] = 5.0,
        min_aspect_ratio: Union[int, float] = 0.2,
        filter: bool = False,
    ) -> None:
        """
        Setup Split Task Config
        """
        super().__init__()
        self._content_type = content_type
        self._min_size = min_size
        self._max_aspect_ratio = max_aspect_ratio
        self._min_aspect_ratio = min_aspect_ratio
        self._filter = filter

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "Filter Task:\n"
        info += f"  content_type: {self._content_type}\n"
        info += f"  min_size: {self._min_size}\n"
        info += f"  max_aspect_ratio: {self._max_aspect_ratio}\n"
        info += f"  min_aspect_ratio: {self._min_aspect_ratio}\n"
        info += f"  filter: {self._filter}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis
        """
        filter_params = {
            "min_size": self._min_size,
            "max_aspect_ratio": self._max_aspect_ratio,
            "min_aspect_ratio": self._min_aspect_ratio,
            "filter": self._filter,
        }

        task_properties = {
            "content_type": self._content_type,
            "params": filter_params,
        }

        return {"type": "filter", "task_properties": task_properties}
