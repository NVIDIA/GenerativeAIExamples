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

from morpheus.config import Config
from morpheus.messages import ControlMessage
from morpheus.pipeline.pipeline import Pipeline
from morpheus.stages.general.linear_modules_source import LinearModuleSourceStage
from morpheus.stages.input.kafka_source_stage import KafkaSourceStage
from morpheus.stages.input.kafka_source_stage import AutoOffsetReset
from morpheus.utils.module_utils import ModuleLoaderFactory

from .module.file_source_pipe import FileSourcePipeLoaderFactory
from .module.rss_source_pipe import RSSSourcePipeLoaderFactory
from .module.kafka_source_pipe import KafkaSourcePipeLoaderFactory

logger = logging.getLogger(__name__)


def validate_source_config(source_info: typing.Dict[str, any]) -> None:
    """
    Validates the configuration of a source.

    This function checks whether the given source configuration dictionary
    contains all required keys: 'type', 'name', and 'config'.

    Parameters
    ----------
    source_info : typing.Dict[str, any]
        The source configuration dictionary to validate.

    Raises
    ------
    ValueError
        If any of the required keys ('type', 'name', 'config') are missing
        in the source configuration.
    """
    if ('type' not in source_info or 'name' not in source_info or 'config' not in source_info):
        raise ValueError(f"Each source must have 'type', 'name', and 'config':\n {source_info}")


def setup_rss_source(pipe: Pipeline, config: Config, source_name: str, rss_config: typing.Dict[str, typing.Any]):
    """
    Set up the RSS source stage in the pipeline.

    Parameters
    ----------
    pipe : Pipeline
        The pipeline to which the RSS source stage will be added.
    config : Config
        Configuration object for the pipeline.
    source_name : str
        The name of the RSS source stage.
    rss_config : typing.Dict[str, Any]
        Configuration parameters for the RSS source stage.

    Returns
    -------
    SubPipeline
        The sub-pipeline stage created for the RSS source.
    """
    module_definition = RSSSourcePipeLoaderFactory.get_instance(
        module_name=f"rss_source_pipe__{source_name}",
        module_config={"rss_config": rss_config},
    )
    rss_pipe = pipe.add_stage(
        LinearModuleSourceStage(config, module_definition, output_type=ControlMessage, output_port_name="output"))

    return rss_pipe


def setup_filesystem_source(pipe: Pipeline, config: Config, source_name: str, fs_config: typing.Dict[str, typing.Any]):
    """
    Set up the filesystem source stage in the pipeline.

    Parameters
    ----------
    pipe : Pipeline
        The pipeline to which the filesystem source stage will be added.
    config : Config
        Configuration object for the pipeline.
    source_name : str
        The name of the filesystem source stage.
    fs_config : typing.Dict[str, Any]
        Configuration parameters for the filesystem source stage.

    Returns
    -------
    SubPipeline
        The sub-pipeline stage created for the filesystem source.
    """

    module_loader = FileSourcePipeLoaderFactory.get_instance(module_name=f"file_source_pipe__{source_name}",
                                                             module_config={"file_source_config": fs_config})
    file_pipe = pipe.add_stage(
        LinearModuleSourceStage(config, module_loader, output_type=ControlMessage, output_port_name="output"))

    return file_pipe

def setup_kafka_source(pipe: Pipeline, config: Config, source_name: str, type_config: typing.Dict[str, typing.Any]):
    """
    Set up the kafka source stage in the pipeline.

    Parameters
    ----------
    pipe : Pipeline
        The pipeline to which the filesystem source stage will be added.
    config : Config
        Configuration object for the pipeline.
    source_name : str
        The name of the filesystem source stage.
    fs_config : typing.Dict[str, Any]
        Configuration parameters for the filesystem source stage.

    Returns
    -------
    SubPipeline
        The sub-pipeline stage created for the kafka source.
    """

    module_definition = KafkaSourcePipeLoaderFactory.get_instance(
        module_name=f"kafka_source_pipe__{source_name}",
        module_config={"kafka_config": type_config},
    )

    kafka_pipe = pipe.add_stage(
        LinearModuleSourceStage(config, module_definition, output_type=ControlMessage, output_port_name="output"))
    
    return kafka_pipe

def setup_custom_source(pipe: Pipeline, config: Config, source_name: str, custom_config: typing.Dict[str, typing.Any]):
    """
    Setup a custom source stage in the pipeline.

    Parameters
    ----------
    pipe : Pipeline
        The pipeline to which the custom source stage will be added.
    config : Config
        Configuration object for the pipeline.
    source_name : str
        The name of the custom source stage.
    custom_config : typing.Dict[str, Any]
        Configuration parameters for the custom source stage, including
        the module_id, module_name, namespace, and any additional parameters.

    Returns
    -------
    SubPipeline
        The sub-pipeline stage created for the custom source.
    """

    module_id = custom_config.pop('module_id')
    module_name = f"{module_id}__{source_name}"
    module_namespace = custom_config.pop('namespace')
    module_output_id = custom_config.pop('module_output_id', 'output')

    module_config = {
        "module_id": module_id,
        "module_name": module_name,
        "namespace": module_namespace,
    }

    config_name_mapping = custom_config.pop('config_name_mapping', 'config')
    module_config[config_name_mapping] = custom_config

    # Adding the custom module stage to the pipeline
    custom_pipe = pipe.add_stage(
        LinearModuleSourceStage(config, module_config, output_type=ControlMessage, output_port_name=module_output_id))

    return custom_pipe


def process_vdb_sources(pipe: Pipeline, config: Config, vdb_source_config: typing.List[typing.Dict]) -> typing.List:
    """
    Processes and sets up sources defined in a vdb_source_config.

    This function reads the source configurations provided in vdb_source_config and
    sets up each source based on its type ('rss', 'filesystem', or 'custom').
    It validates each source configuration and then calls the appropriate setup
    function to add the source to the pipeline.

    Parameters
    ----------
    pipe : Pipeline
        The pipeline to which the sources will be added.
    config : Config
        Configuration object for the pipeline.
    vdb_source_config : List[Dict]
        A list of dictionaries, each containing the configuration for a source.

    Returns
    -------
    list
        A list of the sub-pipeline stages created for each defined source.

    Raises
    ------
    ValueError
        If an unsupported source type is encountered in the configuration.
    """
    vdb_sources = []
    for source_info in vdb_source_config:
        validate_source_config(source_info)
        source_type = source_info['type']
        source_name = source_info['name']
        source_config = source_info['config']

        if (source_type == 'rss'):
            vdb_sources.append(setup_rss_source(pipe, config, source_name, source_config))
        elif (source_type == 'filesystem'):
            vdb_sources.append(setup_filesystem_source(pipe, config, source_name, source_config))
        elif (source_type == 'kafka'):
            vdb_sources.append(setup_kafka_source(pipe, config, source_name, source_config))            
        elif (source_type == 'custom'):
            vdb_sources.append(setup_custom_source(pipe, config, source_name, source_config))
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    return vdb_sources
