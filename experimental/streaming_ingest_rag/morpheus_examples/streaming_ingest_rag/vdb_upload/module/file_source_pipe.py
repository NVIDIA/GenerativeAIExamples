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
from vdb_upload.schemas.file_source_pipe_schema import FileSourcePipeSchema

from morpheus.modules.general.monitor import MonitorLoaderFactory
from morpheus.modules.input.multi_file_source import MultiFileSourceLoaderFactory
from morpheus.modules.preprocess.deserialize import DeserializeLoaderFactory
from morpheus.utils.module_utils import ModuleLoaderFactory
from morpheus.utils.module_utils import register_module

from vdb_upload.module.content_extractor_module import ContentExtractorLoaderFactory
from vdb_upload.module.vdb_resource_tagging_module import VDBResourceTaggingLoaderFactory

logger = logging.getLogger(__name__)

FileSourcePipeLoaderFactory = ModuleLoaderFactory("file_source_pipe", "morpheus_examples_llm", FileSourcePipeSchema)


@register_module("file_source_pipe", "morpheus_examples_llm")
def _file_source_pipe(builder: mrc.Builder):
    """
    Sets up a pipeline for processing file sources.

    This function configures a pipeline that reads files, processes their content
    based on specified configurations, and outputs the processed data. It integrates modules for
    multi-file sourcing, file content extraction, and schema transformation, along with monitoring
    at various stages.

    Parameters
    ----------
    builder : mrc.Builder
        The Morpheus builder to which the pipeline modules will be added.

    Notes
    -----
    The module configuration can include the following parameters:

    - **file_source_config**: Configuration for the file source module.
      - **batch_size**: Number of files to process in each batch.
      - **chunk_overlap**: Overlap size for chunks in file processing.
      - **chunk_size**: Size of chunks for file processing.
      - **converters_meta**: Metadata for file format converters.
        - **csv**: Configuration for CSV files.
          - **chunk_size**: Chunk size for CSV processing.
          - **text_column_name**: Name of the text column in CSV files.
      - **enable_monitor**: Boolean to enable monitoring for this module.
      - **extractor_config**: Configuration for the file content extractor module.
        - **chunk_size**: Size of chunks for the extractor.
        - **num_threads**: Number of threads for file content extraction.
      - **filenames**: List of file paths to be processed.
      - **watch**: Boolean to watch for file changes.

    The pipeline connects these modules in the following order:
    Multi-File Source -> File Content Extractor -> Schema Transform -> Deserialize,
    with monitoring at each stage.
    """

    module_config = builder.get_current_module_config()
    file_source_config = module_config.get("file_source_config", {})
    try:
        validated_config = FileSourcePipeSchema(**file_source_config)
    except ValidationError as e:
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid file source configuration: {error_messages}"
        logger.error(log_error_message)
        raise ValueError(log_error_message)

    # Use the validated configuration
    enable_monitor = validated_config.enable_monitor

    # Configure and load the multi-file source module
    source_config = {
        "batch_size": validated_config.batch_size,
        "filenames": validated_config.filenames,
        "watch_interval": validated_config.watch_interval,
        "watch_dir": validated_config.watch,
    }
    multi_file_loader = MultiFileSourceLoaderFactory.get_instance("multi_file_source", {"source_config": source_config})

    # Configure and load the file content extractor module
    file_content_extractor_config = {
        "batch_size": validated_config.batch_size,
        "num_threads": validated_config.num_threads,
        "chunk_size": validated_config.chunk_size,
        "chunk_overlap": validated_config.chunk_overlap,
        "converters_meta": validated_config.converters_meta
    }
    extractor_loader = ContentExtractorLoaderFactory.get_instance("file_content_extractor",
                                                                  file_content_extractor_config)

    # Configure and load the schema transformation module
    transform_config = {
        "schema_transform_config": {
            "summary": {
                "dtype": "str", "op_type": "select"
            },
            "title": {
                "dtype": "str", "op_type": "select"
            },
            "content": {
                "dtype": "str", "op_type": "select"
            },
            "source": {
                "dtype": "str", "op_type": "select"
            }
        }
    }
    schema_transform_loader = SchemaTransformLoaderFactory.get_instance("schema_transform", transform_config)

    deserialize_loader = DeserializeLoaderFactory.get_instance(
        "deserialize", {
            "batch_size": validated_config.batch_size, "message_type": "ControlMessage"
        })

    vdb_resource_tagging_loader = VDBResourceTaggingLoaderFactory.get_instance(
        "vdb_resource_tagging", {"vdb_resource_name": validated_config.vdb_resource_name})

    monitor_1_loader = MonitorLoaderFactory.get_instance(
        "monitor_1", {
            "description": "FileSourcePipe Transform", "silence_monitors": not enable_monitor
        })

    monitor_2_loader = MonitorLoaderFactory.get_instance(
        "monitor_2", {
            "description": "File Source Deserialize", "silence_monitors": not enable_monitor
        })

    # Load modules
    multi_file_module = multi_file_loader.load(builder=builder)
    file_content_extractor_module = extractor_loader.load(builder=builder)
    transform_module = schema_transform_loader.load(builder=builder)
    monitor_1_module = monitor_1_loader.load(builder=builder)
    deserialize_module = deserialize_loader.load(builder=builder)
    vdb_resource_tagging_module = vdb_resource_tagging_loader.load(builder=builder)
    monitor_2_module = monitor_2_loader.load(builder=builder)

    # Connect the modules in the pipeline
    builder.make_edge(multi_file_module.output_port("output"), file_content_extractor_module.input_port("input"))
    builder.make_edge(file_content_extractor_module.output_port("output"), transform_module.input_port("input"))
    builder.make_edge(transform_module.output_port("output"), monitor_1_module.input_port("input"))
    builder.make_edge(monitor_1_module.output_port("output"), deserialize_module.input_port("input"))
    builder.make_edge(deserialize_module.output_port("output"), vdb_resource_tagging_module.input_port("input"))
    builder.make_edge(vdb_resource_tagging_module.output_port("output"), monitor_2_module.input_port("input"))

    # Register the final output of the transformation module
    builder.register_module_output("output", monitor_2_module.output_port("output"))
