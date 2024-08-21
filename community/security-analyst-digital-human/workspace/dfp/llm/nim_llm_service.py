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
import asyncio
import copy
import logging
import os
import time
import typing
from contextlib import contextmanager
from textwrap import dedent
import re

import appdirs

from morpheus.llm.services.llm_service import LLMClient
from morpheus.llm.services.llm_service import LLMService
from morpheus.llm.services.openai_chat_service import OpenAIChatService, OpenAIChatClient

logger = logging.getLogger(__name__)

IMPORT_EXCEPTION = None
IMPORT_ERROR_MESSAGE = ("OpenAIChatService & OpenAIChatClient require the openai package to be installed. "
                        "Install it by running the following command:\n"
                        "`conda env update --solver=libmamba -n morpheus "
                        "--file conda/environments/dev_cuda-121_arch-x86_64.yaml --prune`")

try:
    import openai
    import openai.types.chat
    import openai.types.chat.chat_completion
except ImportError as import_exc:
    IMPORT_EXCEPTION = import_exc


class NIMChatClient(OpenAIChatClient):
    """
    Client for interacting with a specific NVIDIA Inference Microservice chat model. This class should be constructed with the
    `NIMChatService.get_client` method.

    Parameters
    ----------
    model_name : str
        The name of the model to interact with.
        
    base_url: str
        The URI at which the NIM can be reached.
        
    set_assistant: bool, optional default=False
        When `True`, a second input field named `assistant` will be used to proide additional context to the model.

    max_retries: int, optional default=10
        The maximum number of retries to attempt when making a request to the OpenAI API.

    model_kwargs : dict[str, typing.Any]
        Additional keyword arguments to pass to the model when generating text.
    """

    _prompt_key: str = "prompt"
    _assistant_key: str = "assistant"

    def __init__(self,
                 parent: "NIMChatService",
                 *,
                 model_name: str,
                 base_url: str,
                 set_assistant: bool = False,
                 max_retries: int = 10,
                 **model_kwargs) -> None:
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__(
            parent=parent,
            model_name=model_name,
            set_assistant=set_assistant,
            max_retries=max_retries,
            **model_kwargs
        )
        
        self._base_url = base_url

        # Create the client objects for both sync and async
        self._client = openai.OpenAI(base_url = self._base_url, max_retries=max_retries)
        self._client_async = openai.AsyncOpenAI(base_url = self._base_url, max_retries=max_retries)
        
    

class NIMChatService(OpenAIChatService):
    """
    A service for interacting with NIM Chat models, this class should be used to create clients.
    """

    def __init__(self, *, default_model_kwargs: dict = None) -> None:
        """
        Creates a service for interacting with OpenAI Chat models, this class should be used to create clients.

        Parameters
        ----------
        default_model_kwargs : dict, optional
            Default arguments to use when creating a client via the `get_client` function. Any argument specified here
            will automatically be used when calling `get_client`. Arguments specified in the `get_client` function will
            overwrite default values specified here. This is useful to set model arguments before creating multiple
            clients. By default None

        Raises
        ------
        ImportError
            If the `openai` library is not found in the python environment.
        """
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        self._default_model_kwargs = default_model_kwargs or {}

        
    def get_client(self,
                   *,
                   model_name: str,
                   base_url: str,
                   set_assistant: bool = False,
                   max_retries: int = 10,
                   **model_kwargs) -> NIMChatClient:
        """
        Returns a client for interacting with a specific model. This method is the preferred way to create a client.

        Parameters
        ----------
        model_name : str
            The name of the model to create a client for.
            
        base_url: str
            The URI at which the NIM can be reached.

        set_assistant: bool, optional default=False
            When `True`, a second input field named `assistant` will be used to proide additional context to the model.

        max_retries: int, optional default=10
            The maximum number of retries to attempt when making a request to the OpenAI API.

        model_kwargs : dict[str, typing.Any]
            Additional keyword arguments to pass to the model when generating text. Arguments specified here will
            overwrite the `default_model_kwargs` set in the service constructor
        """

        final_model_kwargs = {**self._default_model_kwargs, **model_kwargs}

        return NIMChatClient(self,
                                model_name=model_name,
                                base_url=base_url,
                                set_assistant=set_assistant,
                                max_retries=max_retries,
                                **final_model_kwargs)