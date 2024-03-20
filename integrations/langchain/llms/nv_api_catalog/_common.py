from __future__ import annotations

import json
import logging
import os
import time
from copy import deepcopy
from functools import partial
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import aiohttp
import requests
from langchain_core.pydantic_v1 import (
    BaseModel,
    Field,
    PrivateAttr,
    SecretStr,
    root_validator,
)
from requests.models import Response

from integrations.langchain.llms.nv_api_catalog._statics import MODEL_SPECS, Model

logger = logging.getLogger(__name__)

_MODE_TYPE = Literal["catalog", "nvidia", "nim", "open", "openai"]


class NVEModel(BaseModel):

    """
    Underlying Client for interacting with the AI Foundation Model Function API.
    Leveraged by the NVIDIABaseModel to provide a simple requests-oriented interface.
    Direct abstraction over NGC-recommended streaming/non-streaming Python solutions.

    NOTE: Models in the playground does not currently support raw text continuation.
    """

    ## Core defaults. These probably should not be changed
    _api_key_var = "NVIDIA_API_KEY"
    base_url: str = Field(
        "https://api.nvcf.nvidia.com/v2/nvcf",
        description="Base URL for standard inference",
    )
    get_session_fn: Callable = Field(requests.Session)
    get_asession_fn: Callable = Field(aiohttp.ClientSession)
    endpoints: dict = Field(
        {
            "infer": "{base_url}/pexec/functions/{model_id}",
            "status": "{base_url}/pexec/status/{request_id}",
            "models": "{base_url}/functions",
        }
    )

    api_key: SecretStr = Field(..., description="API Key for service of choice")
    is_staging: bool = Field(False, description="Whether to use staging API")

    ## Generation arguments
    timeout: float = Field(60, ge=0, description="Timeout for waiting on response (s)")
    interval: float = Field(0.02, ge=0, description="Interval for pulling response")
    last_inputs: dict = Field({}, description="Last inputs sent over to the server")
    last_response: dict = Field({}, description="Last response sent from the server")
    payload_fn: Callable = Field(lambda d: d, description="Function to process payload")
    headers_tmpl: dict = Field(
        ...,
        description="Headers template for API calls."
        " Should contain `call` and `stream` keys.",
    )
    _available_functions: Optional[List[dict]] = PrivateAttr(default=None)
    _available_models: Optional[dict] = PrivateAttr(default=None)

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True

    @property
    def lc_secrets(self) -> Dict[str, str]:
        return {"api_key": self._api_key_var}

    @property
    def headers(self) -> dict:
        """Return headers with API key injected"""
        headers_ = self.headers_tmpl.copy()
        for header in headers_.values():
            if "{api_key}" in header["Authorization"]:
                header["Authorization"] = header["Authorization"].format(
                    api_key=self.api_key.get_secret_value(),
                )
        return headers_

    @root_validator(pre=True)
    def validate_model(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and update model arguments, including API key and formatting"""
        values["api_key"] = (
            values.get(cls._api_key_var.lower())
            or values.get("api_key")
            or os.getenv(cls._api_key_var)
        )
        values["is_staging"] = "nvapi-stg-" in values["api_key"]
        if "headers_tmpl" not in values:
            call_kvs = {
                "Accept": "application/json",
            }
            stream_kvs = {
                "Accept": "text/event-stream",
                "content-type": "application/json",
            }
            shared_kvs = {
                "Authorization": "Bearer {api_key}",
                "User-Agent": "langchain-nvidia-ai-endpoints",
            }
            values["headers_tmpl"] = {
                "call": {**call_kvs, **shared_kvs},
                "stream": {**stream_kvs, **shared_kvs},
            }
        return values

    @root_validator(pre=False)
    def validate_model_post(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Additional validation after default values have been put in"""
        values["stagify"] = partial(cls._stagify, is_staging=values["is_staging"])
        values["base_url"] = values["stagify"](values.get("base_url"))
        return values

    @property
    def available_models(self) -> dict:
        """List the available models that can be invoked."""
        if self._available_models is not None:
            return self._available_models
        live_fns = self.available_functions
        if "status" in live_fns[0]:
            live_fns = [v for v in live_fns if v.get("status") == "ACTIVE"]
            self._available_models = {v["name"]: v["id"] for v in live_fns}
        else:
            self._available_models = {v.get("id"): v.get("owned_by") for v in live_fns}
        return self._available_models

    @property
    def available_functions(self) -> list:
        """List the available functions that can be invoked."""
        if self._available_functions and isinstance(self._available_functions, list):
            return self._available_functions
        if not self.endpoints.get("models"):
            raise ValueError("No models endpoint found, so cannot retrieve model list.")
        try:
            invoke_url = self.endpoints.get("models", "").format(base_url=self.base_url)
            query_res = self.query(invoke_url)
        except Exception as e:
            raise ValueError(f"Failed to query model endpoint {invoke_url}.\n{e}")
        output: list = []
        if isinstance(query_res.get("functions"), list):
            output = query_res.get("functions")
        elif isinstance(query_res.get("data"), list):
            output = query_res.get("data")
        else:
            raise ValueError(
                f"Unexpected response when querying {invoke_url}\n{query_res}"
            )
        self._available_functions = output
        return self._available_functions

    def reset_method_cache(self) -> None:
        """Reset method cache to force re-fetch of available functions"""
        self._available_functions = None
        self._available_models = None

    @staticmethod
    def _stagify(path: str, is_staging: bool) -> str:
        """Helper method to switch between staging and production endpoints"""
        if is_staging and "stg.api" not in path:
            return path.replace("api.", "stg.api.")
        if not is_staging and "stg.api" in path:
            return path.replace("stg.api.", "api.")
        return path

    ####################################################################################
    ## Core utilities for posting and getting from NV Endpoints

    def _post(
        self,
        invoke_url: str,
        payload: Optional[dict] = {},
    ) -> Tuple[Response, Any]:
        """Method for posting to the AI Foundation Model Function API."""
        self.last_inputs = {
            "url": invoke_url,
            "headers": self.headers["call"],
            "json": self.payload_fn(payload),
            "stream": False,
        }
        session = self.get_session_fn()
        self.last_response = response = session.post(**self.last_inputs)
        self._try_raise(response)
        return response, session

    def _get(
        self,
        invoke_url: str,
        payload: Optional[dict] = {},
    ) -> Tuple[Response, Any]:
        """Method for getting from the AI Foundation Model Function API."""
        self.last_inputs = {
            "url": invoke_url,
            "headers": self.headers["call"],
            "stream": False,
        }
        if payload:
            self.last_inputs["json"] = self.payload_fn(payload)
        session = self.get_session_fn()
        self.last_response = response = session.get(**self.last_inputs)
        self._try_raise(response)
        return response, session

    def _wait(self, response: Response, session: Any) -> Response:
        """Wait for a response from API after an initial response is made"""
        start_time = time.time()
        while response.status_code == 202:
            time.sleep(self.interval)
            if (time.time() - start_time) > self.timeout:
                raise TimeoutError(
                    f"Timeout reached without a successful response."
                    f"\nLast response: {str(response)}"
                )
            request_id = response.headers.get("NVCF-REQID", "")
            endpoint_args = {"base_url": self.base_url, "request_id": request_id}
            self.last_response = response = session.get(
                self.endpoints["status"].format(**endpoint_args),
                headers=self.headers["call"],
            )
        self._try_raise(response)
        return response

    def _try_raise(self, response: Response) -> None:
        """Try to raise an error from a response"""
        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                rd = response.json()
                if "detail" in rd and "reqId" in rd.get("detail", ""):
                    rd_buf = "- " + str(rd["detail"])
                    rd_buf = rd_buf.replace(": ", ", Error: ").replace(", ", "\n- ")
                    rd["detail"] = rd_buf
            except json.JSONDecodeError:
                rd = response.__dict__
                rd = rd.get("_content", rd)
                if isinstance(rd, bytes):
                    rd = rd.decode("utf-8")[5:]  ## remove "data:" prefix
                try:
                    rd = json.loads(rd)
                except Exception:
                    rd = {"detail": rd}
            status = rd.get("status", "###")
            title = rd.get("title", rd.get("error", "Unknown Error"))
            header = f"[{status}] {title}"
            body = ""
            if "requestId" in rd:
                if "detail" in rd:
                    body += f"{rd['detail']}\n"
                body += "RequestID: " + rd["requestId"]
            else:
                body = rd.get("detail", rd)
            if str(status) == "401":
                body += "\nPlease check or regenerate your API key."
            raise Exception(f"{header}\n{body}") from None

    ####################################################################################
    ## Simple query interface to show the set of model options

    def query(
        self,
        invoke_url: str,
        payload: Optional[dict] = None,
        request: str = "get",
    ) -> dict:
        """Simple method for an end-to-end get query. Returns result dictionary"""
        if request == "get":
            response, session = self._get(invoke_url, payload)
        else:
            response, session = self._post(invoke_url, payload)
        response = self._wait(response, session)
        output = self._process_response(response)[0]
        return output

    def _process_response(self, response: Union[str, Response]) -> List[dict]:
        """General-purpose response processing for single responses and streams"""
        if hasattr(response, "json"):  ## For single response (i.e. non-streaming)
            try:
                return [response.json()]
            except json.JSONDecodeError:
                response = str(response.__dict__)
        if isinstance(response, str):  ## For set of responses (i.e. streaming)
            msg_list = []
            for msg in response.split("\n\n"):
                if "{" not in msg:
                    continue
                msg_list += [json.loads(msg[msg.find("{") :])]
            return msg_list
        raise ValueError(f"Received ill-formed response: {response}")

    def _get_invoke_url(
        self,
        model_name: Optional[str] = None,
        invoke_url: Optional[str] = None,
        endpoint: str = "",
    ) -> str:
        """Helper method to get invoke URL from a model name, URL, or endpoint stub"""
        if not invoke_url:
            endpoint_str = self.endpoints.get(endpoint, "")
            if not endpoint_str:
                raise ValueError(f"Unknown endpoint referenced {endpoint} provided")
            if "{model_id}" in endpoint_str:
                if not model_name:
                    raise ValueError("URL or model name must be specified to invoke")
                if model_name in self.available_models:
                    model_id = self.available_models[model_name]
                elif f"playground_{model_name}" in self.available_models:
                    model_id = self.available_models[f"playground_{model_name}"]
                else:
                    available_models_str = "\n".join(
                        [f"{k} - {v}" for k, v in self.available_models.items()]
                    )
                    raise ValueError(
                        f"Unknown model name {model_name} specified."
                        "\nAvailable models are:\n"
                        f"{available_models_str}"
                    )
            else:
                model_id = ""

            endpoint_args = {"base_url": self.base_url, "model_id": model_id}
            invoke_url = endpoint_str.format(**endpoint_args)

        if not invoke_url:
            raise ValueError("URL or model name must be specified to invoke")

        return invoke_url

    ####################################################################################
    ## Generation interface to allow users to generate new values from endpoints

    def get_req(
        self,
        model_name: Optional[str] = None,
        payload: dict = {},
        invoke_url: Optional[str] = None,
        stop: Optional[Sequence[str]] = None,
        endpoint: str = "",
    ) -> Response:
        """Post to the API."""
        invoke_url = self._get_invoke_url(model_name, invoke_url, endpoint=endpoint)
        if payload.get("stream", False) is True:
            payload = {**payload, "stream": False}
        response, session = self._post(invoke_url, payload)
        return self._wait(response, session)

    def get_req_generation(
        self,
        model_name: Optional[str] = None,
        payload: dict = {},
        invoke_url: Optional[str] = None,
        stop: Optional[Sequence[str]] = None,
        endpoint: str = "infer",
    ) -> dict:
        """Method for an end-to-end post query with NVE post-processing."""
        invoke_url = self._get_invoke_url(model_name, invoke_url, endpoint=endpoint)
        response = self.get_req(model_name, payload, invoke_url)
        output, _ = self.postprocess(response, stop=stop)
        return output

    def postprocess(
        self, response: Union[str, Response], stop: Optional[Sequence[str]] = None
    ) -> Tuple[dict, bool]:
        """Parses a response from the AI Foundation Model Function API.
        Strongly assumes that the API will return a single response.
        """
        msg_list = self._process_response(response)
        msg, is_stopped = self._aggregate_msgs(msg_list)
        msg, is_stopped = self._early_stop_msg(msg, is_stopped, stop=stop)
        return msg, is_stopped

    def _aggregate_msgs(self, msg_list: Sequence[dict]) -> Tuple[dict, bool]:
        """Dig out relevant details of aggregated message"""
        content_buffer: Dict[str, Any] = dict()
        content_holder: Dict[Any, Any] = dict()
        usage_holder: Dict[Any, Any] = dict()  ####
        is_stopped = False
        for msg in msg_list:
            usage_holder = msg.get("usage", {})  ####
            if "choices" in msg:
                ## Tease out ['choices'][0]...['delta'/'message']
                msg = msg.get("choices", [{}])[0]
                is_stopped = msg.get("finish_reason", "") == "stop"
                msg = msg.get("delta", msg.get("message", msg.get("text", "")))
                if not isinstance(msg, dict):
                    msg = {"content": msg}
            elif "data" in msg:
                ## Tease out ['data'][0]...['embedding']
                msg = msg.get("data", [{}])[0]
            content_holder = msg
            for k, v in msg.items():
                if k in ("content",) and k in content_buffer:
                    content_buffer[k] += v
                else:
                    content_buffer[k] = v
            if is_stopped:
                break
        content_holder = {**content_holder, **content_buffer}
        if usage_holder:
            content_holder.update(token_usage=usage_holder)  ####
        return content_holder, is_stopped

    def _early_stop_msg(
        self, msg: dict, is_stopped: bool, stop: Optional[Sequence[str]] = None
    ) -> Tuple[dict, bool]:
        """Try to early-terminate streaming or generation by iterating over stop list"""
        content = msg.get("content", "")
        if content and stop:
            for stop_str in stop:
                if stop_str and stop_str in content:
                    msg["content"] = content[: content.find(stop_str) + 1]
                    is_stopped = True
        return msg, is_stopped

    ####################################################################################
    ## Streaming interface to allow you to iterate through progressive generations

    def get_req_stream(
        self,
        model: Optional[str] = None,
        payload: dict = {},
        invoke_url: Optional[str] = None,
        stop: Optional[Sequence[str]] = None,
        endpoint: str = "infer",
    ) -> Iterator:
        invoke_url = self._get_invoke_url(model, invoke_url, endpoint=endpoint)
        if payload.get("stream", True) is False:
            payload = {**payload, "stream": True}
        self.last_inputs = {
            "url": invoke_url,
            "headers": self.headers["stream"],
            "json": self.payload_fn(payload),
            "stream": True,
        }
        response = self.get_session_fn().post(**self.last_inputs)
        self._try_raise(response)
        call = self.copy()

        def out_gen() -> Generator[dict, Any, Any]:
            ## Good for client, since it allows self.last_inputs
            for line in response.iter_lines():
                if line and line.strip() != b"data: [DONE]":
                    line = line.decode("utf-8")
                    msg, final_line = call.postprocess(line, stop=stop)
                    yield msg
                    if final_line:
                        break
                self._try_raise(response)

        return (r for r in out_gen())

    ####################################################################################
    ## Asynchronous streaming interface to allow multiple generations to happen at once.

    async def get_req_astream(
        self,
        model: Optional[str] = None,
        payload: dict = {},
        invoke_url: Optional[str] = None,
        stop: Optional[Sequence[str]] = None,
        endpoint: str = "infer",
    ) -> AsyncIterator:
        invoke_url = self._get_invoke_url(model, invoke_url, endpoint=endpoint)
        if payload.get("stream", True) is False:
            payload = {**payload, "stream": True}
        self.last_inputs = {
            "url": invoke_url,
            "headers": self.headers["stream"],
            "json": self.payload_fn(payload),
        }
        async with self.get_asession_fn() as session:
            async with session.post(**self.last_inputs) as response:
                self._try_raise(response)
                async for line in response.content.iter_any():
                    if line and line.strip() != b"data: [DONE]":
                        line = line.decode("utf-8")
                        msg, final_line = self.postprocess(line, stop=stop)
                        yield msg
                        if final_line:
                            break


class _NVIDIAClient(BaseModel):
    """
    Higher-Level AI Foundation Model Function API Client with argument defaults.
    Is subclassed by ChatNVIDIA to provide a simple LangChain interface.
    """

    client: NVEModel = Field(NVEModel)

    _default_model: str = ""
    model: Optional[str] = Field(description="Name of the model to invoke")
    infer_endpoint: str = Field("{base_url}/chat/completions")
    curr_mode: _MODE_TYPE = Field("nvidia")

    ####################################################################################

    @root_validator(pre=True)
    def validate_client(cls, values: Any) -> Any:
        """Validate and update client arguments, including API key and formatting"""
        if not values.get("client"):
            values["client"] = NVEModel(**values)
        elif isinstance(values["client"], NVEModel):
            values["client"] = values["client"].__class__(**values["client"].dict())
        if not values.get("model"):
            values["model"] = cls._default_model
            assert values["model"], "No model given, with no default to fall back on."

        # the only model that doesn't support a stream parameter is kosmos_2.
        # to address this, we'll use the payload_fn to remove the stream parameter for kosmos_2.
        # if a user tries to set their own payload_fn, this patch will be overwritten.
        # todo: get kosmos_2 api updated to support stream parameter
        if values["model"] == "kosmos_2":
            def kosmos_patch(payload):
                payload.pop("stream", None)
                return payload
            values["client"].payload_fn = kosmos_patch

        return values

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True

    @property
    def lc_secrets(self) -> Dict[str, str]:
        return {"api_key": self.client._api_key_var}

    @property
    def lc_attributes(self) -> Dict[str, Any]:
        attributes: Dict[str, Any] = {}
        if getattr(self.client, "base_url"):
            attributes["base_url"] = self.client.base_url

        if self.model:
            attributes["model"] = self.model

        if getattr(self.client, "endpoints"):
            attributes["endpoints"] = self.client.endpoints

        return attributes

    @property
    def available_functions(self) -> List[dict]:
        """Map the available functions that can be invoked."""
        return self.__class__.get_available_functions(client=self)

    @property
    def available_models(self) -> List[Model]:
        """Map the available models that can be invoked."""
        return self.__class__.get_available_models(client=self)

    @classmethod
    def get_available_functions(
        cls,
        mode: Optional[_MODE_TYPE] = None,
        client: Optional[_NVIDIAClient] = None,
        **kwargs: Any,
    ) -> List[dict]:
        """Map the available functions that can be invoked. Callable from class"""
        nveclient = (client or cls(**kwargs)).mode(mode, **kwargs).client
        nveclient.reset_method_cache()
        return nveclient.available_functions

    @classmethod
    def get_available_models(
        cls,
        mode: Optional[_MODE_TYPE] = None,
        client: Optional[_NVIDIAClient] = None,
        list_all: bool = False,
        **kwargs: Any,
    ) -> List[Model]:
        """Map the available models that can be invoked. Callable from class"""
        nveclient = (client or cls(**kwargs)).mode(mode, **kwargs).client
        nveclient.reset_method_cache()
        out = sorted(
            [
                Model(id=k.replace("playground_", ""), path=v, **MODEL_SPECS.get(k, {}))
                for k, v in nveclient.available_models.items()
            ],
            key=lambda x: f"{x.client or 'Z'}{x.id}{cls}",
        )
        if not list_all:
            out = [m for m in out if m.client == cls.__name__ or m.model_type is None]
        return out

    def get_model_details(self, model: Optional[str] = None) -> dict:
        """Get more meta-details about a model retrieved by a given name"""
        if model is None:
            model = self.model
        model_key = self.client._get_invoke_url(model).split("/")[-1]
        known_fns = self.client.available_functions
        fn_spec = [f for f in known_fns if f.get("id") == model_key][0]
        return fn_spec

    def get_binding_model(self) -> Optional[str]:
        """Get the model to bind to the client as default payload argument"""
        # if a model is configured with a model_name, always use that
        # todo: move from search of available_models to a Model property
        matches = [model for model in self.available_models if model.id == self.model]
        if matches:
            if matches[0].model_name:
                return matches[0].model_name
        if self.curr_mode == "catalog":
            return f"playground_{self.model}"
        if self.curr_mode == "nvidia":
            return ""
        return self.model

    def mode(
        self,
        mode: Optional[_MODE_TYPE] = "nvidia",
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        infer_path: Optional[str] = None,
        models_path: Optional[str] = "{base_url}/models",
        force_mode: bool = False,
        force_clone: bool = True,
        **kwargs: Any,
    ) -> _NVIDIAClient:
        """Return a client swapped to a different mode"""
        if isinstance(self, str):
            raise ValueError("Please construct the model before calling mode()")
        out = self if not force_clone else deepcopy(self)

        if mode is None:
            return out

        out.model = model or out.model

        if base_url and not force_mode:
            ## If a user tries to set base_url, assume custom openapi unless forced
            mode = "open"

        if mode in ["nvidia", "catalog"]:
            key_var = "NVIDIA_API_KEY"
            if not api_key or not api_key.startswith("nvapi-"):
                api_key = os.getenv(key_var) or out.client.api_key.get_secret_value()
            if not api_key.startswith("nvapi-"):
                raise ValueError(f"No {key_var} in env/fed as api_key. (nvapi-...)")

        if mode in ["openai"]:
            key_var = "OPENAI_API_KEY"
            if not api_key or not api_key.startswith("sk-"):
                api_key = os.getenv(key_var) or out.client.api_key.get_secret_value()
            if not api_key.startswith("sk-"):
                raise ValueError(f"No {key_var} in env/fed as api_key. (sk-...)")

        out.curr_mode = mode
        if api_key:
            out.client.api_key = SecretStr(api_key)

        catalog_base = "https://integrate.api.nvidia.com/v1"
        openai_base = "https://api.openai.com/v1"  ## OpenAI Main URL
        nvcf_base = "https://api.nvcf.nvidia.com/v2/nvcf"  ## NVCF Main URL
        nvcf_infer = "{base_url}/pexec/functions/{model_id}"  ## Inference endpoints
        nvcf_status = "{base_url}/pexec/status/{request_id}"  ## 202 wait handle
        nvcf_models = "{base_url}/functions"  ## Model listing

        if mode == "nvidia":
            ## Classic support for nvcf-backed foundation model endpoints.
            out.client.base_url = base_url or nvcf_base
            out.client.endpoints = {
                "infer": nvcf_infer,  ## Per-model inference
                "status": nvcf_status,  ## 202 wait handle
                "models": nvcf_models,  ## Model listing
            }

        elif mode == "catalog":
            ## NVIDIA API Catalog Integration: OpenAPI-spec gateway over NVCF endpoints
            out.client.base_url = base_url or catalog_base
            out.client.endpoints["infer"] = infer_path or out.infer_endpoint
            ## API Catalog is early, so no models list yet. Undercut to nvcf for now.
            out.client.endpoints["models"] = nvcf_models.format(base_url=nvcf_base)

        elif mode == "open" or mode == "nim":
            ## OpenAPI-style specs to connect to NeMo Inference Microservices etc.
            ## Most generic option, requires specifying base_url
            assert base_url, "Base URL must be specified for open/nim mode"
            out.client.base_url = base_url
            out.client.endpoints["infer"] = infer_path or out.infer_endpoint
            out.client.endpoints["models"] = models_path or "{base_url}/models"

        elif mode == "openai":
            ## OpenAI-style specification to connect to OpenAI endpoints
            out.client.base_url = base_url or openai_base
            out.client.endpoints["infer"] = infer_path or out.infer_endpoint
            out.client.endpoints["models"] = models_path or "{base_url}/models"

        else:
            options = ["catalog", "nvidia", "nim", "open", "openai"]
            raise ValueError(f"Unknown mode: `{mode}`. Expected one of {options}.")

        out.client.reset_method_cache()

        return out
