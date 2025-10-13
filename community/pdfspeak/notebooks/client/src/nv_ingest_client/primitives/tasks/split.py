# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import logging
from typing import Dict
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import validator

from .task_base import Task

logger = logging.getLogger(__name__)


class SplitTaskSchema(BaseModel):
    split_by: Optional[str] = "sentence"
    split_length: Optional[int] = 10
    split_overlap: Optional[int] = 0
    max_character_length: Optional[int] = 1024
    sentence_window_size: Optional[int] = 0

    @validator("split_by")
    def split_by_must_be_valid(cls, v):
        valid_criteria = ["page", "size", "word", "sentence"]
        if v not in valid_criteria:
            raise ValueError(f"split_by must be one of {valid_criteria}")
        return v

    class Config:
        extra = "forbid"


class SplitTask(Task):
    """
    Object for document splitting task
    """

    _TypeSplitBy = Literal["word", "sentence", "passage"]

    def __init__(
        self,
        split_by: _TypeSplitBy = None,
        split_length: int = None,
        split_overlap: int = None,
        max_character_length: int = None,
        sentence_window_size: int = None,
    ) -> None:
        """
        Setup Split Task Config
        """
        super().__init__()
        self._split_by = split_by
        self._split_length = split_length
        self._split_overlap = split_overlap
        self._max_character_length = max_character_length
        self._sentence_window_size = sentence_window_size

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "Split Task:\n"
        info += f"  split_by: {self._split_by}\n"
        info += f"  split_length: {self._split_length}\n"
        info += f"  split_overlap: {self._split_overlap}\n"
        info += f"  split_max_character_length: {self._max_character_length}\n"
        info += f"  split_sentence_window_size: {self._sentence_window_size}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis
        """
        split_params = {}

        if self._split_by is not None:
            split_params["split_by"] = self._split_by
        if self._split_length is not None:
            split_params["split_length"] = self._split_length
        if self._split_overlap is not None:
            split_params["split_overlap"] = self._split_overlap
        if self._max_character_length is not None:
            split_params["max_character_length"] = self._max_character_length
        if self._sentence_window_size is not None:
            split_params["sentence_window_size"] = self._sentence_window_size

        return {"type": "split", "task_properties": split_params}
