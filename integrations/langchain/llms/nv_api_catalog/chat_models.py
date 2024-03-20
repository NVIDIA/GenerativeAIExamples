"""Chat Model Components Derived from ChatModel/NVIDIA"""

from __future__ import annotations

import base64
import io
import logging
import os
import sys
import urllib.parse
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)

import requests
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.messages import (
    BaseMessage,
    ChatMessage,
    ChatMessageChunk,
)
from langchain_core.outputs import (
    ChatGeneration,
    ChatGenerationChunk,
    ChatResult,
)
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import run_in_executor
from langchain_core.tools import BaseTool

from integrations.langchain.llms.nv_api_catalog import _common as nvidia_ai_endpoints

_CallbackManager = Union[AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun]
_DictOrPydanticClass = Union[Dict[str, Any], Type[BaseModel]]
_DictOrPydantic = Union[Dict, BaseModel]

try:
    import PIL.Image

    has_pillow = True
except ImportError:
    has_pillow = False

logger = logging.getLogger(__name__)


def _is_url(s: str) -> bool:
    try:
        result = urllib.parse.urlparse(s)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.debug(f"Unable to parse URL: {e}")
        return False


def _resize_image(img_data: bytes, max_dim: int = 1024) -> str:
    if not has_pillow:
        print(  # noqa: T201
            "Pillow is required to resize images down to reasonable scale."
            " Please install it using `pip install pillow`."
            " For now, not resizing; may cause NVIDIA API to fail."
        )
        return base64.b64encode(img_data).decode("utf-8")
    image = PIL.Image.open(io.BytesIO(img_data))
    max_dim_size = max(image.size)
    aspect_ratio = max_dim / max_dim_size
    new_h = int(image.size[1] * aspect_ratio)
    new_w = int(image.size[0] * aspect_ratio)
    resized_image = image.resize((new_w, new_h), PIL.Image.Resampling.LANCZOS)
    output_buffer = io.BytesIO()
    resized_image.save(output_buffer, format="JPEG")
    output_buffer.seek(0)
    resized_b64_string = base64.b64encode(output_buffer.read()).decode("utf-8")
    return resized_b64_string


def _url_to_b64_string(image_source: str) -> str:
    b64_template = "data:image/png;base64,{b64_string}"
    try:
        if _is_url(image_source):
            response = requests.get(image_source)
            response.raise_for_status()
            encoded = base64.b64encode(response.content).decode("utf-8")
            if sys.getsizeof(encoded) > 200000:
                ## (VK) Temporary fix. NVIDIA API has a limit of 250KB for the input.
                encoded = _resize_image(response.content)
            return b64_template.format(b64_string=encoded)
        elif image_source.startswith("data:image"):
            return image_source
        elif os.path.exists(image_source):
            with open(image_source, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return b64_template.format(b64_string=encoded)
        else:
            raise ValueError(
                "The provided string is not a valid URL, base64, or file path."
            )
    except Exception as e:
        raise ValueError(f"Unable to process the provided image source: {e}")


class ChatNVIDIA(nvidia_ai_endpoints._NVIDIAClient, BaseChatModel):
    """NVIDIA chat model.

    Example:
        .. code-block:: python

            from integrations.langchain.llms.nv_api_catalog import ChatNVIDIA


            model = ChatNVIDIA(model="llama2_13b")
            response = model.invoke("Hello")
    """

    _default_model: str = "mixtral_8x7b"
    infer_endpoint: str = Field("{base_url}/chat/completions")
    model: str = Field(_default_model, description="Name of the model to invoke")
    temperature: Optional[float] = Field(description="Sampling temperature in [0, 1]")
    max_tokens: Optional[int] = Field(description="Maximum # of tokens to generate")
    top_p: Optional[float] = Field(description="Top-p for distribution sampling")
    seed: Optional[int] = Field(description="The seed for deterministic results")
    bad: Optional[Sequence[str]] = Field(description="Bad words to avoid (cased)")
    stop: Optional[Sequence[str]] = Field(description="Stop words (cased)")
    labels: Optional[Dict[str, float]] = Field(description="Steering parameters")
    streaming: bool = Field(True)

    @property
    def _llm_type(self) -> str:
        """Return type of NVIDIA AI Foundation Model Interface."""
        return "chat-nvidia-ai-playground"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        responses = self._call(messages, stop=stop, run_manager=run_manager, **kwargs)
        self._set_callback_out(responses, run_manager)
        message = ChatMessage(**self.custom_postprocess(responses))
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation], llm_output=responses)

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return await run_in_executor(
            None,
            self._generate,
            messages,
            stop=stop,
            run_manager=run_manager.get_sync() if run_manager else None,
            **kwargs,
        )

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[Sequence[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> dict:
        """Invoke on a single list of chat messages."""
        inputs = self.custom_preprocess(messages)
        responses = self.get_generation(inputs=inputs, stop=stop, **kwargs)
        return responses

    def _get_filled_chunk(self, **kwargs: Any) -> ChatGenerationChunk:
        """Fill the generation chunk."""
        return ChatGenerationChunk(message=ChatMessageChunk(**kwargs))

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[Sequence[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Allows streaming to model!"""
        inputs = self.custom_preprocess(messages)
        for response in self.get_stream(inputs=inputs, stop=stop, **kwargs):
            self._set_callback_out(response, run_manager)
            chunk = self._get_filled_chunk(**self.custom_postprocess(response))
            if run_manager:
                run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            yield chunk

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[Sequence[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        inputs = self.custom_preprocess(messages)
        async for response in self.get_astream(inputs=inputs, stop=stop, **kwargs):
            self._set_callback_out(response, run_manager)
            chunk = self._get_filled_chunk(**self.custom_postprocess(response))
            if run_manager:
                await run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            yield chunk

    def _set_callback_out(
        self,
        result: dict,
        run_manager: Optional[_CallbackManager],
    ) -> None:
        result.update({"model_name": self.model})
        if run_manager:
            for cb in run_manager.handlers:
                if hasattr(cb, "llm_output"):
                    cb.llm_output = result

    def custom_preprocess(
        self, msg_list: Sequence[BaseMessage]
    ) -> List[Dict[str, str]]:
        return [self.preprocess_msg(m) for m in msg_list]

    def _process_content(self, content: Union[str, List[Union[dict, str]]]) -> str:
        if isinstance(content, str):
            return content
        string_array: list = []

        for part in content:
            if isinstance(part, str):
                string_array.append(part)
            elif isinstance(part, Mapping):
                # OpenAI Format
                if "type" in part:
                    if part["type"] == "text":
                        string_array.append(str(part["text"]))
                    elif part["type"] == "image_url":
                        img_url = part["image_url"]
                        if isinstance(img_url, dict):
                            if "url" not in img_url:
                                raise ValueError(
                                    f"Unrecognized message image format: {img_url}"
                                )
                            img_url = img_url["url"]
                        b64_string = _url_to_b64_string(img_url)
                        string_array.append(f'<img src="{b64_string}" />')
                    else:
                        raise ValueError(
                            f"Unrecognized message part type: {part['type']}"
                        )
                else:
                    raise ValueError(f"Unrecognized message part format: {part}")
        return "".join(string_array)

    def preprocess_msg(self, msg: BaseMessage) -> Dict[str, str]:
        if isinstance(msg, BaseMessage):
            role_convert = {"ai": "assistant", "human": "user"}
            if isinstance(msg, ChatMessage):
                role = msg.role
            else:
                role = msg.type
            role = role_convert.get(role, role)
            content = self._process_content(msg.content)
            return {"role": role, "content": content}
        raise ValueError(f"Invalid message: {repr(msg)} of type {type(msg)}")

    def custom_postprocess(self, msg: dict) -> dict:
        kw_left = msg.copy()
        out_dict = {
            "role": kw_left.pop("role", "assistant") or "assistant",
            "name": kw_left.pop("name", None),
            "id": kw_left.pop("id", None),
            "content": kw_left.pop("content", "") or "",
            "additional_kwargs": {},
            "response_metadata": {},
        }
        for k in list(kw_left.keys()):
            if "tool" in k:
                out_dict["additional_kwargs"][k] = kw_left.pop(k)
        out_dict["response_metadata"] = kw_left
        return out_dict

    ######################################################################################
    ## Core client-side interfaces

    def get_generation(
        self,
        inputs: Sequence[Dict],
        **kwargs: Any,
    ) -> dict:
        """Call to client generate method with call scope"""
        stop = kwargs["stop"] = kwargs.get("stop") or self.stop
        payload = self.get_payload(inputs=inputs, stream=False, **kwargs)
        out = self.client.get_req_generation(self.model, stop=stop, payload=payload)
        return out

    def get_stream(
        self,
        inputs: Sequence[Dict],
        **kwargs: Any,
    ) -> Iterator:
        """Call to client stream method with call scope"""
        stop = kwargs["stop"] = kwargs.get("stop") or self.stop
        payload = self.get_payload(inputs=inputs, stream=True, **kwargs)
        return self.client.get_req_stream(self.model, stop=stop, payload=payload)

    def get_astream(
        self,
        inputs: Sequence[Dict],
        **kwargs: Any,
    ) -> AsyncIterator:
        """Call to client astream methods with call scope"""
        stop = kwargs["stop"] = kwargs.get("stop") or self.stop
        payload = self.get_payload(inputs=inputs, stream=True, **kwargs)
        return self.client.get_req_astream(self.model, stop=stop, payload=payload)

    def get_payload(self, inputs: Sequence[Dict], **kwargs: Any) -> dict:
        """Generates payload for the _NVIDIAClient API to send to service."""
        attr_kwargs = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "seed": self.seed,
            "bad": self.bad,
            "stop": self.stop,
            "labels": self.labels,
        }
        if model_name := self.get_binding_model():
            attr_kwargs["model"] = model_name
        attr_kwargs = {k: v for k, v in attr_kwargs.items() if v is not None}
        new_kwargs = {**attr_kwargs, **kwargs}
        return self.prep_payload(inputs=inputs, **new_kwargs)

    def prep_payload(self, inputs: Sequence[Dict], **kwargs: Any) -> dict:
        """Prepares a message or list of messages for the payload"""
        messages = [self.prep_msg(m) for m in inputs]
        if kwargs.get("labels"):
            # (WFH) Labels are currently (?) always passed as an assistant
            # suffix message, but this API seems less stable.
            messages += [{"labels": kwargs.pop("labels"), "role": "assistant"}]
        if kwargs.get("stop") is None:
            kwargs.pop("stop")
        return {"messages": messages, **kwargs}

    def prep_msg(self, msg: Union[str, dict, BaseMessage]) -> dict:
        """Helper Method: Ensures a message is a dictionary with a role and content."""
        if isinstance(msg, str):
            # (WFH) this shouldn't ever be reached but leaving this here bcs
            # it's a Chesterton's fence I'm unwilling to touch
            return dict(role="user", content=msg)
        if isinstance(msg, dict):
            if msg.get("content", None) is None:
                raise ValueError(f"Message {msg} has no content")
            return msg
        raise ValueError(f"Unknown message received: {msg} of type {type(msg)}")

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable, BaseTool]],
        *,
        tool_choice: Optional[Union[dict, str, Literal["auto", "none"], bool]] = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        raise NotImplementedError(
            "Not implemented, awaiting server-side function-recieving API"
            " Consider following open-source LLM agent spec techniques:"
            " https://huggingface.co/blog/open-source-llms-as-agents"
        )

    def bind_functions(
        self,
        functions: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable]],
        function_call: Optional[str] = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        raise NotImplementedError(
            "Not implemented, awaiting server-side function-recieving API"
            " Consider following open-source LLM agent spec techniques:"
            " https://huggingface.co/blog/open-source-llms-as-agents"
        )

    def with_structured_output(
        self,
        schema: _DictOrPydanticClass,
        *,
        method: Literal["function_calling", "json_mode"] = "function_calling",
        return_type: Literal["parsed", "all"] = "parsed",
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, _DictOrPydantic]:
        raise NotImplementedError(
            "Not implemented, awaiting server-side function-recieving API"
            " Consider following open-source LLM agent spec techniques:"
            " https://huggingface.co/blog/open-source-llms-as-agents"
        )
