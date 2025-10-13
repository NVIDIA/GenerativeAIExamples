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

from morpheus.llm.services.llm_service import LLMClient
from morpheus.llm.services.llm_service import LLMService

logger = logging.getLogger(__name__)

IMPORT_EXCEPTION = None
IMPORT_ERROR_MESSAGE = ("ChatNVIDIA library from Langchain is a required installation. %pip install --upgrade --quiet langchain-nvidia-ai-endpoints")

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
except ImportError as import_exc:
    IMPORT_EXCEPTION = import_exc


class _ApiLogger:
    """
    Simple class that allows passing back and forth the inputs and outputs of an API call via a context manager.
    """

    log_template: typing.ClassVar[str] = dedent("""
        ============= MESSAGE %d START ==============
                        --- Input ---
        %s
                        --- Output --- (%f ms)
        %s
        =============  MESSAGE %d END ==============
        """).strip("\n")

    def __init__(self, *, message_id: int, inputs: typing.Any) -> None:

        self.message_id = message_id
        self.inputs = inputs
        self.outputs = None

    def set_output(self, output: typing.Any) -> None:
        self.outputs = output

class ChatNVIDIAChatClient(LLMClient):
    
    def __init__(self,
                 parent: "ChatNVIDIAChatService",
                 *,
                 model_name: str,
                 set_assistant: bool = False,
                 max_retries: int = 10,
                 api_key=os.getenv('NGC_API_KEY'),
                 **model_kwargs) -> None:
        
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        self._model_name = model_name
        self._set_assistant = set_assistant
        self._prompt_key = "prompt"
        self._assistant_key = "assistant"
        self._model_kwargs = copy.deepcopy(model_kwargs)


        self._client = ChatNVIDIA(model=self._model_name,
                                 nvidia_api_key = api_key)


    @contextmanager
    def _api_logger(self, inputs: typing.Any):

        message_id = self._parent._get_message_id()
        start_time = time.time()

        api_logger = _ApiLogger(message_id=message_id, inputs=inputs)

        yield api_logger

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000.0

        self._parent._logger.info(_ApiLogger.log_template,
                                  message_id,
                                  api_logger.inputs,
                                  duration_ms,
                                  api_logger.outputs,
                                  message_id)
    
    
    async def _generate_async(self, prompt: str, assistant: str = None) -> str:
        """
        Generate async call to NIM using ChatNVIDIA client. 
        """

        output = await self._client.ainvoke(prompt)

        return output.content


    async def generate_batch_async(self,
                                   inputs: dict[str, list],
                                   return_exceptions=False) -> list[str] | list[str | BaseException]:


        prompts = inputs[self._prompt_key]

        coros = []
        for (i, prompt) in enumerate(prompts):
            coros.append(self._generate_async(prompt))

        
        return await asyncio.gather(*coros, return_exceptions=return_exceptions)

    def generate(self, **input_dict) -> str:
        """
        Issue a request to generate a response based on a given prompt.

        Parameters
        ----------
        input_dict : dict
            Input containing prompt data.
        """
        return self._client.invoke(input_dict[self._prompt_key])

    
   
    async def generate_async(self, **input_dict) -> str:
        """
        Issue an asynchronous request to generate a response based on a given prompt.

        Parameters
        ----------
        input_dict : dict
            Input containing prompt data.
        """
        return await self._generate_async(input_dict[self._prompt_key], input_dict.get(self._assistant_key))

    
    def generate_batch(self, inputs: dict[str, list], return_exceptions=False) -> list[str] | list[str | BaseException]:
        
        return ['Not implemented']

    def get_input_names(self) -> list[str]:
        input_names = [self._prompt_key]
        if self._set_assistant:
            input_names.append(self._assistant_key)

        return input_names


class ChatNVIDIAChatService(LLMService):
    """
    A service for interacting with ChatNVIDIA Chat models, this class should be used to create clients.
    """

    def __init__(self, *, default_model_kwargs: dict = None) -> None:
        """
        Creates a service for interacting with ChatNVIDIA Chat models, this class should be used to create clients.

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
            ChatNVIDIA library from Langchain is a required installation.
        """
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        self._default_model_kwargs = default_model_kwargs or {}

        self._logger = logging.getLogger(f"{__package__}.{ChatNVIDIAChatService.__name__}")

        # Dont propagate up to the default logger. Just log to file
        self._logger.propagate = False

        log_file = os.path.join(appdirs.user_log_dir(appauthor="NVIDIA", appname="morpheus"), "openai.log")

        # Add a file handler
        file_handler = logging.FileHandler(log_file)

        self._logger.addHandler(file_handler)
        self._logger.setLevel(logging.INFO)

        self._logger.info("ChatNVIDIA Chat Service started.")

        self._message_count = 0

    def _get_message_id(self):

        self._message_count += 1

        return self._message_count

    def get_client(self,
                   *,
                   model_name: str,
                   set_assistant: bool = False,
                   max_retries: int = 10,
                   **model_kwargs) -> ChatNVIDIAChatClient:
        """
        Returns a client for interacting with a specific model. This method is the preferred way to create a client.

        Parameters
        ----------
        model_name : str
            The name of the model to create a client for.

        set_assistant: bool, optional default=False
            When `True`, a second input field named `assistant` will be used to proide additional context to the model.

        max_retries: int, optional default=10
            The maximum number of retries to attempt when making a request to the ChatNVIDIA API.

        model_kwargs : dict[str, typing.Any]
            Additional keyword arguments to pass to the model when generating text. Arguments specified here will
            overwrite the `default_model_kwargs` set in the service constructor
        """

        final_model_kwargs = {**self._default_model_kwargs, **model_kwargs}

        return ChatNVIDIAChatClient(self,
                                model_name=model_name,
                                set_assistant=set_assistant,
                                max_retries=max_retries,
                                **final_model_kwargs) 


        


