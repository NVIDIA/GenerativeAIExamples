# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


import logging
from concurrent.futures import Future
from enum import Enum
from enum import auto
from typing import Dict
from typing import Optional
from typing import Union
from uuid import UUID

from .job_spec import JobSpec

logger = logging.getLogger(__name__)


class JobStateEnum(Enum):
    """
    Enumeration of possible states for a job in the NvIngestClient system.
    """

    PENDING = auto()  # Job has been created but not yet submitted or processed.
    SUBMITTED_ASYNC = auto()  # Job has been submitted to the queue asynchronously.
    SUBMITTED = auto()  # Job has been submitted to the queue.
    PROCESSING = auto()  # Job is currently being processed.
    COMPLETED = auto()  # Job has completed processing successfully.
    FAILED = auto()  # Job has failed during processing.
    CANCELLED = auto()  # Job has been cancelled before completion.


_TERMINAL_STATES = {JobStateEnum.COMPLETED, JobStateEnum.FAILED, JobStateEnum.CANCELLED}
_PREFLIGHT_STATES = {JobStateEnum.PENDING, JobStateEnum.SUBMITTED_ASYNC}


class JobState:
    """
    Encapsulates the state information for a job managed by the NvIngestClient.

    Attributes
    ----------
    job_spec: JobSpec
        The unique identifier for the job.
    state : str
        The current state of the job.
    future : Future, optional
        The future object associated with the job's asynchronous operation.
    response : Dict, optional
        The response data received for the job.
    response_channel : str, optional
        The channel through which responses for the job are received.

    Methods
    -------
    __init__(self, job_id: str, state: str, future: Optional[Future] = None,
             response: Optional[Dict] = None, response_channel: Optional[str] = None)
        Initializes a new instance of JobState.
    """

    def __init__(
        self,
        job_spec: JobSpec,
        state: JobStateEnum = JobStateEnum.PENDING,
        future: Optional[Future] = None,
        response: Optional[Dict] = None,
        response_channel: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        self._job_spec = job_spec
        self._state = state
        self._future = future
        self._response = response  # TODO(Devin): Not currently used
        self._response_channel = response_channel
        self._trace_id = trace_id
        self._telemetry = {}

    @property
    def job_spec(self) -> JobSpec:
        """Gets the job specification associated with the state."""
        return self._job_spec

    @job_spec.setter
    def job_spec(self, value: JobSpec) -> None:
        """Sets the job specification associated with the state."""
        if self._state not in _PREFLIGHT_STATES:
            err_msg = f"Attempt to change job_spec after job submission: {self._state.name}"
            logger.error(err_msg)

            raise ValueError(err_msg)

        self._job_spec = value

    @property
    def job_id(self) -> Union[UUID, str]:
        """Gets the job's unique identifier."""
        return self._job_spec.job_id

    @job_id.setter
    def job_id(self, value: str) -> None:
        """Sets the job's unique identifier, with constraints."""
        self._job_spec.job_id = value

    @property
    def state(self) -> JobStateEnum:
        """Gets the current state of the job."""
        return self._state

    @state.setter
    def state(self, value: JobStateEnum) -> None:
        """Sets the current state of the job with transition constraints."""
        if self._state in _TERMINAL_STATES:
            logger.error(f"Attempt to change state from {self._state.name} to {value.name} denied.")
            raise ValueError(f"Cannot change state from {self._state.name} to {value.name}.")
        if value.value < self._state.value:
            logger.error(f"Invalid state transition attempt from {self._state.name} to {value.name}.")
            raise ValueError(f"State can only transition forward, from {self._state.name} to {value.name} not allowed.")
        self._state = value

    @property
    def future(self) -> Optional[Future]:
        """Gets the future object associated with the job's asynchronous operation."""
        return self._future

    @future.setter
    def future(self, value: Future) -> None:
        """Sets the future object associated with the job's asynchronous operation, with constraints."""
        self._future = value

    # TODO(Devin): Not convinced we need 'response' probably remove.
    @property
    def response(self) -> Optional[Dict]:
        """Gets the response data received for the job."""
        return self._response

    @response.setter
    def response(self, value: Dict) -> None:
        """Sets the response data received for the job, with constraints."""
        self._response = value

    @property
    def trace_id(self) -> Optional[str]:
        """Gets the trace_id from the job submission"""
        return self._trace_id

    @trace_id.setter
    def trace_id(self, value: str) -> None:
        """Sets the trace_id that was received from the submission to the REST endpoint"""
        self._trace_id = value
