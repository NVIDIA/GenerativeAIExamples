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
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from typing import Optional
from typing_extensions import TypedDict


logger = logging.getLogger(__name__)


class StageSchema(BaseModel):
    enable_monitor: bool = True
    module_id: str = "kafka_scrape_source_pipe"
    module_output_id: str = "output"
    namespace: str = "morpheus_examples_llm"
    run_indefinitely: bool = True
    transform_type: str = "raw_chunker"
    

class KafkaSourceSchema(TypedDict, total=False):
    async_commits: bool = True
    auto_offset_reset: str = "earliest"
    bootstrap_servers: str = "kafka:19092"
    disable_commit: bool = False
    disable_pre_filtering: bool = False
    enable_monitor: bool = True
    group_id: str = "morpheus"
    input_topic: str = "raw_queue"
    max_batch_size: int #= Field(default=2)
    max_concurrent: int = 10
    poll_interval: str = "10millis"
    stop_after: int = 0


class WebScraperSchema(TypedDict, total=False):
    chunk_overlap: int = 51
    chunk_size: int = 512
    enable_cache: bool = True
    cache_path: str = "./.cache/llm/html/WebScrapeModule.sqlite"
    cache_dir: str = "./.cache/llm/html"
    link_column: str = "payload"  


class RawChunkerScraperSchema(TypedDict, total=False):
    payload_column: str = "payload"
    chunk_size: int = 512
    chunk_overlap: int = 51

    class Config:
        extra = "forbid"


class DeserializeSchema(BaseModel):
    output_batch_size: int = 2048


class VDBResourceTaggingSchema(BaseModel):
    vdb_resource_name: str = "vdb_kafka"


class KafkaSourcePipeSchema(BaseModel):
    stage_config: StageSchema
    kafka_config: KafkaSourceSchema
    web_scraper_config: WebScraperSchema = None
    raw_chunker_config: RawChunkerScraperSchema = None
    deserialize_config: DeserializeSchema
    vdb_config: VDBResourceTaggingSchema

    class Config:
        extra = "forbid"
