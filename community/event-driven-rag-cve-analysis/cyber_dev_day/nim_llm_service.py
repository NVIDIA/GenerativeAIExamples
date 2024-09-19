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

import appdirs

from cyber_dev_day.llm_service import LLMClient
from cyber_dev_day.llm_service import LLMService

logger = logging.getLogger(__name__)

IMPORT_EXCEPTION = None
IMPORT_ERROR_MESSAGE = (
    "ChatNVIDIA library from Langchain is a required installation. %pip install --upgrade --quiet langchain-nvidia-ai-endpoints")

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
except ImportError as import_exc:
    IMPORT_EXCEPTION = import_exc


class ChatNVIDIAClient(LLMClient):
    """
    Client for interacting with ChatNVIDIA models through the Langchain-NVIDIA AI Endpoints.
    """

    def __init__(self,
                 parent: "NIMLLMService",
                 *,
                 model_name: str,
                 set_assistant: bool = False,
                 max_retries: int = 10,
                 temperature: float = 0.1,
                 top_p: float = 0.0,
                 api_key=os.getenv('NVIDIA_API_KEY'),
                 **model_kwargs) -> None:
        """
        Initialize the ChatNVIDIAClient.

        Parameters
        ----------
        parent : ChatNVIDIAService
            The service instance creating this client.
        model_name : str
            The name of the model to interact with.
        set_assistant : bool, optional
            Flag indicating if the assistant role should be set, by default False.
        max_retries : int, optional
            Maximum number of retries for API requests, by default 10.
        api_key : str, optional
            API key for authenticating with the NVIDIA service, by default from the 'NGC_API_KEY' environment variable.
        model_kwargs : dict
            Additional model-specific keyword arguments.
        """
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        self._model_name = model_name
        self._set_assistant = set_assistant
        self._prompt_key = "prompt"
        self._assistant_key = "assistant"
        self._model_kwargs = copy.deepcopy(model_kwargs)

        print(f"Initializing chat client with temperature {temperature}")

        self._client = ChatNVIDIA(model=self._model_name, nvidia_api_key=api_key, temperature=temperature, top_p=top_p)

    async def _generate_async(self, prompt: str, assistant: str = None) -> str:
        """
        Generate async call to NIM using ChatNVIDIA client.

        Parameters
        ----------
        prompt : str
            The prompt to generate a response for.
        assistant : str, optional
            The assistant text to guide the response, by default None.

        Returns
        -------
        str
            The generated response content.
        """
        output = await self._client.ainvoke(prompt)
        return output.content

    async def generate_batch_async(self,
                                   inputs: dict[str, list],
                                   return_exceptions=False) -> list[str] | list[str | BaseException]:
        """
        Generate a batch of asynchronous requests to ChatNVIDIA.

        Parameters
        ----------
        inputs : dict[str, list]
            Dictionary containing the prompts for batch processing.
        return_exceptions : bool, optional
            If True, exceptions during the async operations will be returned, by default False.

        Returns
        -------
        list[str] | list[str | BaseException]
            List of generated responses or exceptions.
        """
        prompts = inputs[self._prompt_key]

        coros = [self._generate_async(prompt) for prompt in prompts]

        return await asyncio.gather(*coros, return_exceptions=return_exceptions)

    def generate(self, **input_dict) -> str:
        """
        Issue a request to generate a response based on a given prompt.

        Parameters
        ----------
        input_dict : dict
            Input containing prompt data.

        Returns
        -------
        str
            The generated response content.
        """
        return self._client.invoke(input_dict[self._prompt_key])

    async def generate_async(self, **input_dict) -> str:
        """
        Issue an asynchronous request to generate a response based on a given prompt.

        Parameters
        ----------
        input_dict : dict
            Input containing prompt data.

        Returns
        -------
        str
            The generated response content.
        """
        return await self._generate_async(input_dict[self._prompt_key], input_dict.get(self._assistant_key))

    def generate_batch(self, inputs: dict[str, list], return_exceptions=False) -> list[str] | list[str | BaseException]:
        """
        Generate a batch of requests to ChatNVIDIA.

        Parameters
        ----------
        inputs : dict[str, list]
            Dictionary containing the prompts for batch processing.
        return_exceptions : bool, optional
            If True, exceptions during the operations will be returned, by default False.

        Returns
        -------
        list[str] | list[str | BaseException]
            List of generated responses or exceptions.
        """
        prompts = inputs[self._prompt_key]
        results = [self._generate(prompt) for prompt in prompts]

        return results

    def _generate(self, prompt: str) -> str:
        """
        Issue a request to generate a response based on a given prompt.

        Parameters
        ----------
        prompt : str
            The prompt to generate a response for.

        Returns
        -------
        str
            The generated response content.
        """
        output = self._client.invoke(prompt)
        return self._client.invoke(prompt)

    def get_input_names(self) -> list[str]:
        """
        Get the names of the required inputs for the model.

        Returns
        -------
        list[str]
            List of input names required by the model.
        """
        input_names = [self._prompt_key]
        if self._set_assistant:
            input_names.append(self._assistant_key)

        return input_names


class NIMLLMService(LLMService):
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
            If the `langchain-nvidia-ai-endpoints` library is not found in the python environment.
        """
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        self._default_model_kwargs = default_model_kwargs or {}

        self._logger = logging.getLogger(f"{__package__}.{NIMLLMService.__name__}")

        # Don't propagate up to the default logger. Just log to file
        self._logger.propagate = False

        log_file = os.path.join(appdirs.user_log_dir(appauthor="NVIDIA", appname="morpheus"), "openai.log")

        # Add a file handler
        file_handler = logging.FileHandler(log_file)

        self._logger.addHandler(file_handler)
        self._logger.setLevel(logging.INFO)

        self._logger.info("NIM LLM Chat Service started.")

        self._message_count = 0

    def _get_message_id(self) -> int:
        """
        Get a unique message ID for logging purposes.

        Returns
        -------
        int
            A unique message ID.
        """
        self._message_count += 1

        return self._message_count

    def get_client(self,
                   *,
                   model_name: str,
                   max_retries: int = 10,
                   temperature: float = 0.1,
                   top_p: float = 0.0,
                   **model_kwargs) -> ChatNVIDIAClient:
        """
        Returns a client for interacting with a specific model. This method is the preferred way to create a client.

        Parameters
        ----------
        model_name : str
            The name of the model to create a client for.
        max_retries: int, optional
            The maximum number of retries to attempt when making a request to the OpenAI API.
        model_kwargs : dict[str, typing.Any]
            Additional keyword arguments to pass to the model when generating text. Arguments specified here will
            overwrite the `default_model_kwargs` set in the service constructor.

        Returns
        -------
        ChatNVIDIAClient
            A client instance configured for the specified model.
        """
        final_model_kwargs = {**self._default_model_kwargs, **model_kwargs}

        return ChatNVIDIAClient(self,
                                model_name=model_name,
                                max_retries=max_retries,
                                temperature=temperature,
                                top_p=top_p,
                                **final_model_kwargs)