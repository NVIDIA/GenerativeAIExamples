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
import time
import typing

from morpheus.config import Config
from morpheus.pipeline.pipeline import Pipeline
from morpheus.stages.general.monitor_stage import MonitorStage
from morpheus.stages.general.trigger_stage import TriggerStage
from morpheus.stages.inference.triton_inference_stage import TritonInferenceStage
from morpheus.stages.output.write_to_vector_db_stage import WriteToVectorDBStage
from morpheus.stages.preprocess.preprocess_nlp_stage import PreprocessNLPStage

from vdb_upload.helper import process_vdb_sources

logger = logging.getLogger(__name__)


def pipeline(pipeline_config: Config,
             source_config: typing.List,
             vdb_config: typing.Dict,
             embeddings_config: typing.Dict,
             tokenizer_config: typing.Dict) -> float:
    """
    Sets up and runs a data processing pipeline based on provided configurations.

    Parameters
    ----------
    source_config : Dict
        Configuration for data sources (e.g., 'rss', 'filesystem').
    vdb_config : Dict
        Configuration for the vector database.
    pipeline_config : Dict
        General configuration for the pipeline (e.g., number of threads, batch sizes).
    embeddings_config : Dict
        Configuration for embeddings (e.g., model name, embedding size).

    Returns
    -------
    float
        The start time of the pipeline execution.
    """

    isolate_embeddings = embeddings_config.get('isolate_embeddings', False)

    pipe = Pipeline(pipeline_config)

    vdb_sources = process_vdb_sources(pipe, pipeline_config, source_config)

    trigger = None
    if (isolate_embeddings):
        trigger = pipe.add_stage(TriggerStage(pipeline_config))

    nlp_stage = pipe.add_stage(PreprocessNLPStage(pipeline_config, **tokenizer_config.get("model_kwargs", {})))

    monitor_1 = pipe.add_stage(
        MonitorStage(pipeline_config, description="Tokenize rate", unit='chunks', delayed_start=False))

    embedding_stage = pipe.add_stage(TritonInferenceStage(pipeline_config, **embeddings_config.get('model_kwargs', {})))

    monitor_2 = pipe.add_stage(
        MonitorStage(pipeline_config, description="Inference rate", unit="embeddings", delayed_start=False))

    vector_db = pipe.add_stage(WriteToVectorDBStage(pipeline_config, **vdb_config))

    monitor_3 = pipe.add_stage(
        MonitorStage(pipeline_config, description="Upload rate", unit="embeddings", delayed_start=False))

    # Connect the pipeline
    for source_output in vdb_sources:
        if (isolate_embeddings):
            pipe.add_edge(source_output, trigger)
        else:
            pipe.add_edge(source_output, nlp_stage)

    if (isolate_embeddings):
        pipe.add_edge(trigger, nlp_stage)

    pipe.add_edge(nlp_stage, monitor_1)
    pipe.add_edge(monitor_1, embedding_stage)
    pipe.add_edge(embedding_stage, monitor_2)
    pipe.add_edge(monitor_2, vector_db)
    pipe.add_edge(vector_db, monitor_3)

    start_time = time.time()

    pipe.run()

    return start_time
