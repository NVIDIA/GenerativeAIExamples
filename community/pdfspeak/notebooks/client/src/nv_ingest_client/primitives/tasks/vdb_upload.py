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


class VdbUploadTaskSchema(BaseModel):
    filter_errors: bool = False
    bulk_ingest: bool = (False,)
    bulk_ingest_path: str = (None,)
    params: dict = None

    class Config:
        extra = "forbid"


class VdbUploadTask(Task):
    """
    Object for document embedding task
    """

    def __init__(
        self,
        filter_errors: bool = False,
        bulk_ingest: bool = False,
        bulk_ingest_path: str = "embeddings/",
        params: dict = None,
    ) -> None:
        """
        Setup VDB Upload Task Config
        """
        super().__init__()
        self._filter_errors = filter_errors
        self._bulk_ingest = bulk_ingest
        self._bulk_ingest_path = bulk_ingest_path
        self._params = params or {}

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "VDB Upload Task:\n"
        info += f"  filter_errors: {self._filter_errors}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis
        """

        task_properties = {
            "filter_errors": self._filter_errors,
            "bulk_ingest": self._bulk_ingest,
            "bulk_ingest_path": self._bulk_ingest_path,
            "params": self._params,
        }

        return {"type": "vdb_upload", "task_properties": task_properties}
