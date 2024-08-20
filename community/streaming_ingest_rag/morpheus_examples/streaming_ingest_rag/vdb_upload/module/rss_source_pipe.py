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

import mrc
from pydantic import ValidationError
from vdb_upload.module.schema_transform import SchemaTransformLoaderFactory
from vdb_upload.schemas.rss_source_pipe_schema import RSSSourcePipeSchema

from morpheus.modules.general.monitor import MonitorLoaderFactory
from morpheus.modules.input.rss_source import RSSSourceLoaderFactory
from morpheus.modules.preprocess.deserialize import DeserializeLoaderFactory
from morpheus.utils.module_utils import ModuleLoaderFactory
from morpheus.utils.module_utils import register_module

from vdb_upload.module.vdb_resource_tagging_module import VDBResourceTaggingLoaderFactory
from vdb_upload.module.web_scraper_module import WebScraperLoaderFactory

logger = logging.getLogger(__name__)

RSSSourcePipeLoaderFactory = ModuleLoaderFactory("rss_source_pipe", "morpheus_examples_llm", RSSSourcePipeSchema)


@register_module("rss_source_pipe", "morpheus_examples_llm")
def _rss_source_pipe(builder: mrc.Builder):
    """
    Creates a pipeline for processing RSS feeds.

    This function sets up a pipeline that takes RSS feed data, scrapes web content
    based on the feed, and then outputs the scraped data. It integrates modules like RSS source,
    web scraper, and deserializer, along with monitoring for each stage.

    Parameters
    ----------
    builder : mrc.Builder
        The Morpheus builder to which the pipeline modules will be added.

    Notes
    -----
    The module configuration can include the following parameters:

    - **rss_config**: Configuration for the RSS source module.
      - **batch_size**: Number of RSS feed items to process in each batch.
      - **cache_dir**: Directory for caching RSS feed data.
      - **cooldown_interval_sec**: Cooldown interval in seconds between fetches.
      - **enable_cache**: Boolean to enable caching of feed data.
      - **enable_monitor**: Boolean to enable monitoring for this module.
      - **feed_input**: List of RSS feed URLs to process.
      - **interval_sec**: Interval in seconds for fetching new feed items.
      - **request_timeout_sec**: Timeout in seconds for RSS feed requests.
      - **run_indefinitely**: Boolean to indicate continuous running.
      - **stop_after**: Number of records to process before stopping (0 for indefinite).
      - **web_scraper_config**: Configuration for the web scraper module.
        - **chunk_overlap**: Overlap size for chunks in web scraping.
        - **chunk_size**: Size of content chunks for processing.
        - **enable_cache**: Boolean to enable caching of scraped data.

    The pipeline connects these modules in the following order:
    RSS Source -> Web Scraper -> Deserializer, with monitoring at each stage.
    """

    # Load and validate the module configuration from the builder
    module_config = builder.get_current_module_config()
    rss_config = module_config.get("rss_config", {})
    try:
        validated_config = RSSSourcePipeSchema(**rss_config)
    except ValidationError as e:
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid RSS source configuration: {error_messages}"
        logger.error(log_error_message)
        raise ValueError(log_error_message)

    enable_monitor = validated_config.enable_monitor

    rss_source_config = {
        "feed_input": validated_config.feed_input,
        "run_indefinitely": validated_config.run_indefinitely,
        "batch_size": validated_config.batch_size,
        "enable_cache": validated_config.enable_cache,
        "cache_dir": validated_config.cache_dir,
        "cooldown_interval_sec": validated_config.cooldown_interval_sec,
        "request_timeout_sec": validated_config.request_timeout_sec,
        "interval_sec": validated_config.interval_sec,
        "stop_after_sec": validated_config.stop_after_sec,
    }
    rss_source_loader = RSSSourceLoaderFactory.get_instance("rss_source", {"rss_source": rss_source_config})

    web_scraper_loader = WebScraperLoaderFactory.get_instance(
        "web_scraper", {
            "web_scraper_config": validated_config.web_scraper_config,
        })

    transform_config = {
        "schema_transform_config": {
            "summary": {
                "dtype": "str", "op_type": "select"
            },
            "title": {
                "dtype": "str", "op_type": "select"
            },
            "content": {
                "from": "page_content", "dtype": "str", "op_type": "rename"
            },
            "source": {
                "from": "link", "dtype": "str", "op_type": "rename"
            }
        }
    }
    schema_transform_loader = SchemaTransformLoaderFactory.get_instance("schema_transform", transform_config)

    deserialize_loader = DeserializeLoaderFactory.get_instance(
        "deserialize", {
            "batch_size": validated_config.output_batch_size, "message_type": "ControlMessage"
        })

    vdb_resource_tagging_loader = VDBResourceTaggingLoaderFactory.get_instance(
        "vdb_resource_tagging", {"vdb_resource_name": validated_config.vdb_resource_name})

    monitor_0_loader = MonitorLoaderFactory.get_instance(
        "monitor_m1", {
            "description": "RSSSourcePipe RSS Source", "silence_monitors": not enable_monitor
        })
    monitor_1_loader = MonitorLoaderFactory.get_instance(
        "monitor_0", {
            "description": "RSSSourcePipe Web Scraper", "silence_monitors": not enable_monitor
        })
    monitor_2_loader = MonitorLoaderFactory.get_instance(
        "monitor_1", {
            "description": "RSSSourcePipe Transform", "silence_monitors": not enable_monitor
        })
    monitor_3_loader = MonitorLoaderFactory.get_instance(
        "monitor_2", {
            "description": "RSSSourcePipe Deserialize", "silence_monitors": not enable_monitor
        })

    # Load modules
    rss_source_module = rss_source_loader.load(builder=builder)
    monitor_0_loader = monitor_0_loader.load(builder=builder)
    web_scraper_module = web_scraper_loader.load(builder=builder)
    monitor_0_module = monitor_1_loader.load(builder=builder)
    transform_module = schema_transform_loader.load(builder=builder)
    monitor_1_module = monitor_2_loader.load(builder=builder)
    deserialize_module = deserialize_loader.load(builder=builder)
    vdb_resource_tagging_module = vdb_resource_tagging_loader.load(builder=builder)
    monitor_2_module = monitor_3_loader.load(builder=builder)

    # Connect the modules: RSS source -> Web scraper -> Schema transform
    builder.make_edge(rss_source_module.output_port("output"), monitor_0_loader.input_port("input"))
    builder.make_edge(monitor_0_loader.output_port("output"), web_scraper_module.input_port("input"))
    builder.make_edge(web_scraper_module.output_port("output"), monitor_0_module.input_port("input"))
    builder.make_edge(monitor_0_module.output_port("output"), transform_module.input_port("input"))
    builder.make_edge(transform_module.output_port("output"), monitor_1_module.input_port("input"))
    builder.make_edge(monitor_1_module.output_port("output"), deserialize_module.input_port("input"))
    builder.make_edge(deserialize_module.output_port("output"), vdb_resource_tagging_module.input_port("input"))
    builder.make_edge(vdb_resource_tagging_module.output_port("output"), monitor_2_module.input_port("input"))

    # Register the final output of the transformation module
    builder.register_module_output("output", monitor_2_module.output_port("output"))
