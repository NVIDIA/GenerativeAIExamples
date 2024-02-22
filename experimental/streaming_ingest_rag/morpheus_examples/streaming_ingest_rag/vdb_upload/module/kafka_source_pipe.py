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


from morpheus.modules.general.monitor import MonitorLoaderFactory
from morpheus.modules.preprocess.deserialize import DeserializeLoaderFactory
from morpheus.modules.input.rss_source import RSSSourceLoaderFactory
from morpheus.utils.module_utils import ModuleLoaderFactory
from morpheus.utils.module_utils import register_module

from vdb_upload.module.kafka_source_module import KafkaSourceLoaderFactory
from vdb_upload.module.vdb_resource_tagging_module import VDBResourceTaggingLoaderFactory
from vdb_upload.module.web_scraper_module import WebScraperLoaderFactory
from vdb_upload.module.schema_transform import SchemaTransformLoaderFactory
from vdb_upload.schemas.rss_source_pipe_schema import RSSSourcePipeSchema
from vdb_upload.schemas.kafka_source_pipe_schema import KafkaSourcePipeSchema
from vdb_upload import module


logger = logging.getLogger(__name__)

KafkaSourcePipeLoaderFactory = ModuleLoaderFactory("kafka_source_pipe", "morpheus_examples_llm", KafkaSourcePipeSchema)


@register_module("kafka_source_pipe", "morpheus_examples_llm")
def _kafka_source_pipe(builder: mrc.Builder, default_transform="raw_chunker"):
    """
    Sets up a pipeline for processing kafka sources.

    This function configures a pipeline that subscribes to a kafka topic, processes received content
    based on specified configurations, and outputs the processed data. It integrates modules for
    kafka sourcing, content extraction, and schema transformation, along with monitoring
    at various stages.

    Parameters
    ----------
    builder : mrc.Builder
        The Morpheus builder to which the pipeline modules will be added.
    default_transform : str
        The default extractor is not provided.

    Notes
    -----
    The module configuration can include the following parameters:

    - **kafka_source_config**: Configuration for the kafka source module.
      - **stage_config**: Source stage level configuration.
        - **enable_monitor**: Boolean to enable monitoring.
        - **namespace**: Name of namespace of stage modules.
        - **module_id**: Name of source module.
        - **module_output_id**: Name of output port of source module.
        - **transform_type**: Name of module to transform data.                                
      - **deserialize_config**: Deserialization module configurations.
        - output_batch_size: Number of elements per batch emitted from source
      - **kafka_config**: Kafka module configurations.
        - **max_batch_size**: Number of kafka messages per batch emitted from kafka source module.
        - **bootstrap_servers**: URL to a Kafka broker that can serve data.
        - **input_topic**: Name of topic containing messages to process.
        - **group_id**: Consumer group this worker/stage will belong to.
        - **poll_interval**: How often to poll Kafka for new data (pandas format).
        - **disable_commit**: Boolean to control possible arrival of duplicate messages.        
        - **disable_pre_filtering**: Boolean controling skipping committing messages as they are pulled off the server.
        - **auto_offset_reset**: Decision to consume from the beginning of a topic partition or only new messages.
        - **stop_after**: Number of records before stopping ingestion of new messages.
        - **async_commits**: Boolean to decided to asynchronously acknowledge consuming Kafka messages.
      - **extractor_config**: Provide extractor specific parameters.
        - **kwargs**: Keyword arguments used for extractor specific parameters.
      - **vdb_config**: Vector Database parameters.
        - **vdb_resource_name**: Name of the Milvus database collection to write vectors.

    The pipeline connects these modules in the following order:
    Kafka Source -> Content Extractor -> Schema Transform -> Deserialize,
    with monitoring at each stage. The content extraction method is determined
    by pipeline configuration.
    """    

    # Load and validate the module configuration from the builder
    module_config = builder.get_current_module_config()
    kafka_source_config = module_config.get("kafka_config", {})
    
    try:
        validated_config = KafkaSourcePipeSchema(**kafka_source_config)
    except ValidationError as e:
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid Kafka source configuration: {error_messages}"
        logger.error(log_error_message)
        raise ValueError(log_error_message)

    enable_monitor = validated_config.stage_config.enable_monitor

    kafka_source_loader = KafkaSourceLoaderFactory.get_instance(
        "kafka_source", validated_config.kafka_config)

    transform_type = validated_config.stage_config.transform_type
    transform_config_key = f"{transform_type}_config"

    if not hasattr(module, transform_type):
        transform_type = default_transform

    transform_loader = getattr(module, transform_type).get_instance(
        transform_type, {transform_config_key: getattr(validated_config, transform_config_key)})

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
                "from": "payload", "dtype": "str", "op_type": "rename"
            }
        }
    }

    schema_transform_loader = SchemaTransformLoaderFactory.get_instance("schema_transform", transform_config) 

    deserialize_loader = DeserializeLoaderFactory.get_instance(
        "deserialize", {
            "batch_size": validated_config.deserialize_config.output_batch_size, "message_type": "ControlMessage"
        })           

    vdb_resource_tagging_loader = VDBResourceTaggingLoaderFactory.get_instance(
        "vdb_resource_tagging", {"vdb_resource_name": validated_config.vdb_config.vdb_resource_name})   

    monitor_0_loader = MonitorLoaderFactory.get_instance(
        "monitor_0", {
            "description": f"KafkaSourcePipe Kafka Source ({transform_type})", 
            "unit": "messages", 
            "silence_monitors": not enable_monitor
        })    

    monitor_1_loader = MonitorLoaderFactory.get_instance(
        "monitor_1", {
            "description": f"KafkaSourcePipe Transform ({transform_type})", 
            "unit": "chunks",
            "silence_monitors": not enable_monitor
        })         

    monitor_2_loader = MonitorLoaderFactory.get_instance(
        "monitor_2", {
            "description": f"KafkaSourcePipe Schema Transform ({transform_type})", 
            "unit": "chunks", 
            "silence_monitors": not enable_monitor
        })            
        
    monitor_3_loader = MonitorLoaderFactory.get_instance(
        "monitor_3", {
            "description": f"KafkaSourcePipe Deserialize ({transform_type})", 
            "unit": "chunks", 
            "silence_monitors": not enable_monitor
        })          

    monitor_4_loader = MonitorLoaderFactory.get_instance(
        "monitor_4", {
            "description": f"KafkaSourcePipe VDB Tagger ({transform_type})", 
            "unit": "chunks", 
            "silence_monitors": not enable_monitor
        })

    # Load modules
    kafka_source_module = kafka_source_loader.load(builder=builder)
    monitor_0_module = monitor_0_loader.load(builder=builder)
    transform_loader_module = transform_loader.load(builder=builder)
    monitor_1_module = monitor_1_loader.load(builder=builder)
    schema_transform_module = schema_transform_loader.load(builder=builder) 
    monitor_2_module = monitor_2_loader.load(builder=builder)
    deserialize_module = deserialize_loader.load(builder=builder) 
    monitor_3_module = monitor_3_loader.load(builder=builder)    
    vdb_resource_tagging_module = vdb_resource_tagging_loader.load(builder=builder) 
    monitor_4_module = monitor_4_loader.load(builder=builder)      

    # Connect the modules: Kafka source -> Monitor
    builder.make_edge(kafka_source_module.output_port("output"), monitor_0_module.input_port("input"))
    builder.make_edge(monitor_0_module.output_port("output"), transform_loader_module.input_port("input"))
    builder.make_edge(transform_loader_module.output_port("output"), monitor_1_module.input_port("input"))
    builder.make_edge(monitor_1_module.output_port("output"), schema_transform_module.input_port("input"))
    builder.make_edge(schema_transform_module.output_port("output"), monitor_2_module.input_port("input"))
    builder.make_edge(monitor_2_module.output_port("output"), deserialize_module.input_port("input"))
    builder.make_edge(deserialize_module.output_port("output"), monitor_3_module.input_port("input")) 
    builder.make_edge(monitor_3_module.output_port("output"), vdb_resource_tagging_module.input_port("input"))
    builder.make_edge(vdb_resource_tagging_module.output_port("output"), monitor_4_module.input_port("input"))        

    # Register the final output of the transformation module
    builder.register_module_output("output", monitor_4_module.output_port("output"))
