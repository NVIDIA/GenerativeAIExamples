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

logger = logging.getLogger(__name__)


class RSSSourcePipeSchema(BaseModel):
    batch_size: int = 32
    cache_dir: str = "./.cache/http"
    cooldown_interval_sec: int = 600
    enable_cache: bool = False
    enable_monitor: bool = True
    feed_input: List[str] = Field(default_factory=list)
    interval_sec: int = 600
    output_batch_size: int = 2048
    request_timeout_sec: float = 2.0
    run_indefinitely: bool = True
    stop_after_sec: int = 0
    vdb_resource_name: str
    web_scraper_config: Optional[Dict[Any, Any]] = None

    @validator('feed_input', pre=True)
    def validate_feed_input(cls, v):
        if isinstance(v, str):
            return [v]
        elif isinstance(v, list):
            return v
        raise ValueError('feed_input must be a string or a list of strings')

    class Config:
        extra = "forbid"
