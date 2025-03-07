<!--
SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
All rights reserved.
SPDX-License-Identifier: Apache-2.0
-->

# NV-Ingest-Client

NV-Ingest-Client is a tool designed for efficient ingestion and processing of large datasets. It provides both a Python API and a command-line interface to cater to various ingestion needs.

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
   - [CLI Tool](#cli-tool)
   - [API Libraries](#api-libraries)
3. [Command Line Interface (CLI)](#command-line-interface-cli)
   - [Command Overview](#command-overview)
   - [Options](#options)
4. [Examples](#examples)

## Installation

To install NV-Ingest-Client, run the following command in your terminal:

```bash
pip install [REPO_ROOT]/client
```

This command installs both the API libraries and the `nv-ingest-cli` tool which can subsequently be called from the
command line.

## API Libraries

### nv_ingest_client.primitives.jobs

#### JobSpec

Specification for creating a job for submission to the nv-ingest microservice.

- **Parameters**:

  - `payload` (Dict): The payload data for the job.
  - `tasks` (Optional[List], optional): A list of tasks to be added to the job. Defaults to None.
  - `source_id` (Optional[str], optional): An identifier for the source of the job. Defaults to None.
  - `source_name` (Optional[str], optional): A name for the source of the job. Defaults to None.
  - `document_type` (Optional[str], optional): Type of the document. Defaults to 'txt'.
  - `job_id` (Optional[Union[UUID, str]], optional): A unique identifier for the job. Defaults to a new UUID.
  - `extended_options` (Optional[Dict], optional): Additional options for job processing. Defaults to None.

- **Attributes**:

  - `_payload` (Dict): Storage for the payload data.
  - `_tasks` (List): Storage for the list of tasks.
  - `_source_id` (str): Storage for the source identifier.
  - `_job_id` (UUID): Storage for the job's unique identifier.
  - `_extended_options` (Dict): Storage for the additional options.

- **Methods**:

  - **to_dict() -> Dict**:
    - **Description**: Converts the job specification to a dictionary for JSON serialization.
    - **Returns**: `Dict`: Dictionary representation of the job specification.
  - **add_task(task)**:
    - **Description**: Adds a task to the job specification.
    - **Parameters**:
      - `task`: The task to be added. Assumes the task has a `to_dict()` method.
    - **Raises**:
      - `ValueError`: If the task does not have a `to_dict()` method or is not an instance of `Task`.

- **Properties**:

  - `payload`: Getter/Setter for the payload data.
  - `job_id`: Getter/Setter for the job's unique identifier.
  - `source_id`: Getter/Setter for the source identifier.
  - `source_name`: Getter/Setter for the source name.

- **Example Usage**:
  ```python
  job_spec = JobSpec(
      payload={"data": "Example data"},
      tasks=[extract_task, split_task],
      source_id="12345",
      job_id="abcd-efgh-ijkl-mnop",
      extended_options={"tracing_options": {"trace": True}}
  )
  print(job_spec.to_dict())
  ```

### nv_ingest_client.primitives.tasks

#### Task Factory

- **Function**: `task_factory(task_type, **kwargs)`

  - **Description**: Factory method for creating task objects based on the provided task type. It dynamically selects
    the appropriate task class from a mapping and initializes it with any additional keyword arguments.
  - **Parameters**:
    - `task_type` (TaskType or str): The type of the task to create. Can be an enum member of `TaskType` or a string
      representing a valid task type.
    - `**kwargs` (dict): Additional keyword arguments to pass to the task's constructor.
  - **Returns**:
    - `Task`: An instance of the task corresponding to the given task type.
  - **Raises**:
    - `ValueError`: If an invalid task type is provided, or if any unexpected keyword arguments are passed that do
      not match the task constructor's parameters.

- **Example**:
  ```python
  # Assuming TaskType has 'Extract' and 'Split' as valid members and corresponding classes are defined.
  extract_task = task_factory('extract', document_type='PDF', extract_text=True)
  split_task = task_factory('split', split_by='sentence', split_length=100)
  ```

#### ExtractTask

Object for document extraction tasks, extending the `Task` class.

- **Method**: `__init__(document_type, extract_method='pdfium', extract_text=False, extract_images=False,
extract_tables=False)`

  - **Parameters**:
    - `document_type`: Type of document.
    - `extract_method`: Method used for extraction. Default is 'pdfium'.
    - `extract_text`: Boolean indicating if text should be extracted. Default is False.
    - `extract_images`: Boolean indicating if images should be extracted. Default is False.
    - `extract_tables`: Boolean indicating if tables should be extracted. Default is False.
  - **Description**: Sets up configuration for the extraction task.

- **Method: `to_dict()`**
  - **Description**: Converts task details to a dictionary for submission to message client. Includes handling for
    specific
    methods and document types.
  - **Returns**: `Dict`: Dictionary containing task type and properties.

- **Example**:
  ```python
  extract_task = ExtractTask(
    document_type=file_type,
    extract_text=True,
    extract_images=True,
    extract_tables=True
  )
  ```

#### SplitTask

Object for document splitting tasks, extending the `Task` class.

- **Method**: `__init__(split_by=None, split_length=None, split_overlap=None, max_character_length=None,
sentence_window_size=None)`
  - **Parameters**:
    - `split_by`: Criterion for splitting, e.g., 'word', 'sentence', 'passage'.
    - `split_length`: The length of each split segment.
    - `split_overlap`: Overlap length between segments.
    - `max_character_length`: Maximum character length for a split.
    - `sentence_window_size`: Window size for sentence-based splits.
  - **Description**: Sets up configuration for the splitting task.
- **Method: `to_dict()`**
  - **Description**: Converts task details to a dictionary for submission to message client.
  - **Returns**: `Dict`: Dictionary containing task type and properties.

- **Example**:
  ```python
  split_task = SplitTask(
      split_by="word",
      split_length=300,
      split_overlap=10,
      max_character_length=5000,
      sentence_window_size=0,
  )
  ```

### nv_ingest_client.client.client

The `NvIngestClient` class provides a comprehensive suite of methods to handle job submission and retrieval processes
efficiently. Below are the public methods available:

### Initialization

- **`__init__`**:
  Initializes the NvIngestClient with customizable client allocator and Redis configuration.
  - **Parameters**:
    - `message_client_allocator`: A callable that returns an instance of the client used for communication.
    - `message_client_hostname`: Hostname of the message client server. Defaults to "localhost".
    - `message_client_port`: Port number of the message client server. Defaults to 7670.
    - `message_client_kwargs`: Additional keyword arguments for the message client.
    - `msg_counter_id`: Redis key for tracking message counts. Defaults to "nv-ingest-message-id".
    - `worker_pool_size`: Number of worker processes in the pool. Defaults to 1.

- **Example**:
  ```python
  client = NvIngestClient(
    message_client_hostname="localhost", # Host where nv-ingest-ms-runtime is running
    message_client_port=7670 # REST port, defaults to 7670
  )
  ```

## Submission Methods

### submit_job

Submits a job to a specified job queue. This method can optionally wait for a response if blocking is set to True.

- **Parameters**:
  - `job_id`: The unique identifier of the job to be submitted.
  - `job_queue_id`: The ID of the job queue where the job will be submitted.
- **Returns**:
  - Optional[Dict]: The job result if blocking is True and a result is available before the timeout, otherwise None.
- **Raises**:
  - Exception: If submitting the job fails.

- **Example**:
  ```python
  client.submit_job(job_id, "morpheus_task_queue")
  ```

### submit_jobs

Submits multiple jobs to a specified job queue. This method does not wait for any of the jobs to complete.

- **Parameters**:
  - `job_ids`: A list of job IDs to be submitted.
  - `job_queue_id`: The ID of the job queue where the jobs will be submitted.
- **Returns**:
  - List[Union[Dict, None]]: A list of job results if blocking is True and results are available before the timeout,
    otherwise None.

- **Example**:
  ```python
  client.submit_jobs([job_id0, job_id1], "morpheus_task_queue")
  ```

### submit_job_async

Asynchronously submits one or more jobs to a specified job queue using a thread pool. This method handles both single
job ID or a list of job IDs.

- **Parameters**:
  - `job_ids`: A single job ID or a list of job IDs to be submitted.
  - `job_queue_id`: The ID of the job queue where the jobs will be submitted.
- **Returns**:
  - Dict[Future, str]: A dictionary mapping futures to their respective job IDs for later retrieval of outcomes.
- **Notes**:
  - This method queues the jobs for asynchronous submission and returns a mapping of futures to job IDs.
  - It does not wait for any of the jobs to complete.
  - Ensure that each job is in the proper state before submission.

- **Example**:
  ```python
  client.submit_job_async(job_id, "morpheus_task_queue")
  ```

## Job Retrieval

### fetch_job_result

- **Description**: Fetches the job result from a message client, handling potential errors and state changes.
- **Method**: `fetch_job_result(job_id, timeout=10, data_only=True)`
- **Parameters**:
  - `job_id` (str): The identifier of the job.
  - `timeout` (float, optional): Timeout for the fetch operation in seconds. Defaults to 10.
  - `data_only` (bool, optional): If true, only returns the data part of the job result.
- **Returns**:
  - Tuple[Dict, str]: The job result and the job ID.
- **Raises**:
  - `ValueError`: If there is an error in decoding the job result.
  - `TimeoutError`: If the fetch operation times out.
  - `Exception`: For all other unexpected issues.

- **Example**:
  ```python
  job_id = client.add_job(job_spec)
  client.submit_job(job_id, TASK_QUEUE)
  generated_metadata = client.fetch_job_result(
      job_id, timeout=DEFAULT_JOB_TIMEOUT
  )
  ```

### fetch_job_result_async

- **Description**: Fetches job results for a list or a single job ID asynchronously and returns a mapping of futures to
  job IDs.
- **Method**: `fetch_job_result_async(job_ids, timeout=10, data_only=True)`
- **Parameters**:
  - `job_ids` (Union[str, List[str]]): A single job ID or a list of job IDs.
  - `timeout` (float, optional): Timeout for fetching each job result, in seconds. Defaults to 10.
  - `data_only` (bool, optional): Whether to return only the data part of the job result.
- **Returns**:
  - Dict[Future, str]: A dictionary mapping each future to its corresponding job ID.
- **Raises**:
  - No explicit exceptions raised but leverages the exceptions from `fetch_job_result`.

- **Example**:
  ```python
  job_id = client.add_job(job_spec)
  client.submit_job(job_id, TASK_QUEUE)
  generated_metadata = client.fetch_job_result_async(
      job_id, timeout=DEFAULT_JOB_TIMEOUT
  )
  ```

## Job and Task Management

### job_count

- **Description**: Returns the number of jobs currently tracked by the client.
- **Method**: `job_count()`
- **Returns**: Integer representing the total number of jobs.

- **Example**:
  ```python
  client.job_count()
  ```

### add_job

- **Description**: Adds a job specification to the job tracking system.
- **Method**: `add_job(job_spec)`
- **Parameters**:
  - `job_spec` (JobSpec, optional): The job specification to add. If not provided, a new job ID will be generated.
- **Returns**: String representing the job ID of the added job.
- **Raises**:
  - `ValueError`: If a job with the specified job ID already exists.

- **Example**:
  ```python
  extract_task = ExtractTask(
    document_type=file_type,
    extract_text=True,
    extract_images=True,
    extract_tables=True,
    text_depth="document",
    extract_tables_method="yolox",
  )
  job_spec.add_task(extract_task)
  job_id = client.add_job(job_spec)
  ```

### create_job

- **Description**: Creates a new job with specified parameters and adds it to the job tracking dictionary.
- **Method**: `create_job(payload, source_id, source_name, document_type, tasks, job_id, extended_options)`
- **Parameters**:
  - `payload` (str): The payload associated with the job.
  - `source_id` (str): The source identifier for the job.
  - `source_name` (str): The unique name of the job's source data.
  - `document_type` (str, optional): The type of document to be processed.
  - `tasks` (list, optional): A list of tasks to be associated with the job.
  - `job_id` (uuid.UUID | str, optional): The unique identifier for the job.
  - `extended_options` (dict, optional): Additional options for job creation.
- **Returns**: String representing the job ID.
- **Raises**:
  - `ValueError`: If a job with the specified job ID already exists.

### add_task

- **Description**: Adds a task to an existing job.
- **Method**: `add_task(job_id, task)`
- **Parameters**:
  - `job_id` (str): The job ID to which the task will be added.
  - `task` (Task): The task to add.
- **Raises**:
  - `ValueError`: If the job does not exist or is not in the correct state.

- **Example**:
  ```python
  job_spec = JobSpec(
      document_type=file_type,
      payload=file_content,
      source_id=SAMPLE_PDF,
      source_name=SAMPLE_PDF,
      extended_options={
          "tracing_options": {
              "trace": True,
              "ts_send": time.time_ns(),
          }
      },
  )
  extract_task = ExtractTask(
      document_type=file_type,
      extract_text=True,
      extract_images=True,
      extract_tables=True,
      text_depth="document",
      extract_tables_method="yolox",
  )
  job_spec.add_task(extract_task)
  ```

### create_task

- **Description**: Creates a task with specified parameters and adds it to an existing job.
- **Method**: `create_task(job_id, task_type, task_params)`
- **Parameters**:
  - `job_id` (uuid.UUID | str): The unique identifier of the job.
  - `task_type` (TaskType): The type of the task.
  - `task_params` (dict, optional): Parameters for the task.
- **Raises**:
  - `ValueError`: If the job does not exist or if an attempt is made to modify a job after its submission.

- **Example**:
  ```python
  job_id = client.add_job(job_spec)
  client.create_task(job_id, DedupTask, {content_type: "image", filter: True})
  ```

## CLI Tool

After installation, you can use the `nv-ingest-cli` tool from the command line to manage and process datasets.

### CLI Options

Here are the options provided by the CLI, explained:

- `--batch_size`: Specifies the number of documents to process in a single batch. Default is 10. Must be 1 or more.
- `--doc`: Adds a new document to be processed. Supports multiple entries. Files must exist.
- `--dataset`: Specifies the path to a dataset definition file.
- `--client`: Sets the client type with choices including REST, Redis, Kafka. Default is Redis.
- `--client_host`: Specifies the DNS name or URL for the endpoint.
- `--client_port`: Sets the port number for the client endpoint.
- `--client_kwargs`: Provides additional arguments to pass to the client. Default is `{}`.
- `--concurrency_n`: Defines the number of inflight jobs to maintain at one time. Default is 1.
- `--dry_run`: Enables a dry run without executing actions.
- `--output_directory`: Specifies the output directory for results.
- `--log_level`: Sets the log level. Choices are DEBUG, INFO, WARNING, ERROR, CRITICAL. Default is INFO.
- `--shuffle_dataset`: Shuffles the dataset before processing if enabled. Default is true.
- `--task`: Allows for specification of tasks in JSON format. Supports multiple tasks.
- `--collect_profiling_traces`: Collect the tracing profile for the run after processing.
- `--zipkin_host`: Host used to connect to Zipkin to gather tracing profiles.
- `--zipkin_port`: Port used to connect to Zipkin to gether tracing profiles.

## Examples

You can find a notebook with examples using the client [here](client_examples/examples/cli_client_usage.ipynb).
