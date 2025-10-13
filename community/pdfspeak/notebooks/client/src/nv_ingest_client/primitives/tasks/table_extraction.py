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


class TableExtractionSchema(BaseModel):
    class Config:
        extra = "forbid"


class TableExtractionTask(Task):
    """
    Object for table extraction tasks
    """

    def __init__(self) -> None:
        """
        Setup Dedup Task Config
        """
        super().__init__()

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "table extraction task\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis
        """

        task_properties = {
            "params": {},
        }

        return {"type": "table_data_extract", "task_properties": task_properties}
