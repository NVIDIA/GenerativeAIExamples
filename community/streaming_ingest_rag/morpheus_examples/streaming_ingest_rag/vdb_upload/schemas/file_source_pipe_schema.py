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

logger = logging.getLogger(__name__)


class FileSourcePipeSchema(BaseModel):
    batch_size: int = 1024
    chunk_overlap: int = 51
    chunk_size: int = 512
    converters_meta: Optional[Dict[Any, Any]] = {}  # Flexible dictionary for converters metadata
    enable_monitor: bool = False
    extractor_config: Optional[Dict[Any, Any]] = {}  # Flexible dictionary for extractor configuration
    filenames: List[str] = Field(default_factory=list)  # List of file paths
    num_threads: int = 1  # Number of threads for processing
    vdb_resource_name: str
    watch: bool = False  # Flag to watch file changes
    watch_interval: float = -5.0  # Interval to watch file changes

    class Config:
        extra = "forbid"
