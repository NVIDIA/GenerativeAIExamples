# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The definition of the application configuration."""
from frontend.configuration_wizard import ConfigWizard, configclass, configfield


@configclass
class AppConfig(ConfigWizard):
    """Configuration class for the application.

    :cvar triton: The configuration of the chat server.
    :type triton: ChatConfig
    :cvar model: The configuration of the model
    :type triton: ModelConfig
    """

    server_url: str = configfield(
        "serverUrl", default="http://localhost", help_txt="The location of the chat server.",
    )
    server_port: str = configfield(
        "serverPort", default="8000", help_txt="The port on which the chat server is listening for HTTP requests.",
    )
    model_name: str = configfield(
        "modelName", default="meta/llama3-70b-instruct", help_txt="The name of the hosted LLM model.",
    )
