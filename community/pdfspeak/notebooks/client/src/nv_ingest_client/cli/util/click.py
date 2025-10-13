# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


import json
import logging
import os
import random
from enum import Enum
from pprint import pprint

import click
from nv_ingest_client.cli.util.processing import check_schema
from nv_ingest_client.primitives.tasks import CaptionTask
from nv_ingest_client.primitives.tasks import DedupTask
from nv_ingest_client.primitives.tasks import EmbedTask
from nv_ingest_client.primitives.tasks import ExtractTask
from nv_ingest_client.primitives.tasks import FilterTask
from nv_ingest_client.primitives.tasks import SplitTask
from nv_ingest_client.primitives.tasks import StoreEmbedTask
from nv_ingest_client.primitives.tasks import StoreTask
from nv_ingest_client.primitives.tasks import VdbUploadTask
from nv_ingest_client.primitives.tasks.caption import CaptionTaskSchema
from nv_ingest_client.primitives.tasks.chart_extraction import ChartExtractionSchema
from nv_ingest_client.primitives.tasks.chart_extraction import ChartExtractionTask
from nv_ingest_client.primitives.tasks.dedup import DedupTaskSchema
from nv_ingest_client.primitives.tasks.embed import EmbedTaskSchema
from nv_ingest_client.primitives.tasks.extract import ExtractTaskSchema
from nv_ingest_client.primitives.tasks.filter import FilterTaskSchema
from nv_ingest_client.primitives.tasks.split import SplitTaskSchema
from nv_ingest_client.primitives.tasks.store import StoreEmbedTaskSchema
from nv_ingest_client.primitives.tasks.store import StoreTaskSchema
from nv_ingest_client.primitives.tasks.table_extraction import TableExtractionSchema
from nv_ingest_client.primitives.tasks.table_extraction import TableExtractionTask
from nv_ingest_client.primitives.tasks.vdb_upload import VdbUploadTaskSchema
from nv_ingest_client.util.util import generate_matching_files

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ClientType(str, Enum):
    REST = "REST"
    REDIS = "REDIS"
    KAFKA = "KAFKA"


# Example TaskId validation set
VALID_TASK_IDS = {"task1", "task2", "task3"}

_MODULE_UNDER_TEST = "nv_ingest_client.cli.util.click"


def debug_print_click_options(ctx):
    """
    Retrieves all options from the Click context and pretty prints them.

    Parameters
    ----------
    ctx : click.Context
        The Click context object from which to retrieve the command options.
    """
    click_options = {}
    for param in ctx.command.params:
        if isinstance(param, click.Option):
            value = ctx.params[param.name]
            click_options[param.name] = value

    pprint(click_options)


def click_validate_file_exists(ctx, param, value):
    if not value:
        return []

    if isinstance(value, str):
        value = [value]
    else:
        value = list(value)

    for filepath in value:
        if not os.path.exists(filepath):
            raise click.BadParameter(f"File does not exist: {filepath}")

    return value


def click_validate_task(ctx, param, value):
    validated_tasks = {}
    validation_errors = []

    for task_str in value:
        task_split = task_str.split(":", 1)
        if len(task_split) != 2:
            task_id, json_options = task_str, "{}"
        else:
            task_id, json_options = task_split

        try:
            options = json.loads(json_options)

            if task_id == "split":
                task_options = check_schema(SplitTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, SplitTask(**task_options.dict()))]
            elif task_id == "extract":
                task_options = check_schema(ExtractTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}_{task_options.document_type}"
                new_task = [(new_task_id, ExtractTask(**task_options.dict()))]

                if task_options.extract_tables is True:
                    subtask_options = check_schema(TableExtractionSchema, {}, "table_data_extract", "{}")
                    new_task.append(("table_data_extract", TableExtractionTask(**subtask_options.dict())))

                if task_options.extract_charts is True:
                    subtask_options = check_schema(ChartExtractionSchema, {}, "chart_data_extract", "{}")
                    new_task.append(("chart_data_extract", ChartExtractionTask(**subtask_options.dict())))

            elif task_id == "store":
                task_options = check_schema(StoreTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, StoreTask(**task_options.dict()))]
            elif task_id == "store_embedding":
                task_options = check_schema(StoreEmbedTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, StoreEmbedTask(**task_options.dict()))]
            elif task_id == "caption":
                task_options = check_schema(CaptionTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, CaptionTask(**task_options.dict()))]
            elif task_id == "dedup":
                task_options = check_schema(DedupTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, DedupTask(**task_options.dict()))]
            elif task_id == "filter":
                task_options = check_schema(FilterTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, FilterTask(**task_options.dict()))]
            elif task_id == "embed":
                task_options = check_schema(EmbedTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, EmbedTask(**task_options.dict()))]
            elif task_id == "vdb_upload":
                task_options = check_schema(VdbUploadTaskSchema, options, task_id, json_options)
                new_task_id = f"{task_id}"
                new_task = [(new_task_id, VdbUploadTask(**task_options.dict()))]
            else:
                raise ValueError(f"Unsupported task type: {task_id}")

            if new_task_id in validated_tasks:
                raise ValueError(f"Duplicate task detected: {new_task_id}")

            logger.debug("Adding task: %s", new_task_id)
            for task_tuple in new_task:
                validated_tasks[task_tuple[0]] = task_tuple[1]
        except ValueError as e:
            validation_errors.append(str(e))

    if validation_errors:
        # Aggregate error messages with original values highlighted
        error_message = "\n".join(validation_errors)
        raise click.BadParameter(error_message)

    return validated_tasks


def click_validate_batch_size(ctx, param, value):
    if value < 1:
        raise click.BadParameter("Batch size must be >= 1.")
    return value


def pre_process_dataset(dataset_json: str, shuffle_dataset: bool):
    """
    Loads a dataset from a JSON file and optionally shuffles the list of files contained within.

    Parameters
    ----------
    dataset_json : str
        The path to the dataset JSON file.
    shuffle_dataset : bool, optional
        Whether to shuffle the dataset before processing. Defaults to True.

    Returns
    -------
    list
        The list of files from the dataset, possibly shuffled.
    """
    try:
        with open(dataset_json, "r") as f:
            file_source = json.load(f)
    except FileNotFoundError:
        raise click.BadParameter(f"Dataset JSON file not found: {dataset_json}")
    except json.JSONDecodeError:
        raise click.BadParameter(f"Invalid JSON format in file: {dataset_json}")

    # Extract the list of files and optionally shuffle them
    file_source = file_source.get("sampled_files", [])

    if shuffle_dataset:
        random.shuffle(file_source)

    return file_source


def click_match_and_validate_files(ctx, param, value):
    """
    Matches and validates files based on the provided file source patterns.

    Parameters
    ----------
    value : list of str
        A list containing file source patterns to match against.

    Returns
    -------
    list of str or None
        A list of matching file paths if any matches are found; otherwise, None.
    """

    if not value:
        return []

    matching_files = list(generate_matching_files(value))
    if not matching_files:
        logger.warning("No files found matching the specified patterns.")
        return []

    return matching_files
