# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import logging
from enum import Enum
from enum import auto
from typing import Dict

logger = logging.getLogger(__name__)


class TaskType(Enum):
    CAPTION = auto()
    DEDUP = auto()
    EMBED = auto()
    EXTRACT = auto()
    FILTER = auto()
    SPLIT = auto()
    TRANSFORM = auto()
    STORE_EMBEDDING = auto()
    STORE = auto()
    VDB_UPLOAD = auto()
    TABLE_DATA_EXTRACT = auto()
    CHART_DATA_EXTRACT = auto()


def is_valid_task_type(task_type_str: str) -> bool:
    """
    Checks if the provided string is a valid TaskType enum value.

    Parameters
    ----------
    task_type_str : str
        The string to check against the TaskType enum values.

    Returns
    -------
    bool
        True if the string is a valid TaskType enum value, False otherwise.
    """
    return task_type_str in TaskType.__members__


class Task:
    """
    Generic task Object
    """

    def __init__(self) -> None:
        """
        Setup Ingest Task Config
        """

    def __str__(self) -> str:
        """
        Returns a string with the object's config and run time state
        """
        info = ""
        info += f"{self.__class__.__name__}\n"
        return info

    def to_dict(self) -> Dict:
        """
        Returns a string with the task specification. This string is used for constructing
        tasks that are then submitted to the redis client
        """
        return {}


# class ExtractUnstructuredTask(ExtractTask):
#    """
#    Object for document unstructured extraction task
#    extract_method = ["unstructured_local", "unstructured_service"]
#    """
#
#    def __init__(
#            self,
#            extract_method: ExtractTask._Type_Extract_Method,
#            document_type: ExtractTask._TypeDocumentType,
#            api_key: str,
#            uri: str,
#    ) -> None:
#        """
#        Setup Extract Task Config
#        """
#        super().__init__(extract_method, document_type)
#        self._api_key = api_key
#        self._uri = uri
#
#    def __str__(self) -> str:
#        """
#        Returns a string with the object's config and run time state
#        """
#        info = ""
#        info += super().__str__()
#        info += f"unstructured uri: {self._uri}\n"
#        return info
#
#    def to_dict(self) -> Dict:
#        """
#        Convert to a dict for submission to redis (fixme)
#        """
#        unstructured_properties = {
#            "api_key": self._api_key,
#            "unstructured_url": self._uri,
#        }
#        task_desc = super().to_dict()
#        task_desc["task_properties"]["params"].update(unstructured_properties)
#        return task_desc


# class ExtractLlamaParseTask(ExtractTask):
#    """
#    Object for document llama extraction task
#    extract_method = ["llama_parse"]
#    """
#
#    def __init__(
#            self,
#            extract_method: ExtractTask._Type_Extract_Method,
#            document_type: ExtractTask._TypeDocumentType,
#            api_key: str,
#    ) -> None:
#        """
#        Setup Extract Task Config
#        """
#        super().__init__(extract_method, document_type)
#        self._api_key = api_key
#
#    def to_dict(self) -> Dict:
#        """
#        Convert to a dict for submission to redis (fixme)
#        """
#        llama_parse_properties = {
#            "api_key": self._api_key,
#        }
#        task_desc = super().to_dict()
#        task_desc["task_properties"]["params"].update(llama_parse_properties)
#        return task_desc
