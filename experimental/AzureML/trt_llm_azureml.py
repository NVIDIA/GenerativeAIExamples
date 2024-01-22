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


"""A Langchain LLM component for connecting to Triton + TensorRT LLM backend for AzureML hosted endpoints."""

# pylint: disable=too-many-lines
import time
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Type

import gevent.ssl
import numpy as np
import tritonclient.http as httpclient
from tritonclient.utils import np_to_triton_dtype

try:
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from langchain.pydantic_v1 import Field, root_validator

    USE_LANGCHAIN = True
except ImportError:
    USE_LANGCHAIN = False


STOP_WORDS = ["</s>"]
RANDOM_SEED = 0

if USE_LANGCHAIN:
    # pylint: disable-next=too-few-public-methods  # Interface is defined by LangChain
    class TensorRTLLM(LLM):  # type: ignore  # LLM class not typed in langchain
        """A custom Langchain LLM class that integrates with TRTLLM triton models.

        Arguments:
        server_url: (str) The URL of the Triton inference server to use.
        model_name: (str) The name of the Triton TRT model to use.
        temperature: (str) Temperature to use for sampling
        top_p: (float) The top-p value to use for sampling
        top_k: (float) The top k values use for sampling
        beam_width: (int) Last n number of tokens to penalize
        repetition_penalty: (int) Last n number of tokens to penalize
        length_penalty: (float) The penalty to apply repeated tokens
        tokens: (int) The maximum number of tokens to generate.
        client: The client object used to communicate with the inference server
        """

        server_url: str = Field(None, alias="server_url")

        # # all the optional arguments
        model_name: str = "ensemble"
        temperature: Optional[float] = 1.0
        top_p: Optional[float] = 0
        top_k: Optional[int] = 1
        tokens: Optional[int] = 100
        beam_width: Optional[int] = 1
        repetition_penalty: Optional[float] = 1.0
        length_penalty: Optional[float] = 1.0
        client: Any
        api_key: Optional[str] = None
        use_ssl = False
        extra_headers: Dict[str, str] = {}

        @root_validator()  # type: ignore  # typing not declared in langchain
        @classmethod
        def validate_environment(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            """Validate that python package exists in environment."""
            try:
                values["client"] = HttpTritonClient(
                    values["server_url"],
                    values["use_ssl"],
                    values["api_key"],
                    **values["extra_headers"],
                )

            except ImportError as err:
                raise ImportError(
                    "Could not import triton client python package. "
                    "Please install it with `pip install tritonclient[all]`."
                ) from err
            return values

        @property
        def _get_model_default_parameters(self) -> Dict[str, Any]:
            return {
                "tokens": self.tokens,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "temperature": self.temperature,
                "repetition_penalty": self.repetition_penalty,
                "length_penalty": self.length_penalty,
                "beam_width": self.beam_width,
            }

        @property
        def _invocation_params(self, **kwargs: Any) -> Dict[str, Any]:
            params = {**self._get_model_default_parameters, **kwargs}
            return params

        @property
        def _identifying_params(self) -> Dict[str, Any]:
            """Get all the identifying parameters."""
            return {
                "server_url": self.server_url,
                "model_name": self.model_name,
            }

        @property
        def _llm_type(self) -> str:
            return "triton_tensorrt"

        def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,  # pylint: disable=unused-argument
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> str:
            """
            Execute an inference request.

            Args:
                prompt: The prompt to pass into the model.
                stop: A list of strings to stop generation when encountered

            Returns:
                The string generated by the model
            """
            text_callback = None
            if run_manager:
                text_callback = partial(
                    run_manager.on_llm_new_token, verbose=self.verbose
                )

            invocation_params = self._get_model_default_parameters
            invocation_params.update(kwargs)
            invocation_params["prompt"] = [[prompt]]
            model_params = self._identifying_params
            model_params.update(kwargs)

            #self.client.load_model(model_params["model_name"])
            return self._request(model_params, invocation_params, text_callback)

        def _streaming_request(
            self,
            model_params: Dict[str, Any],
            request_id: str,
            invocation_params: Dict[str, Any],
            text_callback: Optional[Callable[[str], None]],
        ) -> str:
            """Request a streaming inference session."""
            result_queue = self.client.request_streaming(
                model_params["model_name"], request_id, **invocation_params
            )

            response = ""
            for token in result_queue:
                if text_callback:
                    text_callback(token)
                response = response + token
            return response

        def _request(
            self,
            model_params: Dict[str, Any],
            invocation_params: Dict[str, Any],
            text_callback: Optional[Callable[[str], None]],
        ) -> str:
            """Request a streaming inference session."""
            token: str = self.client.request(
                model_params["model_name"], **invocation_params
            )
            if text_callback:
                text_callback(token)
            return token


class HttpTritonClient:
    """HTTP connection to a triton inference server."""

    def __init__(
        self,
        server_url: str,
        use_ssl: Optional[bool] = False,
        api_key: Optional[str] = None,
        **extra_headers,
    ) -> None:
        """Initialize the client."""
        self._server_url = server_url

        use_ssl = use_ssl or False  # ensure use ssl is a bool and not None
        # pylint: disable-next=no-member ; false positive
        ssl_factory = gevent.ssl._create_default_https_context if use_ssl else None
        self._client: httpclient.InferenceServerClient = self._inference_server_client(
            server_url,
            ssl=use_ssl,
            ssl_context_factory=ssl_factory,
        )
        self._headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            self._headers["Authorization"] = "Bearer " + api_key
        if extra_headers:
            self._headers.update(extra_headers)

    @property
    def _inference_server_client(
        self,
    ) -> Type[httpclient.InferenceServerClient]:
        """Return the prefered InferenceServerClient class."""
        return httpclient.InferenceServerClient  # type: ignore

    @property
    def _infer_input(self) -> Type[httpclient.InferInput]:
        """Return the preferred InferInput."""
        return httpclient.InferInput  # type: ignore

    @property
    def _infer_output(
        self,
    ) -> Type[httpclient.InferRequestedOutput]:
        """Return the preferred InferRequestedOutput."""
        return httpclient.InferRequestedOutput  # type: ignore

    def load_model(self, model_name: str, timeout: int = 1000) -> None:
        """Load a model into the server."""
        if self._client.is_model_ready(model_name, "1", headers=self._headers):
            return

        #self._client.load_model(model_name, headers=self._headers)
        t0 = time.perf_counter()
        t1 = t0
        while (
            not self._client.is_model_ready(model_name, headers=self._headers)
            and t1 - t0 < timeout
        ):
            t1 = time.perf_counter()

        if not self._client.is_model_ready(model_name, headers=self._headers):
            raise RuntimeError(f"Failed to load {model_name} on Triton in {timeout}s")

    def get_model_list(self) -> List[str]:
        """Get a list of models loaded in the triton server."""
        res = self._client.get_model_repository_index(headers=self._headers)
        return [model["name"] for model in res["models"]]

    def get_model_concurrency(self, model_name: str, timeout: int = 1000) -> int:
        """Get the modle concurrency."""
        self.load_model(model_name, timeout)
        instances = self._client.get_model_config(model_name, headers=self._headers)[
            "config"
        ]["instance_group"]
        return sum(instance["count"] * len(instance["gpus"]) for instance in instances)

    def _generate_outputs(
        self,
    ) -> List[httpclient.InferRequestedOutput]:
        """Generate the expected output structure."""
        return [self._infer_output("text_output")]

    def _prepare_tensor(self, name: str, input_data: Any) -> httpclient.InferInput:
        """Prepare an input data structure."""
        t = self._infer_input(
            name, input_data.shape, np_to_triton_dtype(input_data.dtype)
        )
        t.set_data_from_numpy(input_data)
        return t

    def _generate_inputs(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        prompt: str,
        tokens: int = 300,
        temperature: float = 1.0,
        top_k: float = 1,
        top_p: float = 0,
        beam_width: int = 1,
        repetition_penalty: float = 1,
        length_penalty: float = 1.0,
        stream: bool = False,
    ) -> List[httpclient.InferInput]:
        """Create the input for the triton inference server."""
        query = np.array(prompt).astype(object)
        request_output_len = np.array([tokens]).astype(np.uint32).reshape((1, -1))
        runtime_top_k = np.array([top_k]).astype(np.uint32).reshape((1, -1))
        runtime_top_p = np.array([top_p]).astype(np.float32).reshape((1, -1))
        temperature_array = np.array([temperature]).astype(np.float32).reshape((1, -1))
        len_penalty = np.array([length_penalty]).astype(np.float32).reshape((1, -1))
        repetition_penalty_array = (
            np.array([repetition_penalty]).astype(np.float32).reshape((1, -1))
        )
        random_seed = np.array([RANDOM_SEED]).astype(np.uint64).reshape((1, -1))
        beam_width_array = np.array([beam_width]).astype(np.uint32).reshape((1, -1))
        streaming_data = np.array([[stream]], dtype=bool)

        inputs = [
            self._prepare_tensor("text_input", query),
            self._prepare_tensor("max_tokens", request_output_len),
            self._prepare_tensor("top_k", runtime_top_k),
            self._prepare_tensor("top_p", runtime_top_p),
            self._prepare_tensor("temperature", temperature_array),
            self._prepare_tensor("length_penalty", len_penalty),
            self._prepare_tensor("repetition_penalty", repetition_penalty_array),
            self._prepare_tensor("random_seed", random_seed),
            self._prepare_tensor("beam_width", beam_width_array),
            self._prepare_tensor("stream", streaming_data),
        ]
        return inputs

    def _trim_batch_response(self, result_str: str) -> str:
        """Trim the resulting response from a batch request by removing provided prompt and extra generated text."""
        # extract the generated part of the prompt
        assistant_block = False
        generated = []
        for line in result_str.split("\n"):
            if assistant_block:
                if line == "User":
                    break
                generated += [line]
                continue

            if line == "Assistant":
                assistant_block = True

        return "\n".join(generated).strip()

    def request(
        self,
        model_name: str,
        **params: Any,
    ) -> str:
        """Request inferencing from the triton server."""
        if not self._client.is_model_ready(model_name, headers=self._headers):
            raise RuntimeError("Cannot request streaming, model is not loaded")

        # create model inputs and outputs
        inputs = self._generate_inputs(stream=False, **params)
        #outputs = self._generate_outputs()

        # call the model for inference
        result = self._client.infer(
            model_name, inputs=inputs, headers=self._headers
        )
        result_str = "".join(
            [val.decode("utf-8") for val in result.as_numpy("text_output").tolist()]
        )

        # extract the generated part of the prompt
        # return result_str
        return self._trim_batch_response(result_str)
