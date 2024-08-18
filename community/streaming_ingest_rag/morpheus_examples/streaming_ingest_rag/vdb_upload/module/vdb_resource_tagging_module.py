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
from pydantic import BaseModel
from pydantic import ValidationError

from morpheus.messages import ControlMessage
from morpheus.utils.module_utils import ModuleLoaderFactory
from morpheus.utils.module_utils import register_module

logger = logging.getLogger(__name__)


class VDBResourceTaggingSchema(BaseModel):
    vdb_resource_name: str

    class Config:
        extra = "forbid"


VDBResourceTaggingLoaderFactory = ModuleLoaderFactory("vdb_resource_tagging",
                                                      "morpheus_examples_llm",
                                                      VDBResourceTaggingSchema)


@register_module("vdb_resource_tagging", "morpheus_examples_llm")
def _vdb_resource_tagging(builder: mrc.Builder):
    module_config = builder.get_current_module_config()
    try:
        validated_config = VDBResourceTaggingSchema(**module_config)
    except ValidationError as e:
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid RSS source configuration: {error_messages}"
        logger.error(log_error_message)

        raise

    def on_data(data: ControlMessage):
        data.set_metadata("vdb_resource", validated_config.vdb_resource_name)

        return data

    node = builder.make_node("vdb_resource_tagging", on_data)

    builder.register_module_input("input", node)
    builder.register_module_output("output", node)