# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


import json
import logging
import time
from io import BytesIO
from typing import List

import click
import pkg_resources
from nv_ingest_client.util.zipkin import collect_traces_from_zipkin, write_results_to_output_directory
from nv_ingest_client.cli.util.click import LogLevel
from nv_ingest_client.cli.util.click import click_match_and_validate_files
from nv_ingest_client.cli.util.click import click_validate_batch_size
from nv_ingest_client.cli.util.click import click_validate_file_exists
from nv_ingest_client.cli.util.click import click_validate_task
from nv_ingest_client.cli.util.processing import create_and_process_jobs
from nv_ingest_client.cli.util.processing import report_statistics
from nv_ingest_client.cli.util.system import configure_logging
from nv_ingest_client.cli.util.system import ensure_directory_with_permissions
from nv_ingest_client.client import NvIngestClient
from nv_ingest_client.message_clients.rest.rest_client import RestClient
from nv_ingest_client.message_clients.simple.simple_client import SimpleClient
from nv_ingest_client.util.dataset import get_dataset_files
from nv_ingest_client.util.dataset import get_dataset_statistics
from pkg_resources import DistributionNotFound
from pkg_resources import VersionConflict

try:
    NV_INGEST_VERSION = pkg_resources.get_distribution("nv_ingest").version
except (DistributionNotFound, VersionConflict):
    NV_INGEST_VERSION = "Unknown -- No Distribution found or Version conflict."

try:
    NV_INGEST_CLIENT_VERSION = pkg_resources.get_distribution("nv_ingest_client").version
except (DistributionNotFound, VersionConflict):
    NV_INGEST_CLIENT_VERSION = "Unknown -- No Distribution found or Version conflict."

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--batch_size",
    default=10,
    show_default=True,
    type=int,
    help="Batch size (must be >= 1).",
    callback=click_validate_batch_size,
)
@click.option(
    "--doc",
    multiple=True,
    default=None,
    type=click.Path(exists=False),
    help="Add a new document to be processed (supports multiple).",
    callback=click_match_and_validate_files,
)
@click.option(
    "--dataset",
    type=click.Path(exists=False),
    default=None,
    help="Path to a dataset definition file.",
    callback=click_validate_file_exists,
)
@click.option("--client_host", default="localhost", help="DNS name or URL for the endpoint.")
@click.option("--client_port", default=6397, type=int, help="Port for the client endpoint.")
@click.option("--client_kwargs", help="Additional arguments to pass to the client.", default="{}")
@click.option(
    "--client_type",
    default="rest",
    type=click.Choice(["rest", "simple"], case_sensitive=False),
    help="Client type used to connect to the ingest service.",
)
@click.option(
    "--concurrency_n", default=10, show_default=True, type=int, help="Number of inflight jobs to maintain at one time."
)
@click.option(
    "--document_processing_timeout",
    default=10,
    show_default=True,
    type=int,
    help="Timeout when waiting for a document to be processed.",
)
@click.option("--dry_run", is_flag=True, help="Perform a dry run without executing actions.")
@click.option("--fail_on_error", is_flag=True, help="Fail on error.")
@click.option("--output_directory", type=click.Path(), default=None, help="Output directory for results.")
@click.option(
    "--log_level",
    type=click.Choice([level.value for level in LogLevel], case_sensitive=False),
    default="INFO",
    show_default=True,
    help="Log level.",
)
@click.option(
    "--save_images_separately",
    is_flag=True,
    help="Save images separately from returned metadata. This can make metadata files more human readable",
)
@click.option(
    "--shuffle_dataset", is_flag=True, default=True, show_default=True, help="Shuffle the dataset before processing."
)
@click.option(
    "--task",
    multiple=True,
    callback=click_validate_task,
    help="""
\b
Task definitions in JSON format, allowing multiple tasks to be configured by repeating this option.
Each task must be specified with its type and corresponding options in the '[task_id]:{json_options}' format.

\b
Example:
  --task 'split:{"split_by":"page", "split_length":10}'
  --task 'extract:{"document_type":"pdf", "extract_text":true}'
  --task 'extract:{"document_type":"pdf", "extract_method":"doughnut"}'
  --task 'extract:{"document_type":"pdf", "extract_method":"unstructured_io"}'
  --task 'extract:{"document_type":"docx", "extract_text":true, "extract_images":true}'
  --task 'store:{"content_type":"image", "store_method":"minio", "endpoint":"minio:9000"}'
  --task 'embed:{"text":true, "tables":true}'
  --task 'vdb_upload'
  --task 'caption:{}'

\b
Tasks and Options:
- caption: Attempts to extract captions for unstructured images extracted from documents.
    Options:
      - api_key (str): API key for captioning service.
      Default: os.environ(NVIDIA_BUILD_API_KEY).'
      - endpoint_url (str): Endpoint URL for captioning service.
      Default: 'https://build.nvidia.com/meta/llama-3.2-90b-vision-instruct'.
      - prompt (str): Prompt for captioning service.
      Default: 'Caption the content of this image:'.
\b
- dedup: Identifies and optionally filters duplicate images in extraction.
    Options:
      - content_type (str): Content type to deduplicate ('image').
      - filter (bool): When set to True, duplicates will be filtered, otherwise, an info message will be added.
\b
- embed: Computes embeddings on multimodal extractions.
    Options:
    - filter_errors (bool): Flag to filter embedding errors. Optional.
    - tables (bool): Flag to create embeddings for table extractions. Optional.
    - text (bool): Flag to create embeddings for text extractions. Optional.
\b
- extract: Extracts content from documents, customizable per document type.
    Can be specified multiple times for different 'document_type' values.
    Options:
    - document_type (str): Document format ('pdf', 'docx', 'pptx', 'html', 'xml', 'excel', 'csv', 'parquet'). Required.
    - extract_charts (bool): Enables chart extraction. Default: False.
    - extract_images (bool): Enables image extraction. Default: False.
    - extract_method (str): Extraction technique. Defaults are smartly chosen based on 'document_type'.
    - extract_tables (bool): Enables table extraction. Default: False.
    - extract_text (bool): Enables text extraction. Default: False.
    - text_depth (str): Text extraction granularity ('document', 'page'). Default: 'document'.
        Note: this will affect the granularity of text extraction, and the associated metadata. ie. 'page' will extract
        text per page and you will get page-level metadata, 'document' will extract text for the entire document so
        elements like page numbers will not be associated with individual text elements.
\b
- filter: Identifies and optionally filters images above or below scale thresholds.
    Options:
      - content_type (str): Content type to filter ('image').
      - filter (bool): When set to True, filtered images will be excluded; otherwise, an info message will be added.
      - max_aspect_ratio (Union[float, int]): Maximum allowable aspect ratio of extracted image.
      - min_aspect_ratio (Union[float, int]): Minimum allowable aspect ratio of extracted image.
      - min_size (int): Minimum allowable size of extracted image.
\b
- split: Divides documents according to specified criteria.
    Options:
    - max_character_length (int): Maximum segment character count. No default.
    - sentence_window_size (int): Sentence window size. No default.
    - split_by (str): Criteria ('page', 'size', 'word', 'sentence'). No default.
    - split_length (int): Segment length. No default.
    - split_overlap (int): Segment overlap. No default.
\b
- store: Stores any images extracted from documents.
    Options:
    - images (bool): Flag to write extracted images to object store.
    - structured (bool): Flag to write extracted charts and tables to object store.
    - store_method (str): Storage type ('minio', ). Required.
\b
- vdb_upload: Uploads extraction embeddings to vector database.
\b
Note: The 'extract_method' automatically selects the optimal method based on 'document_type' if not explicitly stated.
""",
)
@click.option(
    "--collect_profiling_traces",
    is_flag=True,
    default=False,
    help="""
\b
If enabled the CLI will collect the 'profile' for each file that was submitted to the
nv-ingest REST endpoint for processing.

\b
Those `trace_id` values will be consolidated and then a subsequent request will be made to
Zipkin to collect the traces for each individual `trace_id`. The trace is rich with information
that can further breakdown the runtimes for each section of the codebase. This is useful
for locating portions of the system that might be bottlenecks for the overall runtimes.
""",
)
@click.option("--zipkin_host", default="localhost", help="DNS name or Zipkin API.")
@click.option("--zipkin_port", default=9411, type=int, help="Port for the Zipkin trace API")
@click.option("--version", is_flag=True, help="Show version.")
@click.pass_context
def main(
    ctx,
    batch_size: int,
    client_host: str,
    client_kwargs: str,
    client_port: int,
    client_type: str,
    concurrency_n: int,
    dataset: str,
    doc: List[str],
    document_processing_timeout: int,
    dry_run: bool,
    fail_on_error: bool,
    log_level: str,
    output_directory: str,
    save_images_separately: bool,
    shuffle_dataset: bool,
    collect_profiling_traces: bool,
    zipkin_host: str,
    zipkin_port: int,
    task: [str],
    version: [bool],
):
    if version:
        click.echo(f"nv-ingest     : {NV_INGEST_VERSION}")
        click.echo(f"nv-ingest-cli : {NV_INGEST_CLIENT_VERSION}")
        return

    try:
        configure_logging(logger, log_level)
        logging.debug(f"nv-ingest-cli:params:\n{json.dumps(ctx.params, indent=2, default=repr)}")

        docs = list(doc)
        if dataset:
            dataset = dataset[0]
            logger.info(f"Processing dataset: {dataset}")
            with open(dataset, "rb") as file:
                dataset_bytes = BytesIO(file.read())

            logger.debug(get_dataset_statistics(dataset_bytes))
            docs.extend(get_dataset_files(dataset_bytes, shuffle_dataset))

        logger.info(f"Processing {len(docs)} documents.")
        if output_directory:
            _msg = f"Output will be written to: {output_directory}"
            if dry_run:
                _msg = f"[Dry-Run] {_msg}"
            else:
                ensure_directory_with_permissions(output_directory)

            logger.info(_msg)

        if not dry_run:
            logging.debug(f"Creating message client: {client_host} and port: {client_port} -> {client_kwargs}")

            if client_type == "rest":
                client_allocator = RestClient
            elif client_type == "simple":
                client_allocator = SimpleClient
            else:
                raise ValueError(f"Unknown client type: {client_type}")

            ingest_client = NvIngestClient(
                message_client_allocator=client_allocator,
                message_client_hostname=client_host,
                message_client_port=client_port,
                message_client_kwargs=json.loads(client_kwargs),
                worker_pool_size=concurrency_n,
            )

            start_time_ns = time.time_ns()
            (total_files, trace_times, pages_processed, trace_ids) = create_and_process_jobs(
                files=docs,
                client=ingest_client,
                tasks=task,
                output_directory=output_directory,
                batch_size=batch_size,
                timeout=document_processing_timeout,
                fail_on_error=fail_on_error,
                save_images_separately=save_images_separately,
            )

            report_statistics(start_time_ns, trace_times, pages_processed, total_files)

            # Gather profiling data after processing has completed.
            if collect_profiling_traces:
                logger.info("Collecting profiling traces ....")
                trace_responses = collect_traces_from_zipkin(zipkin_host, zipkin_port, trace_ids, 1)

                # Log the responses to a file in the configured results --output_directory
                write_results_to_output_directory(output_directory, trace_responses)

    except Exception as err:
        logging.error(f"Error: {err}")
        raise


if __name__ == "__main__":
    main()
