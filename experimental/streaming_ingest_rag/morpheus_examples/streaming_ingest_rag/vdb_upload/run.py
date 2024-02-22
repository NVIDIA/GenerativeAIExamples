# Copyright (c) 2023-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os

import click
from vdb_upload.vdb_utils import build_cli_configs
from vdb_upload.vdb_utils import build_final_config
from vdb_upload.vdb_utils import is_valid_service

logger = logging.getLogger(__name__)


@click.group(name=__name__)
def run():
    pass


@run.command()
@click.option(
    "--content_chunking_size",
    default=512,  # Set a sensible default value
    type=click.IntRange(min=1),  # Ensure that only positive integers are valid
    help="The size of content chunks for processing.")
@click.option(
    "--embedding_size",
    default=384,
    type=click.IntRange(min=1),
    help="Output size of the embedding model",
)
@click.option(
    "--enable_cache",
    is_flag=True,
    default=False,
    help="Enable caching of RSS feed request data.",
)
@click.option("--enable_monitors", is_flag=True, default=False, help="Enable or disable monitor functionality.")
@click.option('--file_source', multiple=True, default=[], type=str, help='List of file sources/paths to be processed.')
@click.option('--feed_inputs', multiple=True, default=[], type=str, help='List of RSS source feeds to process.')
@click.option(
    "--interval_secs",
    default=600,
    type=click.IntRange(min=1),
    help="Interval in seconds between fetching new feed items.",
)
@click.option("--isolate_embeddings",
              is_flag=True,
              default=False,
              help="Whether to fetch all data prior to executing the rest of the pipeline.")
@click.option(
    "--model_fea_length",
    default=512,
    type=click.IntRange(min=1),
    help="Features length to use for the model",
)
@click.option(
    "--model_max_batch_size",
    default=64,
    type=click.IntRange(min=1),
    help="Max batch size to use for the model",
)
@click.option(
    "--embedding_model_name",
    required=True,
    default='all-MiniLM-L6-v2',
    help="The name of the model that is deployed on Triton server",
)
@click.option(
    "--num_threads",
    default=os.cpu_count(),
    type=click.IntRange(min=1),
    help="Number of internal pipeline threads to use",
)
@click.option(
    "--pipeline_batch_size",
    default=8192,
    type=click.IntRange(min=1),
    help=("Internal batch size for the pipeline. Can be much larger than the model batch size. "
          "Also used for Kafka consumers"),
)
@click.option(
    "--run_indefinitely",
    is_flag=True,
    default=False,
    help="Indicates whether the process should run continuously.",
)
@click.option(
    "--rss_request_timeout_sec",
    default=2.0,  # Set a default value, adjust as needed
    type=click.FloatRange(min=0.0),  # Ensure that only non-negative floats are valid
    help="Timeout in seconds for RSS feed requests.")
@click.option("--source_type",
              multiple=True,
              type=click.Choice(['rss', 'filesystem'], case_sensitive=False),
              default=[],
              show_default=True,
              help="The type of source to use. Can specify multiple times for different source types.")
@click.option(
    "--stop_after",
    default=0,
    type=click.IntRange(min=0),
    help="Stop after emitting this many records from the RSS source stage. Useful for testing. Disabled if `0`",
)
@click.option(
    "--triton_server_url",
    type=str,
    default="triton:8001",
    help="Triton server URL.",
)
@click.option(
    "--vdb_config_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    default=None,
    help="Path to a YAML configuration file.",
)
@click.option(
    "--vector_db_resource_name",
    type=str,
    default="VDBUploadExample",
    help="The identifier of the resource on which operations are to be performed in the vector database.",
)
@click.option(
    "--vector_db_service",
    type=str,
    default="milvus",
    callback=is_valid_service,
    help="Name of the vector database service to use.",
)
@click.option(
    "--vector_db_uri",
    type=str,
    default="http://milvus:19530",
    help="URI for connecting to Vector Database server.",
)
def pipeline(**kwargs):
    """
    Configure and run the data processing pipeline based on the specified command-line options.

    This function initializes and runs the data processing pipeline using configurations provided
    via command-line options. It supports customization for various components of the pipeline such as
    source type, embedding model, and vector database parameters.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments containing command-line options.

    Returns
    -------
    The result of the internal pipeline function call.
    """
    vdb_config_path = kwargs.pop('vdb_config_path', None)
    cli_source_conf, cli_embed_conf, cli_pipe_conf, cli_tok_conf, cli_vdb_conf = build_cli_configs(**kwargs)
    final_config = build_final_config(vdb_config_path,
                                      cli_source_conf,
                                      cli_embed_conf,
                                      cli_pipe_conf,
                                      cli_tok_conf,
                                      cli_vdb_conf)

    # Call the internal pipeline function with the final config dictionary
    from .pipeline import pipeline as _pipeline
    return _pipeline(**final_config)


@run.command()
@click.option(
    "--model_name",
    required=True,
    default='all-MiniLM-L6-v2',
    help="The name of the model that is deployed on Triton server",
)
@click.option(
    "--save_cache",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
    help="Location to save the cache to",
)
def langchain(**kwargs):
    from .langchain import chain

    return chain(**kwargs)


@run.command()
@click.option(
    "--model_name",
    required=True,
    default='all-MiniLM-L6-v2',
    help="The name of the model that is deployed on Triton server",
)
@click.option(
    "--model_seq_length",
    default=512,
    type=click.IntRange(min=1),
    help="Accepted input size of the text tokens",
)
@click.option(
    "--max_batch_size",
    default=256,
    type=click.IntRange(min=1),
    help="Max batch size for the model config",
)
@click.option(
    "--triton_repo",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory of the Triton Model Repo where the model will be saved",
)
@click.option(
    "--output_model_name",
    default=None,
    help="Overrides the model name that is used in triton. Defaults to `model_name`",
)
def export_triton_model(**kwargs):
    from .export_model import build_triton_model

    return build_triton_model(**kwargs)
