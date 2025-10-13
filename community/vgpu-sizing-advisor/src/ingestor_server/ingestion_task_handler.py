# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Module for handling ingestion tasks.

This module is responsible for handling ingestion tasks.
It is used to submit tasks to the task handler and get the status and result of tasks.
"""
import os
from typing import Callable, Dict, Any, Optional
import asyncio
from uuid import uuid4
from pydantic import BaseModel
from redis import Redis
import logging

logger = logging.getLogger(__name__)


class RedisSchema(BaseModel):
    """
    A class that defines the schema of the Redis database.
    """
    task_id: str
    state: str
    result: Dict[str, Any] = {}


class IngestionTaskHandler:
    """
    A class that handles ingestion tasks.
    Responsible for submitting tasks to the task handler and getting the status and result of tasks.
    """

    # Redis configuration
    _redis_host: str = os.getenv("REDIS_HOST", "localhost")
    _redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    _redis_db: int = int(os.getenv("REDIS_DB", 0))
    _enable_redis_backend: bool = os.getenv("ENABLE_REDIS_BACKEND", "False").lower() in ["true", "True"]

    if _enable_redis_backend:
        logger.info(f"Initializing Redis client with host {_redis_host}, port {_redis_port}, db {_redis_db}")
        # Initialize the Redis client
        _redis_client: Redis = Redis(host=_redis_host, port=_redis_port, db=_redis_db)
    else:
        logger.info("Redis backend is disabled")
        _redis_client = None

    def __init__(self):
        # Local task map to store tasks
        self.task_map = {} # {task_id: asyncio_task}

    async def _execute_ingestion_task(self, task_id: str, function: Callable):
        """
        Execute the ingestion task and update Redis with the result.
        Args:
            task_id: The id of the task.
            function: The function to execute.
        """
        try:
            result = await function()
            logger.info(f"Task {task_id} completed using IngestionTaskHandler")
            self._set_task_result(task_id, result)
            return result
        except Exception as e:
            self.update_task_status(task_id, "FAILED")
            logger.error(f"Task {task_id} failed using IngestionTaskHandler with error: {e}",
                         exc_info=logger.getEffectiveLevel() <= logging.DEBUG)
            raise e

    def submit_task(self, function: Callable):
        """
        Submit a task to the task handler.
        Args:
            function: The async function to submit to the task handler.
        Returns:
            task_id: The id of the task.
        """
        task_id = str(uuid4())
        asyncio_task = asyncio.create_task(self._execute_ingestion_task(task_id, function))
        self.task_map[task_id] = asyncio_task
        if self._enable_redis_backend:
            self._redis_client.json().set(
                task_id,
                "$",
                RedisSchema(task_id=task_id, state="PENDING").model_dump()
            )
        return task_id
    
    def get_task_status(self, task_id: str):
        """
        Get the status of a task.
        Args:
            task_id: The id of the task.
        Returns:
            status: The status of the task.
        """
        if self._enable_redis_backend:
            return self._redis_client.json().get(task_id).get("state")
        return self.task_map[task_id]._state

    def update_task_status(self, task_id: str, status: str):
        """
        Optional function to update the status of a task in Redis and the task map.
        Args:
            task_id: The id of the task.
            status: The status of the task.
        """
        if self._enable_redis_backend:
            self._redis_client.json().set(
                task_id,
                "$",
                RedisSchema(task_id=task_id, state=status).model_dump()
            )
        else:
            self.task_map[task_id]._state = status
    
    def _set_task_result(self, task_id: str, result: Dict[str, Any]):
        """
        Internal function to set the result of a task in Redis.
        Args:
            task_id: The id of the task.
            result: The result of the task.
        """
        if self._enable_redis_backend:
            self._redis_client.json().set(
                task_id,
                "$",
                RedisSchema(task_id=task_id, state="FINISHED", result=result).model_dump()
            )

    def get_task_result(self, task_id: str):
        """
        Get the result of a task from Redis and the task map.
        Args:
            task_id: The id of the task.
        Returns:
            result: The result of the task.
        """
        logger.info(f"Getting result of task {task_id}, enable_redis_backend: {self._enable_redis_backend}")
        if self._enable_redis_backend:
            return self._redis_client.json().get(task_id).get("result")
        logger.info(f"Task result: {self.task_map[task_id].result()}")
        return self.task_map[task_id].result()


# Create a singleton instance of the IngestionTaskHandler
# (Shared across asyncio coroutines in a single uvicorn worker)
INGESTION_TASK_HANDLER = IngestionTaskHandler()
