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


class KafkaSourceSchema(BaseModel):

    max_batch_size: int = Field(default=2)
    bootstrap_servers: str = "kafka:19092"
    input_topic: str = "raw_queue"
    group_id: str = "morpheus"
    poll_interval: str = "10millis"
    disable_commit: bool = False
    disable_pre_filtering: bool = False
    auto_offset_reset: str = "earliest"
    stop_after: int = 0
    async_commits: bool = True
    
    class Config:
        extra = "forbid"
