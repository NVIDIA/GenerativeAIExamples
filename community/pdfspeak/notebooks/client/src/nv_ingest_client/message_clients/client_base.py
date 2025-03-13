# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# NOTE: This code is duplicated from the ingest service:
# src/nv_ingest/util/message_brokers/client_base.py
# Eventually we should move all client wrappers for the message broker into a shared library that both the ingest
# service and the client can use.

from abc import ABC
from abc import abstractmethod
from typing import Any


class MessageBrokerClientBase(ABC):
    """
    Abstract base class for a messaging client to interface with various messaging systems.

    Provides a standard interface for sending and receiving messages with connection management
    and retry logic.
    """

    @abstractmethod
    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        max_retries: int = 0,
        max_backoff: int = 32,
        connection_timeout: int = 300,
        max_pool_size: int = 128,
        use_ssl: bool = False,
    ):
        """
        Initialize the messaging client with connection parameters.
        """

    @abstractmethod
    def get_client(self):
        """
        Returns the client instance, reconnecting if necessary.

        Returns:
            The client instance.
        """

    @abstractmethod
    def ping(self) -> bool:
        """
        Checks if the server is responsive.

        Returns:
            True if the server responds to a ping, False otherwise.
        """

    @abstractmethod
    def fetch_message(self, job_index: str, timeout: float = 0) -> Any:
        """
        Fetches a message from the specified queue with retries on failure.

        Parameters:
            job_index (str): The index of the job to fetch the message for.
            timeout (float): The timeout in seconds for blocking until a message is available.

        Returns:
            The fetched message, or None if no message could be fetched.
        """

    @abstractmethod
    def submit_message(self, channel_name: str, message: str, for_nv_ingest: bool = False) -> Any:
        """
        Submits a message to a specified queue with retries on failure.

        Parameters:
            channel_name (str): The name of the queue to submit the message to.
            message (str): The message to submit.
            for_nv_ingest (bool): Whether the message is expected to be consumed by NV Ingest.
        """
