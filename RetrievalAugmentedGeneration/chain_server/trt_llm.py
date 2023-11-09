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

"""A Langchain LLM component for connecting to Triton + TensorRT LLM backend."""
# pylint: disable=too-many-lines
import abc
import json
import logging
import queue
import random
import time
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Type, Union

import google.protobuf.json_format
import numpy as np
import tritonclient.grpc as grpcclient
import tritonclient.http as httpclient
from tritonclient.grpc.service_pb2 import ModelInferResponse
from tritonclient.utils import np_to_triton_dtype

try:
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from langchain.pydantic_v1 import Field, root_validator

    USE_LANGCHAIN = True
except ImportError:
    USE_LANGCHAIN = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

STOP_WORDS = ["</s>"]
RANDOM_SEED = 0

if USE_LANGCHAIN:
    # pylint: disable-next=too-few-public-methods  # Interface is defined by LangChain
    class TensorRTLLM(LLM):  # LLM class not typed in langchain
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
        streaming: Optional[bool] = True

        @root_validator()  # typing not declared in langchain
        @classmethod
        def validate_environment(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            """Validate that python package exists in environment."""
            try:
                if values.get("streaming", True):
                    values["client"] = GrpcTritonClient(values["server_url"])
                else:
                    values["client"] = HttpTritonClient(values["server_url"])

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
            request_id = str(random.randint(1, 9999999))  # nosec

            self.client.load_model(model_params["model_name"])
            if isinstance(self.client, GrpcTritonClient):
                return self._streaming_request(
                    model_params, request_id, invocation_params, text_callback
                )
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
            start_time = time.time()
            tokens_generated = 0
            for token in result_queue:
                if text_callback:
                    text_callback(token)
                tokens_generated += 1
                response = response + token
            total_time = time.time() - start_time
            logger.info(
                "\n--- Generated %s tokens in %s seconds ---",
                tokens_generated,
                total_time,
            )
            logger.info("--- %s tokens/sec", tokens_generated / total_time)
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


class StreamingResponseGenerator(queue.Queue[Optional[str]]):
    """A Generator that provides the inference results from an LLM."""

    def __init__(
        self, client: "GrpcTritonClient", request_id: str, force_batch: bool
    ) -> None:
        """Instantiate the generator class."""
        super().__init__()
        self._client = client
        self.request_id = request_id
        self._batch = force_batch

    def __iter__(self) -> "StreamingResponseGenerator":
        """Return self as a generator."""
        return self

    def __next__(self) -> str:
        """Return the next retrieved token."""
        val = self.get()
        if val is None or val in STOP_WORDS:
            self._stop_stream()
            raise StopIteration()
        return val

    def _stop_stream(self) -> None:
        """Drain and shutdown the Triton stream."""
        self._client.stop_stream(
            "tensorrt_llm", self.request_id, signal=not self._batch
        )


class _BaseTritonClient(abc.ABC):
    """An abstraction of the connection to a triton inference server."""

    def __init__(self, server_url: str) -> None:
        """Initialize the client."""
        self._server_url = server_url
        self._client = self._inference_server_client(server_url)

    @property
    @abc.abstractmethod
    def _inference_server_client(
        self,
    ) -> Union[
        Type[grpcclient.InferenceServerClient], Type[httpclient.InferenceServerClient]
    ]:
        """Return the prefered InferenceServerClient class."""

    @property
    @abc.abstractmethod
    def _infer_input(
        self,
    ) -> Union[Type[grpcclient.InferInput], Type[httpclient.InferInput]]:
        """Return the preferred InferInput."""

    @property
    @abc.abstractmethod
    def _infer_output(
        self,
    ) -> Union[
        Type[grpcclient.InferRequestedOutput], Type[httpclient.InferRequestedOutput]
    ]:
        """Return the preferred InferRequestedOutput."""

    def load_model(self, model_name: str, timeout: int = 1000) -> None:
        """Load a model into the server."""
        if self._client.is_model_ready(model_name):
            return

        self._client.load_model(model_name)
        t0 = time.perf_counter()
        t1 = t0
        while not self._client.is_model_ready(model_name) and t1 - t0 < timeout:
            t1 = time.perf_counter()

        if not self._client.is_model_ready(model_name):
            raise RuntimeError(f"Failed to load {model_name} on Triton in {timeout}s")

    def get_model_list(self) -> List[str]:
        """Get a list of models loaded in the triton server."""
        res = self._client.get_model_repository_index(as_json=True)
        return [model["name"] for model in res["models"]]

    def get_model_concurrency(self, model_name: str, timeout: int = 1000) -> int:
        """Get the modle concurrency."""
        self.load_model(model_name, timeout)
        instances = self._client.get_model_config(model_name, as_json=True)["config"][
            "instance_group"
        ]
        return sum(instance["count"] * len(instance["gpus"]) for instance in instances)

    def _generate_stop_signals(
        self,
    ) -> List[Union[grpcclient.InferInput, httpclient.InferInput]]:
        """Generate the signal to stop the stream."""
        inputs = [
            self._infer_input("input_ids", [1, 1], "INT32"),
            self._infer_input("input_lengths", [1, 1], "INT32"),
            self._infer_input("request_output_len", [1, 1], "UINT32"),
            self._infer_input("stop", [1, 1], "BOOL"),
        ]
        inputs[0].set_data_from_numpy(np.empty([1, 1], dtype=np.int32))
        inputs[1].set_data_from_numpy(np.zeros([1, 1], dtype=np.int32))
        inputs[2].set_data_from_numpy(np.array([[0]], dtype=np.uint32))
        inputs[3].set_data_from_numpy(np.array([[True]], dtype="bool"))
        return inputs

    def _generate_outputs(
        self,
    ) -> List[Union[grpcclient.InferRequestedOutput, httpclient.InferRequestedOutput]]:
        """Generate the expected output structure."""
        return [self._infer_output("text_output")]

    def _prepare_tensor(
        self, name: str, input_data: Any
    ) -> Union[grpcclient.InferInput, httpclient.InferInput]:
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
        stream: bool = True,
    ) -> List[Union[grpcclient.InferInput, httpclient.InferInput]]:
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
        split = result_str.split("[/INST]", 1)
        generated = split[-1]
        end_token = generated.find("</s>")
        if end_token == -1:
            return generated
        generated = generated[:end_token].strip()
        return generated


class GrpcTritonClient(_BaseTritonClient):
    """GRPC connection to a triton inference server."""

    @property
    def _inference_server_client(
        self,
    ) -> Type[grpcclient.InferenceServerClient]:
        """Return the prefered InferenceServerClient class."""
        return grpcclient.InferenceServerClient  # type: ignore

    @property
    def _infer_input(self) -> Type[grpcclient.InferInput]:
        """Return the preferred InferInput."""
        return grpcclient.InferInput  # type: ignore

    @property
    def _infer_output(
        self,
    ) -> Type[grpcclient.InferRequestedOutput]:
        """Return the preferred InferRequestedOutput."""
        return grpcclient.InferRequestedOutput  # type: ignore

    def _send_stop_signals(self, model_name: str, request_id: str) -> None:
        """Send the stop signal to the Triton Inference server."""
        stop_inputs = self._generate_stop_signals()
        self._client.async_stream_infer(
            model_name,
            stop_inputs,
            request_id=request_id,
            parameters={"Streaming": True},
        )

    @staticmethod
    def _process_result(result: Dict[str, str]) -> str:
        """Post-process the result from the server."""
        message = ModelInferResponse()
        generated_text: str = ""
        google.protobuf.json_format.Parse(json.dumps(result), message)
        infer_result = grpcclient.InferResult(message)
        np_res = infer_result.as_numpy("text_output")

        generated_text = ""
        if np_res is not None:
            generated_text = "".join([token.decode() for token in np_res])

        return generated_text

    def _stream_callback(
        self,
        result_queue: queue.Queue[Union[Optional[Dict[str, str]], str]],
        force_batch: bool,
        result: Any,
        error: str,
    ) -> None:
        """Add streamed result to queue."""
        if error:
            result_queue.put(error)
        else:
            response_raw = result.get_response(as_json=True)
            if "outputs" in response_raw:
                # the very last response might have no output, just the final flag
                response = self._process_result(response_raw)
                if force_batch:
                    response = self._trim_batch_response(response)

                if response in STOP_WORDS:
                    result_queue.put(None)
                else:
                    result_queue.put(response)

            if response_raw["parameters"]["triton_final_response"]["bool_param"]:
                # end of the generation
                result_queue.put(None)

    # pylint: disable-next=too-many-arguments
    def _send_prompt_streaming(
        self,
        model_name: str,
        request_inputs: Any,
        request_outputs: Optional[Any],
        request_id: str,
        result_queue: StreamingResponseGenerator,
        force_batch: bool = False,
    ) -> None:
        """Send the prompt and start streaming the result."""
        self._client.start_stream(
            callback=partial(self._stream_callback, result_queue, force_batch)
        )
        self._client.async_stream_infer(
            model_name=model_name,
            inputs=request_inputs,
            outputs=request_outputs,
            request_id=request_id,
        )

    def request_streaming(
        self,
        model_name: str,
        request_id: Optional[str] = None,
        force_batch: bool = False,
        **params: Any,
    ) -> StreamingResponseGenerator:
        """Request a streaming connection."""
        if not self._client.is_model_ready(model_name):
            raise RuntimeError("Cannot request streaming, model is not loaded")

        if not request_id:
            request_id = str(random.randint(1, 9999999))  # nosec

        result_queue = StreamingResponseGenerator(self, request_id, force_batch)
        inputs = self._generate_inputs(stream=not force_batch, **params)
        outputs = self._generate_outputs()
        self._send_prompt_streaming(
            model_name,
            inputs,
            outputs,
            request_id,
            result_queue,
            force_batch,
        )
        return result_queue

    def stop_stream(
        self, model_name: str, request_id: str, signal: bool = True
    ) -> None:
        """Close the streaming connection."""
        if signal:
            self._send_stop_signals(model_name, request_id)
        self._client.stop_stream()


class HttpTritonClient(_BaseTritonClient):
    """HTTP connection to a triton inference server."""

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

    def request(
        self,
        model_name: str,
        **params: Any,
    ) -> str:
        """Request inferencing from the triton server."""
        if not self._client.is_model_ready(model_name):
            raise RuntimeError("Cannot request streaming, model is not loaded")

        # create model inputs and outputs
        inputs = self._generate_inputs(stream=False, **params)
        outputs = self._generate_outputs()

        # call the model for inference
        result = self._client.infer(model_name, inputs=inputs, outputs=outputs)
        result_str = "".join(
            [val.decode("utf-8") for val in result.as_numpy("text_output").tolist()]
        )

        # extract the generated part of the prompt
        # return(result_str)
        return self._trim_batch_response(result_str)
