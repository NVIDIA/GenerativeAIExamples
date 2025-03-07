# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import logging
from typing import Dict
from typing import Literal

from pydantic import BaseModel
from pydantic import root_validator

from .task_base import Task

logger = logging.getLogger(__name__)

_DEFAULT_STORE_METHOD = "minio"


class StoreEmbedTaskSchema(BaseModel):

    class Config:
        extra = "allow"


class StoreTaskSchema(BaseModel):
    store_method: str = None

    @root_validator(pre=True)
    def set_default_store_method(cls, values):
        store_method = values.get("store_method")

        if store_method is None:
            values["store_method"] = _DEFAULT_STORE_METHOD
        return values

    class Config:
        extra = "allow"


class StoreTask(Task):
    """
    Object for image storage task.
    """

    _Type_Content_Type = Literal["image",]

    _Type_Store_Method = Literal["minio",]

    def __init__(
        self,
        structured: bool = True,
        images: bool = False,
        store_method: _Type_Store_Method = None,
        params: dict = None,
        **extra_params,
    ) -> None:
        """
        Setup Store Task Config
        """
        super().__init__()

        self._structured = structured
        self._images = images
        self._store_method = store_method or "minio"
        self._params = params
        self._extra_params = extra_params

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "Store Task:\n"
        info += f"  store structured types: {self._structured}\n"
        info += f"  store image types: {self._images}\n"
        info += f"  store method: {self._store_method}\n"
        for key, value in self._extra_params.items():
            info += f"  {key}: {value}\n"
        for key, value in self._params.items():
            info += f"  {key}: {value}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis (fixme)
        """

        task_properties = {
            "method": self._store_method,
            "structured": self._structured,
            "images": self._images,
            "params": self._params,
            **self._extra_params,
        }

        return {"type": "store", "task_properties": task_properties}


class StoreEmbedTask(Task):
    """
    Object for image storage task.
    """

    _Type_Content_Type = Literal["embedding",]

    _Type_Store_Method = Literal["minio",]

    def __init__(self, params: dict = None, **extra_params) -> None:
        """
        Setup Store Task Config
        """
        super().__init__()

        self._params = params or {}
        self._extra_params = extra_params

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += "Store Embed Task:\n"
        for key, value in self._extra_params.items():
            info += f"  {key}: {value}\n"
        for key, value in self._params.items():
            info += f"  {key}: {value}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Convert to a dict for submission to redis (fixme)
        """
        task_properties = {
            "params": self._params,
            **self._extra_params,
        }

        return {"type": "store_embedding", "task_properties": task_properties}
