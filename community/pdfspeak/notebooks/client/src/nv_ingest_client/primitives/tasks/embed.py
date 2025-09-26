# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import logging
from typing import Dict

from pydantic import BaseModel

from .task_base import Task

logger = logging.getLogger(__name__)


class EmbedTaskSchema(BaseModel):
    text: bool = True
    tables: bool = True
    filter_errors: bool = False

    class Config:
        extra = "forbid"


class EmbedTask(Task):
    """
    Object for document embedding task
    """

    def __init__(self, text: bool = True, tables: bool = True, filter_errors: bool = False) -> None:
        """
        Setup Embed Task Config
        """
        super().__init__()
        self._text = text
        self._tables = tables
        self._filter_errors = filter_errors

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "Embed Task:\n"
        info += f"  text: {self._text}\n"
        info += f"  tables: {self._tables}\n"
        info += f"  filter_errors: {self._filter_errors}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis
        """

        task_properties = {
            "text": self._text,
            "tables": self._tables,
            "filter_errors": False,
        }

        return {"type": "embed", "task_properties": task_properties}
