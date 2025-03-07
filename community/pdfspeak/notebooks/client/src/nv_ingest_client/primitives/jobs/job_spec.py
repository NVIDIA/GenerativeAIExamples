# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


import logging
from collections import defaultdict
from io import BytesIO
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from uuid import UUID

from nv_ingest_client.primitives.tasks import Task
from nv_ingest_client.primitives.tasks import ExtractTask
from nv_ingest_client.primitives.tasks.table_extraction import TableExtractionTask
from nv_ingest_client.primitives.tasks.chart_extraction import ChartExtractionTask
from nv_ingest_client.util.dataset import get_dataset_files
from nv_ingest_client.util.dataset import get_dataset_statistics

logger = logging.getLogger(__name__)


class JobSpec:
    """
    Specification for creating a job for submission to the nv-ingest microservice.

    Parameters
    ----------
    payload : Dict
        The payload data for the job.
    tasks : Optional[List], optional
        A list of tasks to be added to the job, by default None.
    source_id : Optional[str], optional
        An identifier for the source of the job, by default None.
    job_id : Optional[UUID], optional
        A unique identifier for the job, by default a new UUID is generated.
    extended_options : Optional[Dict], optional
        Additional options for job processing, by default None.

    Attributes
    ----------
    _payload : Dict
        Storage for the payload data.
    _tasks : List
        Storage for the list of tasks.
    _source_id : str
        Storage for the source identifier.
    _job_id : UUID
        Storage for the job's unique identifier.
    _extended_options : Dict
        Storage for the additional options.

    Methods
    -------
    to_dict() -> Dict:
        Converts the job specification to a dictionary.
    add_task(task):
        Adds a task to the job specification.
    """

    def __init__(
        self,
        payload: str = None,
        tasks: Optional[List] = None,
        source_id: Optional[str] = None,
        source_name: Optional[str] = None,
        document_type: Optional[str] = None,
        extended_options: Optional[Dict] = None,
    ) -> None:
        self._document_type = document_type or "txt"
        self._extended_options = extended_options or {}
        self._job_id = None
        self._payload = payload
        self._source_id = source_id
        self._source_name = source_name
        self._tasks = tasks or []

    def __str__(self) -> str:
        task_info = "\n".join(str(task) for task in self._tasks)
        return (
            f"source-id: {self._source_id}\n"
            f"source-name: {self._source_name}\n"
            f"document-type: {self._document_type}\n"
            f"task count: {len(self._tasks)}\n"
            f"payload: {'<*** ' + str(len(self._payload)) + ' ***>' if self._payload else 'Empty'}\n"
            f"extended-options: {self._extended_options}\n"
            f"{task_info}"
        )

    def to_dict(self) -> Dict:
        """
        Converts the job specification instance into a dictionary suitable for JSON serialization.

        Returns
        -------
        Dict
            A dictionary representation of the job specification.
        """
        return {
            "job_payload": {
                "source_name": [self._source_name],
                "source_id": [self._source_id],
                "content": [self._payload],
                "document_type": [self._document_type],
            },
            "job_id": str(self._job_id),
            "tasks": [task.to_dict() for task in self._tasks],
            "tracing_options": self._extended_options.get("tracing_options", {}),
        }

    @property
    def payload(self) -> Dict:
        return self._payload

    @payload.setter
    def payload(self, payload: Dict) -> None:
        self._payload = payload

    @property
    def job_id(self) -> UUID:
        return self._job_id

    @job_id.setter
    def job_id(self, job_id: UUID) -> None:
        self._job_id = job_id

    @property
    def source_id(self) -> str:
        return self._source_id

    @source_id.setter
    def source_id(self, source_id: str) -> None:
        self._source_id = source_id

    @property
    def source_name(self) -> str:
        return self._source_name

    @source_name.setter
    def source_name(self, source_name: str) -> None:
        self._source_name = source_name

    @property
    def document_type(self) -> str:
        return self._document_type

    def add_task(self, task) -> None:
        """
        Adds a task to the job specification.

        Parameters
        ----------
        task
            The task to add to the job specification. Assumes the task has a to_dict method.

        Raises
        ------
        ValueError
            If the task does not have a to_dict method.
        """
        if not isinstance(task, Task):
            raise ValueError("Task must derive from nv_ingest_client.primitives.Task class")

        self._tasks.append(task)

        if isinstance(task, ExtractTask) and (task._extract_tables is True):
            self._tasks.append(TableExtractionTask())
        if isinstance(task, ExtractTask) and (task._extract_charts is True):
            self._tasks.append(ChartExtractionTask())


class BatchJobSpec:
    """
    A class used to represent a batch of job specifications (JobSpecs).

    This class allows for batch processing of multiple jobs, either from a list of
    `JobSpec` instances or from file paths. It provides methods for adding job
    specifications, associating tasks with those specifications, and serializing the
    batch to a dictionary format.

    Attributes
    ----------
    _file_type_to_job_spec : defaultdict
        A dictionary that maps document types to a list of `JobSpec` instances.
    """

    def __init__(self, job_specs_or_files: Optional[Union[List[JobSpec], List[str]]] = None) -> None:
        """
        Initializes the BatchJobSpec instance.

        Parameters
        ----------
        job_specs_or_files : Optional[Union[List[JobSpec], List[str]]], optional
            A list of either `JobSpec` instances or file paths. If provided, the
            instance will be initialized with the corresponding job specifications.
        """
        self._file_type_to_job_spec = defaultdict(list)

        if job_specs_or_files:
            if isinstance(job_specs_or_files[0], JobSpec):
                self.from_job_specs(job_specs_or_files)
            elif isinstance(job_specs_or_files[0], str):
                self.from_files(job_specs_or_files)
            else:
                raise ValueError("Invalid input type for job_specs. Must be a list of JobSpec or file paths.")

    def from_job_specs(self, job_specs: Union[JobSpec, List[JobSpec]]) -> None:
        """
        Initializes the batch with a list of `JobSpec` instances.

        Parameters
        ----------
        job_specs : Union[JobSpec, List[JobSpec]]
            A single `JobSpec` or a list of `JobSpec` instances to add to the batch.
        """
        if isinstance(job_specs, JobSpec):
            job_specs = [job_specs]

        for job_spec in job_specs:
            self.add_job_spec(job_spec)

    def from_files(self, files: Union[str, List[str]]) -> None:
        """
        Initializes the batch by generating job specifications from file paths.

        Parameters
        ----------
        files : Union[str, List[str]]
            A single file path or a list of file paths to create job specifications from.
        """
        from nv_ingest_client.util.util import create_job_specs_for_batch
        from nv_ingest_client.util.util import generate_matching_files

        if isinstance(files, str):
            files = [files]

        matching_files = list(generate_matching_files(files))
        if not matching_files:
            logger.warning(f"No files found matching {files}.")
            return

        job_specs = create_job_specs_for_batch(matching_files)
        for job_spec in job_specs:
            self.add_job_spec(job_spec)

    def _from_dataset(self, dataset: str, shuffle_dataset: bool = True) -> None:
        """
        Internal method to initialize the batch from a dataset.

        Parameters
        ----------
        dataset : str
            The path to the dataset file.
        shuffle_dataset : bool, optional
            Whether to shuffle the dataset files before adding them to the batch, by default True.
        """
        with open(dataset, "rb") as file:
            dataset_bytes = BytesIO(file.read())

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(get_dataset_statistics(dataset_bytes))

        dataset_files = get_dataset_files(dataset_bytes, shuffle_dataset)

        self.from_files(dataset_files)

    @classmethod
    def from_dataset(cls, dataset: str, shuffle_dataset: bool = True):
        """
        Class method to create a `BatchJobSpec` instance from a dataset.

        Parameters
        ----------
        dataset : str
            The path to the dataset file.
        shuffle_dataset : bool, optional
            Whether to shuffle the dataset files before adding them to the batch, by default True.

        Returns
        -------
        BatchJobSpec
            A new instance of `BatchJobSpec` initialized with the dataset files.
        """
        batch_job_spec = cls()
        batch_job_spec._from_dataset(dataset, shuffle_dataset=shuffle_dataset)
        return batch_job_spec

    def add_job_spec(self, job_spec: JobSpec) -> None:
        """
        Adds a `JobSpec` to the batch.

        Parameters
        ----------
        job_spec : JobSpec
            The job specification to add.
        """
        self._file_type_to_job_spec[job_spec.document_type].append(job_spec)

    def add_task(self, task, document_type=None):
        """
        Adds a task to the relevant job specifications in the batch.

        If a `document_type` is provided, the task will be added to all job specifications
        matching that document type. If no `document_type` is provided, the task will be added
        to all job specifications in the batch.

        Parameters
        ----------
        task : Task
            The task to add. Must derive from the `nv_ingest_client.primitives.Task` class.

        document_type : str, optional
            The document type used to filter job specifications. If not provided, the
            `document_type` is inferred from the task, or the task is applied to all job specifications.

        Raises
        ------
        ValueError
            If the task does not derive from the `Task` class.
        """
        if not isinstance(task, Task):
            raise ValueError("Task must derive from nv_ingest_client.primitives.Task class")

        document_type = document_type or task.to_dict().get("document_type")

        if document_type:
            target_job_specs = self._file_type_to_job_spec[document_type]
        else:
            target_job_specs = []
            for job_specs in self._file_type_to_job_spec.values():
                target_job_specs.extend(job_specs)

        for job_spec in target_job_specs:
            job_spec.add_task(task)

    def to_dict(self) -> Dict[str, List[Dict]]:
        """
        Serializes the batch of job specifications into a list of dictionaries.

        Returns
        -------
        List[Dict]
            A list of dictionaries representing the job specifications in the batch.
        """
        return {
            file_type: [j.to_dict() for j in job_specs] for file_type, job_specs in self._file_type_to_job_spec.items()
        }

    def __str__(self) -> str:
        """
        Returns a string representation of the batch.

        Returns
        -------
        str
            A string representation of the job specifications in the batch.
        """
        result = ""
        for file_type, job_specs in self._file_type_to_job_spec.items():
            result += f"{file_type}\n"
            for job_spec in job_specs:
                result += str(job_spec) + "\n"

        return result

    @property
    def job_specs(self) -> Dict[str, List[str]]:
        """
        A property that returns a dictionary of job specs categorized by document type.

        Returns
        -------
        Dict[str, List[str]]
            A dictionary mapping document types to job specifications.
        """
        return self._file_type_to_job_spec

    @property
    def file_types(self) -> List[str]:
        """
        Returns the list of unique file types present in the batch.

        This property retrieves the document types currently stored in the batch's
        job specifications.

        Returns
        -------
        List[str]
            A list of document types for the jobs in the batch.
        """
        return list(self._file_type_to_job_spec.keys())

    @property
    def tasks(self) -> Dict[str, List[Task]]:
        """
        Adds a task to the relevant job specifications in the batch.

        If a `document_type` is provided, the task will be added to all job specifications
        matching that document type. If no `document_type` is provided, the task will be added
        to all job specifications in the batch.

        Parameters
        ----------
        task : Task
            The task to add. Must derive from the `nv_ingest_client.primitives.Task` class.

        document_type : str, optional
            The document type used to filter job specifications. If not provided, the
            `document_type` is inferred from the task, or the task is applied to all job specifications.
        """
        all_tasks = {}
        for file_type, job_specs in self._file_type_to_job_spec.items():
            if not job_specs:
                continue
            # All job specs under the same file type should have the same tasks.
            tasks = job_specs[0]._tasks
            if not tasks:
                continue
            all_tasks[file_type] = tasks
        return all_tasks
