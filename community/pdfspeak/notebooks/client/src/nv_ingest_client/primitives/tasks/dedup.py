# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import logging
from typing import Dict
from typing import Literal

from pydantic import BaseModel
from pydantic import validator

from .task_base import Task

logger = logging.getLogger(__name__)


class DedupTaskSchema(BaseModel):
    content_type: str = "image"
    filter: bool = False

    @validator("content_type")
    def content_type_must_be_valid(cls, v):
        valid_criteria = ["image"]
        if v not in valid_criteria:
            raise ValueError(f"content_type must be one of {valid_criteria}")
        return v

    class Config:
        extra = "forbid"


class DedupTask(Task):
    """
    Object for document dedup task
    """

    _TypeContentType = Literal["image"]

    def __init__(
        self,
        content_type: _TypeContentType = "image",
        filter: bool = False,
    ) -> None:
        """
        Setup Dedup Task Config
        """
        super().__init__()
        self._content_type = content_type
        self._filter = filter

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "Dedup Task:\n"
        info += f"  content_type: {self._content_type}\n"
        info += f"  filter: {self._filter}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis
        """
        dedup_params = {"filter": self._filter}

        task_properties = {
            "content_type": self._content_type,
            "params": dedup_params,
        }

        return {"type": "dedup", "task_properties": task_properties}
