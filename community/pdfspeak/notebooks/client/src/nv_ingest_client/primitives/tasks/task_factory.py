# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import inspect
from typing import Callable
from typing import Dict
from typing import Type
from typing import Union

from .caption import CaptionTask
from .dedup import DedupTask
from .embed import EmbedTask
from .extract import ExtractTask
from .filter import FilterTask
from .split import SplitTask
from .store import StoreEmbedTask
from .store import StoreTask
from .task_base import Task
from .task_base import TaskType
from .task_base import is_valid_task_type
from .vdb_upload import VdbUploadTask


class TaskUnimplemented(Task):
    """
    Placeholder for unimplemented tasks
    """

    def __init__(self, **kwargs) -> None:
        super().__init__()
        raise NotImplementedError("Task type is not implemented")


# Mapping of TaskType to Task classes, arranged alphabetically by task type
_TASK_MAP: Dict[TaskType, Callable] = {
    TaskType.CAPTION: CaptionTask,
    TaskType.DEDUP: DedupTask,
    TaskType.EMBED: EmbedTask,
    TaskType.EXTRACT: ExtractTask,
    TaskType.FILTER: FilterTask,
    TaskType.SPLIT: SplitTask,
    TaskType.STORE_EMBEDDING: StoreEmbedTask,
    TaskType.STORE: StoreTask,
    TaskType.TRANSFORM: TaskUnimplemented,
    TaskType.VDB_UPLOAD: VdbUploadTask,
}


def task_factory(task_type: Union[TaskType, str], **kwargs) -> Task:
    """
    Factory method for creating tasks based on the provided task type.

    Parameters
    ----------
    task_type : TaskType
        The type of the task to create.
    **kwargs : dict
        Additional keyword arguments to pass to the task's constructor.

    Returns
    -------
    Task
        An instance of the task corresponding to the given task type.

    Raises
    ------
    ValueError
        If an invalid task type is provided.
    """

    if isinstance(task_type, str):
        if is_valid_task_type(task_type):
            task_type = TaskType[task_type]
        else:
            raise ValueError(f"Invalid task type string: '{task_type}'")
    elif not isinstance(task_type, TaskType):
        raise ValueError("task_type must be a TaskType enum member or a valid task type string")

    task_class: Type[Task] = _TASK_MAP[task_type]

    # Inspect the constructor (__init__) of the task class to get its parameters
    sig = inspect.signature(task_class.__init__)
    params = sig.parameters

    # Exclude 'self' and positional-only parameters
    valid_kwargs = {
        name
        for name, param in params.items()
        if param.kind in [param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD] and name != "self"
    }

    # Check if provided kwargs match the task's constructor parameters
    for kwarg in kwargs:
        if kwarg not in valid_kwargs:
            raise ValueError(f"Unexpected keyword argument '{kwarg}' for task type '{task_type.name}'")

    # Create and return the task instance with the provided kwargs
    return task_class(**kwargs)
