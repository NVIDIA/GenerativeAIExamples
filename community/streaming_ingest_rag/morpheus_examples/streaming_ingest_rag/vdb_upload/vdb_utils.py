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
import typing

import pymilvus
import yaml

from morpheus.config import Config
from morpheus.config import PipelineModes
from morpheus.service.vdb.milvus_client import DATA_TYPE_MAP

logger = logging.getLogger(__name__)


def build_milvus_config(resource_schema_config: dict):
    schema_fields = []
    for field_data in resource_schema_config["schema_conf"]["schema_fields"]:
        field_data["dtype"] = DATA_TYPE_MAP.get(field_data["dtype"])
        field_schema = pymilvus.FieldSchema(**field_data)
        schema_fields.append(field_schema.to_dict())

    resource_schema_config["schema_conf"]["schema_fields"] = schema_fields

    return resource_schema_config


def is_valid_service(ctx, param, value):  # pylint: disable=unused-argument
    """
    Validate the provided vector database service name.

    Checks if the given vector database service name is supported and valid. This is used as a callback function
    for a CLI option to ensure that the user inputs a supported service name.

    Parameters
    ----------
    ctx : click.Context
        The context within which the command is being invoked.
    param : click.Parameter
        The parameter object that this function serves as a callback for.
    value : str
        The value of the parameter to validate.

    Returns
    -------
    str
        The validated and lowercased service name.

    Raises
    ------
    click.BadParameter
        If the provided service name is not supported or invalid.
    """
    from morpheus.service.vdb.utils import validate_service
    value = value.lower()
    return validate_service(service_name=value)


def merge_dicts(d1, d2):
    """
    Recursively merge two dictionaries.

    Nested dictionaries are merged instead of being replaced.
    Non-dict items in the second dictionary will override those in the first.

    Parameters
    ----------
    d1 : dict
        The first dictionary.
    d2 : dict
        The second dictionary, whose items will take precedence.

    Returns
    -------
    dict
        The merged dictionary.
    """
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            merge_dicts(d1[key], value)
        else:
            d1[key] = value
    return d1


def merge_configs(file_config, cli_config):
    """
    Merge two configuration dictionaries, prioritizing the file_config configuration.

    This function merges configurations provided from a file and the CLI, with the CLI configuration taking precedence
    in case of overlapping keys. Nested dictionaries are merged recursively.

    Parameters
    ----------
    file_config : dict
        The configuration dictionary loaded from a file.
    cli_config : dict
        The configuration dictionary provided via CLI arguments.

    Returns
    -------
    dict
        A merged dictionary with CLI configurations overriding file configurations where they overlap.
    """
    return merge_dicts(cli_config.copy(), {k: v for k, v in file_config.items() if v is not None})


def _build_default_rss_source(enable_cache,
                              enable_monitors,
                              interval_secs,
                              run_indefinitely,
                              stop_after,
                              vector_db_resource_name,
                              content_chunking_size,
                              rss_request_timeout_sec,
                              feed_inputs):
    return {
        'type': 'rss',
        'name': 'rss-cli',
        'config': {
            # RSS feeds can take a while to pull, smaller batch sizes allows the pipeline to feel more responsive
            "batch_size": 32,
            "output_batch_size": 2048,
            "cache_dir": "./.cache/http",
            "cooldown_interval_sec": interval_secs,
            "enable_cache": enable_cache,
            "enable_monitor": enable_monitors,
            "feed_input": feed_inputs if feed_inputs else build_rss_urls(),
            "interval_sec": interval_secs,
            "request_timeout_sec": rss_request_timeout_sec,
            "run_indefinitely": run_indefinitely,
            "vdb_resource_name": vector_db_resource_name,
            "web_scraper_config": {
                "chunk_size": content_chunking_size,
                "enable_cache": enable_cache,
            }
        }
    }


def _build_default_filesystem_source(enable_monitors,
                                     file_source,
                                     pipeline_batch_size,
                                     run_indefinitely,
                                     vector_db_resource_name,
                                     content_chunking_size,
                                     num_threads):
    return {
        'type': 'filesystem',
        'name': 'filesystem-cli',
        'config': {
            "batch_size": pipeline_batch_size,
            "enable_monitor": enable_monitors,
            "extractor_config": {
                "chunk_size": content_chunking_size,
                "num_threads": num_threads,
            },
            "filenames": file_source,
            "vdb_resource_name": vector_db_resource_name,
            "watch": run_indefinitely,
        }
    }


def build_cli_configs(source_type,
                      enable_cache,
                      embedding_size,
                      isolate_embeddings,
                      embedding_model_name,
                      enable_monitors,
                      file_source,
                      interval_secs,
                      pipeline_batch_size,
                      run_indefinitely,
                      stop_after,
                      vector_db_resource_name,
                      vector_db_service,
                      vector_db_uri,
                      content_chunking_size,
                      num_threads,
                      rss_request_timeout_sec,
                      model_max_batch_size,
                      model_fea_length,
                      triton_server_url,
                      feed_inputs):
    """
    Create configuration dictionaries based on CLI arguments.

    Constructs individual configuration dictionaries for various components of the data processing pipeline,
    such as source, embeddings, pipeline, tokenizer, and vector database configurations.

    Parameters
    ----------
    source_type : list of str
        Types of data sources (e.g., 'rss', 'filesystem').
    enable_cache : bool
        Flag to enable caching.
    embedding_size : int
        Size of the embeddings.
    isolate_embeddings : bool
        Flag to isolate embeddings.
    embedding_model_name : str
        Name of the embedding model.
    enable_monitors : bool
        Flag to enable monitor functionality.
    file_source : list of str
        File sources or paths to be processed.
    interval_secs : int
        Interval in seconds for operations.
    pipeline_batch_size : int
        Batch size for the pipeline.
    run_indefinitely : bool
        Flag to run the process indefinitely.
    stop_after : int
        Stop after a certain number of records.
    vector_db_resource_name : str
        Name of the resource in the vector database.
    vector_db_service : str
        Name of the vector database service.
    vector_db_uri : str
        URI for the vector database server.
    content_chunking_size : int
        Size of content chunks.
    num_threads : int
        Number of threads to use.
    rss_request_timeout_sec : float
        Timeout in seconds for RSS requests.
    model_max_batch_size : int
        Maximum batch size for the model.
    model_fea_length : int
        Feature length for the model.
    triton_server_url : str
        URL of the Triton server.
    feed_inputs : list of str
        RSS feed inputs.

    Returns
    -------
    tuple
        A tuple containing five dictionaries for source, embeddings, pipeline, tokenizer, and vector database configurations.
    """

    # Source Configuration
    cli_source_conf = {}
    if 'rss' in source_type:
        cli_source_conf['rss'] = _build_default_rss_source(enable_cache,
                                                           enable_monitors,
                                                           interval_secs,
                                                           run_indefinitely,
                                                           stop_after,
                                                           vector_db_resource_name,
                                                           content_chunking_size,
                                                           rss_request_timeout_sec,
                                                           feed_inputs)
    if 'filesystem' in source_type:
        cli_source_conf['filesystem'] = _build_default_filesystem_source(enable_monitors,
                                                                         file_source,
                                                                         pipeline_batch_size,
                                                                         run_indefinitely,
                                                                         vector_db_resource_name,
                                                                         content_chunking_size,
                                                                         num_threads)

    # Embeddings Configuration
    cli_embeddings_conf = {
        "feature_length": model_fea_length,
        "max_batch_size": model_max_batch_size,
        "model_kwargs": {
            "force_convert_inputs": True,
            "model_name": embedding_model_name,
            "server_url": triton_server_url,
            "use_shared_memory": False,
        },
        "num_threads": num_threads,
    }

    # Pipeline Configuration
    cli_pipeline_conf = {
        "edge_buffer_size": 128,
        "embedding_size": embedding_size,
        "feature_length": model_fea_length,
        "isolate_embeddings": isolate_embeddings,
        "max_batch_size": 256,
        "num_threads": num_threads,
        "pipeline_batch_size": pipeline_batch_size,
    }

    # Tokenizer Configuration
    cli_tokenizer_conf = {
        "model_name": "bert-base-uncased-hash",
        "model_kwargs": {
            "add_special_tokens": False,
            "column": "content",
            "do_lower_case": True,
            "truncation": True,
            "vocab_hash_file": "data/bert-base-uncased-hash.txt",
        }
    }

    # VDB Configuration
    cli_vdb_conf = {
        # Vector db upload has some significant transaction overhead, batch size here should be as large as possible
        'batch_size': 5120,
        'resource_name': vector_db_resource_name,
        'embedding_size': embedding_size,
        'recreate': False,
        'resource_schemas': {
            vector_db_resource_name:
                build_defualt_milvus_config(embedding_size) if (vector_db_service == 'milvus') else None,
        },
        'service': vector_db_service,
        'uri': vector_db_uri,
    }

    return cli_source_conf, cli_embeddings_conf, cli_pipeline_conf, cli_tokenizer_conf, cli_vdb_conf


def build_pipeline_config(pipeline_config: dict):
    """
    Construct a pipeline configuration object from a dictionary.

    Parameters
    ----------
    pipeline_config : dict
        A dictionary containing pipeline configuration parameters.

    Returns
    -------
    Config
        A pipeline configuration object populated with values from the input dictionary.

    Notes
    -----
    This function is responsible for mapping a dictionary of configuration parameters
    into a structured configuration object used by the pipeline.
    """

    config = Config()
    config.mode = PipelineModes.NLP

    embedding_size = pipeline_config.get('embedding_size')

    config.num_threads = pipeline_config.get('num_threads')
    config.pipeline_batch_size = pipeline_config.get('pipeline_batch_size')
    config.model_max_batch_size = pipeline_config.get('max_batch_size')
    config.feature_length = pipeline_config.get('feature_length')
    config.edge_buffer_size = pipeline_config.get('edge_buffer_size')
    config.class_labels = [str(i) for i in range(embedding_size)]

    return config


def build_final_config(vdb_conf_path,
                       cli_source_conf,
                       cli_embeddings_conf,
                       cli_pipeline_conf,
                       cli_tokenizer_conf,
                       cli_vdb_conf):
    """
    Load and merge configurations from the CLI and YAML file.

    This function combines the configurations provided via the CLI with those specified in a YAML file.
    If a YAML configuration file is specified and exists, it will merge its settings with the CLI settings,
    with the YAML settings taking precedence.

    Parameters
    ----------
    vdb_conf_path : str
        Path to the YAML configuration file.
    cli_source_conf : dict
        Source configuration provided via CLI.
    cli_embeddings_conf : dict
        Embeddings configuration provided via CLI.
    cli_pipeline_conf : dict
        Pipeline configuration provided via CLI.
    cli_tokenizer_conf : dict
        Tokenizer configuration provided via CLI.
    cli_vdb_conf : dict
        Vector Database (VDB) configuration provided via CLI.

    Returns
    -------
    dict
        A dictionary containing the final merged configuration for the pipeline, including source, embeddings,
        tokenizer, and VDB configurations.

    Notes
    -----
    The function prioritizes the YAML file configurations over CLI configurations. In case of overlapping
    settings, the values from the YAML file will overwrite those from the CLI.
    """
    final_config = {}

    # Load and merge configurations from the YAML file if it exists
    if vdb_conf_path:
        with open(vdb_conf_path, 'r') as file:
            vdb_pipeline_config = yaml.safe_load(file).get('vdb_pipeline', {})

        embeddings_conf = merge_configs(vdb_pipeline_config.get('embeddings', {}), cli_embeddings_conf)
        pipeline_conf = merge_configs(vdb_pipeline_config.get('pipeline', {}), cli_pipeline_conf)
        source_conf = vdb_pipeline_config.get('sources', []) + list(cli_source_conf.values())
        tokenizer_conf = merge_configs(vdb_pipeline_config.get('tokenizer', {}), cli_tokenizer_conf)
        vdb_conf = vdb_pipeline_config.get('vdb', {})
        resource_schema = vdb_conf.pop("resource_schema", None)

        if resource_schema:
            vdb_conf["resource_kwargs"] = build_milvus_config(resource_schema)
        vdb_conf = merge_configs(vdb_conf, cli_vdb_conf)

        pipeline_conf['embedding_size'] = vdb_conf.get('embedding_size', 384)

        final_config.update({
            'embeddings_config': embeddings_conf,
            'pipeline_config': build_pipeline_config(pipeline_conf),
            'source_config': source_conf,
            'tokenizer_config': tokenizer_conf,
            'vdb_config': vdb_conf,
        })
    else:
        # Use CLI configurations only
        final_config.update({
            'embeddings_config': cli_embeddings_conf,
            'pipeline_config': build_pipeline_config(cli_pipeline_conf),
            'source_config': list(cli_source_conf.values()),
            'tokenizer_config': cli_tokenizer_conf,
            'vdb_config': cli_vdb_conf,
        })

    # If no sources are specified either via CLI or in the yaml config, add a default RSS source
    if (not final_config['source_config']):
        final_config['source_config'].append(
            _build_default_rss_source(enable_cache=True,
                                      enable_monitors=True,
                                      interval_secs=60,
                                      run_indefinitely=True,
                                      stop_after=None,
                                      vector_db_resource_name="VDBUploadExample",
                                      content_chunking_size=128,
                                      rss_request_timeout_sec=30,
                                      feed_inputs=build_rss_urls()))

    return final_config


def build_defualt_milvus_config(embedding_size: int) -> typing.Dict[str, typing.Any]:
    """
    Builds the configuration for Milvus.

    This function creates a dictionary configuration for a Milvus collection.
    It includes the index configuration and the schema configuration, with
    various fields like id, title, link, summary, page_content, and embedding.

    Parameters
    ----------
    embedding_size : int
        The size of the embedding vector.

    Returns
    -------
    typing.Dict[str, Any]
        A dictionary containing the configuration settings for Milvus.
    """

    milvus_resource_kwargs = {
        "index_conf": {
            "field_name": "embedding",
            "metric_type": "L2",
            "index_type": "HNSW",
            "params": {
                "M": 8,
                "efConstruction": 64,
            },
        },
        "schema_conf": {
            "enable_dynamic_field": True,
            "schema_fields": [
                pymilvus.FieldSchema(name="id",
                                     dtype=pymilvus.DataType.INT64,
                                     description="Primary key for the collection",
                                     is_primary=True,
                                     auto_id=True).to_dict(),
                pymilvus.FieldSchema(name="title",
                                     dtype=pymilvus.DataType.VARCHAR,
                                     description="The title of the RSS Page",
                                     max_length=65_535).to_dict(),
                pymilvus.FieldSchema(name="source",
                                     dtype=pymilvus.DataType.VARCHAR,
                                     description="The URL of the RSS Page",
                                     max_length=65_535).to_dict(),
                pymilvus.FieldSchema(name="summary",
                                     dtype=pymilvus.DataType.VARCHAR,
                                     description="The summary of the RSS Page",
                                     max_length=65_535).to_dict(),
                pymilvus.FieldSchema(name="content",
                                     dtype=pymilvus.DataType.VARCHAR,
                                     description="A chunk of text from the RSS Page",
                                     max_length=65_535).to_dict(),
                pymilvus.FieldSchema(name="embedding",
                                     dtype=pymilvus.DataType.FLOAT_VECTOR,
                                     description="Embedding vectors",
                                     dim=embedding_size).to_dict(),
            ],
            "description": "Test collection schema"
        }
    }

    return milvus_resource_kwargs


def build_rss_urls() -> typing.List[str]:
    """
    Builds a list of RSS feed URLs.

    Returns
    -------
    typing.List[str]
        A list of URLs as strings, each pointing to a different RSS feed.
    """

    return [
        "https://www.theregister.com/security/headlines.atom",
        "https://isc.sans.edu/dailypodcast.xml",
        "https://threatpost.com/feed/",
        "http://feeds.feedburner.com/TheHackersNews?format=xml",
        "https://www.bleepingcomputer.com/feed/",
        "https://therecord.media/feed/",
        "https://blog.badsectorlabs.com/feeds/all.atom.xml",
        "https://krebsonsecurity.com/feed/",
        "https://www.darkreading.com/rss_simple.asp",
        "https://blog.malwarebytes.com/feed/",
        "https://msrc.microsoft.com/blog/feed",
        "https://securelist.com/feed",
        "https://www.crowdstrike.com/blog/feed/",
        "https://threatconnect.com/blog/rss/",
        "https://news.sophos.com/en-us/feed/",
        "https://www.us-cert.gov/ncas/current-activity.xml",
        "https://www.csoonline.com/feed",
        "https://www.cyberscoop.com/feed",
        "https://research.checkpoint.com/feed",
        "https://feeds.fortinet.com/fortinet/blog/threat-research",
        "https://www.mcafee.com/blogs/rss",
        "https://www.digitalshadows.com/blog-and-research/rss.xml",
        "https://www.nist.gov/news-events/cybersecurity/rss.xml",
        "https://www.sentinelone.com/blog/rss/",
        "https://www.bitdefender.com/blog/api/rss/labs/",
        "https://www.welivesecurity.com/feed/",
        "https://unit42.paloaltonetworks.com/feed/",
        "https://mandiant.com/resources/blog/rss.xml",
        "https://www.wired.com/feed/category/security/latest/rss",
        "https://www.wired.com/feed/tag/ai/latest/rss",
        "https://blog.google/threat-analysis-group/rss/",
        "https://intezer.com/feed/",
    ]
