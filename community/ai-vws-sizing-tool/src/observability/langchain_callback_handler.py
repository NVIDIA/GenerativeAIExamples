# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import json
import logging
import os
import time
import traceback
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, AIMessageChunk
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.outputs import LLMResult
from opentelemetry import context as context_api
from opentelemetry.context.context import Context
from opentelemetry.instrumentation.utils import _SUPPRESS_INSTRUMENTATION_KEY
from opentelemetry.semconv_ai import (
    SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY,
    LLMRequestTypeValues,
    SpanAttributes,
    TraceloopSpanKindValues,
)
from opentelemetry.trace import SpanKind, Tracer, set_span_in_context
from opentelemetry.trace.span import Span
from pydantic import BaseModel
from .otel_metrics import OtelMetrics


class Config:
    exception_logger = None


class CallbackFilteredJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, dict):
            if "callbacks" in o:
                del o["callbacks"]
                return o

        if is_dataclass(o):
            return asdict(o)

        if hasattr(o, "to_json"):
            return o.to_json()

        if isinstance(o, BaseModel) and hasattr(o, "model_dump_json"):
            return o.model_dump_json()

        return super().default(o)


def should_send_prompts():
    return (
        os.getenv("TRACELOOP_TRACE_CONTENT") or "true"
    ).lower() == "true" or context_api.get_value("override_enable_content_tracing")


def dont_throw(func):
    """
    A decorator that wraps the passed in function and logs exceptions instead of throwing them.

    @param func: The function to wrap
    @return: The wrapper function
    """
    # Obtain a logger specific to the function's module
    logger = logging.getLogger(func.__module__)

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.debug(
                "OpenLLMetry failed to trace in %s, error: %s",
                func.__name__,
                traceback.format_exc(),
            )
            if Config.exception_logger:
                Config.exception_logger(e)

    return wrapper


@dataclass
class SpanHolder:
    span: Span
    token: Any
    context: Context
    children: list[UUID]
    workflow_name: str
    entity_name: str
    entity_path: str
    start_time: float = field(default_factory=time.time)
    request_model: Optional[str] = None


def _message_type_to_role(message_type: str) -> str:
    if message_type == "human":
        return "user"
    elif message_type == "system":
        return "system"
    elif message_type == "ai":
        return "assistant"
    else:
        return "unknown"


def _set_span_attribute(span, name, value):
    if value is not None:
        span.set_attribute(name, value)


def _set_request_params(span, kwargs, span_holder: SpanHolder):
    for model_tag in ("model", "model_id", "model_name"):
        if (model := kwargs.get(model_tag)) is not None:
            span_holder.request_model = model
            break
        elif (
            model := (kwargs.get("invocation_params") or {}).get(model_tag)
        ) is not None:
            span_holder.request_model = model
            break
    else:
        model = "unknown"

    span.set_attribute(SpanAttributes.LLM_REQUEST_MODEL, model)
    # response is not available for LLM requests (as opposed to chat)
    span.set_attribute(SpanAttributes.LLM_RESPONSE_MODEL, model)

    if "invocation_params" in kwargs:
        params = (
            kwargs["invocation_params"].get("params") or kwargs["invocation_params"]
        )
    else:
        params = kwargs

    _set_span_attribute(
        span,
        SpanAttributes.LLM_REQUEST_MAX_TOKENS,
        params.get("max_tokens") or params.get("max_new_tokens"),
    )
    _set_span_attribute(
        span, SpanAttributes.LLM_REQUEST_TEMPERATURE, params.get("temperature")
    )
    _set_span_attribute(span, SpanAttributes.LLM_REQUEST_TOP_P, params.get("top_p"))


def _set_llm_request(
    span: Span,
    serialized: dict[str, Any],
    prompts: list[str],
    kwargs: Any,
    span_holder: SpanHolder,
) -> None:
    _set_request_params(span, kwargs, span_holder)

    if should_send_prompts():
        for i, msg in enumerate(prompts):
            span.set_attribute(
                f"{SpanAttributes.LLM_PROMPTS}.{i}.role",
                "user",
            )
            span.set_attribute(
                f"{SpanAttributes.LLM_PROMPTS}.{i}.content",
                msg,
            )


def _set_chat_request(
    span: Span,
    serialized: dict[str, Any],
    messages: list[list[BaseMessage]],
    kwargs: Any,
    span_holder: SpanHolder,
) -> None:
    _set_request_params(span, serialized.get("kwargs", {}), span_holder)

    if should_send_prompts():
        for i, function in enumerate(
            kwargs.get("invocation_params", {}).get("functions", [])
        ):
            prefix = f"{SpanAttributes.LLM_REQUEST_FUNCTIONS}.{i}"

            _set_span_attribute(span, f"{prefix}.name", function.get("name"))
            _set_span_attribute(
                span, f"{prefix}.description", function.get("description")
            )
            _set_span_attribute(
                span, f"{prefix}.parameters", json.dumps(function.get("parameters"))
            )

        i = 0
        for message in messages:
            for msg in message:
                span.set_attribute(
                    f"{SpanAttributes.LLM_PROMPTS}.{i}.role",
                    _message_type_to_role(msg.type),
                )
                # if msg.content is string
                if isinstance(msg.content, str):
                    span.set_attribute(
                        f"{SpanAttributes.LLM_PROMPTS}.{i}.content",
                        msg.content,
                    )
                else:
                    span.set_attribute(
                        f"{SpanAttributes.LLM_PROMPTS}.{i}.content",
                        json.dumps(msg.content, cls=CallbackFilteredJSONEncoder),
                    )
                i += 1


def _set_chat_response(span: Span, response: LLMResult) -> None:
    if not should_send_prompts():
        return

    input_tokens = 0
    output_tokens = 0
    total_tokens = 0

    i = 0
    for generations in response.generations:
        for generation in generations:
            if (
                hasattr(generation, "message")
                and hasattr(generation.message, "usage_metadata")
                and generation.message.usage_metadata is not None
            ):
                input_tokens += (
                    generation.message.usage_metadata.get("input_tokens")
                    or generation.message.usage_metadata.get("prompt_tokens")
                    or 0
                )
                output_tokens += (
                    generation.message.usage_metadata.get("output_tokens")
                    or generation.message.usage_metadata.get("completion_tokens")
                    or 0
                )
                total_tokens = input_tokens + output_tokens

            prefix = f"{SpanAttributes.LLM_COMPLETIONS}.{i}"
            if hasattr(generation, "text") and generation.text != "":
                span.set_attribute(
                    f"{prefix}.content",
                    generation.text,
                )
                span.set_attribute(f"{prefix}.role", "assistant")
            else:
                span.set_attribute(
                    f"{prefix}.role",
                    _message_type_to_role(generation.type),
                )
                if generation.message.content is str:
                    span.set_attribute(
                        f"{prefix}.content",
                        generation.message.content,
                    )
                else:
                    span.set_attribute(
                        f"{prefix}.content",
                        json.dumps(
                            generation.message.content, cls=CallbackFilteredJSONEncoder
                        ),
                    )
                if generation.generation_info.get("finish_reason"):
                    span.set_attribute(
                        f"{prefix}.finish_reason",
                        generation.generation_info.get("finish_reason"),
                    )

                if generation.message.additional_kwargs.get("function_call"):
                    span.set_attribute(
                        f"{prefix}.tool_calls.0.name",
                        generation.message.additional_kwargs.get("function_call").get(
                            "name"
                        ),
                    )
                    span.set_attribute(
                        f"{prefix}.tool_calls.0.arguments",
                        generation.message.additional_kwargs.get("function_call").get(
                            "arguments"
                        ),
                    )

                if generation.message.additional_kwargs.get("tool_calls"):
                    for idx, tool_call in enumerate(
                        generation.message.additional_kwargs.get("tool_calls")
                    ):
                        tool_call_prefix = f"{prefix}.tool_calls.{idx}"

                        span.set_attribute(
                            f"{tool_call_prefix}.id", tool_call.get("id")
                        )
                        span.set_attribute(
                            f"{tool_call_prefix}.name",
                            tool_call.get("function").get("name"),
                        )
                        span.set_attribute(
                            f"{tool_call_prefix}.arguments",
                            tool_call.get("function").get("arguments"),
                        )
            i += 1

    if input_tokens > 0 or output_tokens > 0 or total_tokens > 0:
        span.set_attribute(
            SpanAttributes.LLM_USAGE_PROMPT_TOKENS,
            input_tokens,
        )
        span.set_attribute(
            SpanAttributes.LLM_USAGE_COMPLETION_TOKENS,
            output_tokens,
        )
        span.set_attribute(
            SpanAttributes.LLM_USAGE_TOTAL_TOKENS,
            total_tokens,
        )


class LangchainCallbackHandler(BaseCallbackHandler):
    def __init__(self, tracer: Tracer, metrics: OtelMetrics) -> None:
        super().__init__()
        self.tracer = tracer
        self.metrics = metrics
        self.total_input_words = 0
        self.total_output_words = 0
        self.spans: dict[UUID, SpanHolder] = {}
        self.run_inline = True

    @staticmethod
    def _get_name_from_callback(
        serialized: dict[str, Any],
        _tags: Optional[list[str]] = None,
        _metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Get the name to be used for the span. Based on heuristic. Can be extended."""
        if serialized and "kwargs" in serialized and serialized["kwargs"].get("name"):
            return serialized["kwargs"]["name"]
        if kwargs.get("name"):
            return kwargs["name"]
        if serialized.get("name"):
            return serialized["name"]
        if "id" in serialized:
            return serialized["id"][-1]

        return "unknown"

    def _get_span(self, run_id: UUID) -> Span:
        return self.spans[run_id].span

    def _end_span(self, span: Span, run_id: UUID) -> None:
        for child_id in self.spans[run_id].children:
            child_span = self.spans[child_id].span
            if child_span.end_time is None:  # avoid warning on ended spans
                child_span.end()
        span.end()

    def _create_span(
        self,
        run_id: UUID,
        parent_run_id: Optional[UUID],
        span_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        workflow_name: str = "",
        entity_name: str = "",
        entity_path: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> Span:
        if metadata is not None:
            current_association_properties = (
                context_api.get_value("association_properties") or {}
            )
            context_api.attach(
                context_api.set_value(
                    "association_properties",
                    {**current_association_properties, **metadata},
                )
            )
        if parent_run_id is not None and parent_run_id in self.spans:
            span = self.tracer.start_span(
                span_name,
                context=set_span_in_context(self.spans[parent_run_id].span),
                kind=kind,
            )
        else:
            span = self.tracer.start_span(span_name, kind=kind)

        span.set_attribute(SpanAttributes.TRACELOOP_WORKFLOW_NAME, workflow_name)
        span.set_attribute(SpanAttributes.TRACELOOP_ENTITY_PATH, entity_path)

        token = context_api.attach(
            context_api.set_value(SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY, True)
        )

        self.spans[run_id] = SpanHolder(
            span, token, None, [], workflow_name, entity_name, entity_path
        )

        if parent_run_id is not None and parent_run_id in self.spans:
            self.spans[parent_run_id].children.append(run_id)

        return span

    def _create_task_span(
        self,
        run_id: UUID,
        parent_run_id: Optional[UUID],
        name: str,
        kind: TraceloopSpanKindValues,
        workflow_name: str,
        entity_name: str = "",
        entity_path: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> Span:
        span_name = f"{name}.{kind.value}"
        span = self._create_span(
            run_id,
            parent_run_id,
            span_name,
            workflow_name=workflow_name,
            entity_name=entity_name,
            entity_path=entity_path,
            metadata=metadata,
        )

        span.set_attribute(SpanAttributes.TRACELOOP_SPAN_KIND, kind.value)
        span.set_attribute(SpanAttributes.TRACELOOP_ENTITY_NAME, entity_name)

        return span

    def _create_llm_span(
        self,
        run_id: UUID,
        parent_run_id: Optional[UUID],
        name: str,
        request_type: LLMRequestTypeValues,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Span:
        workflow_name = self.get_workflow_name(parent_run_id)
        entity_path = self.get_entity_path(parent_run_id)

        span = self._create_span(
            run_id,
            parent_run_id,
            f"{name}.{request_type.value}",
            kind=SpanKind.CLIENT,
            workflow_name=workflow_name,
            entity_path=entity_path,
            metadata=metadata,
        )
        span.set_attribute(SpanAttributes.LLM_SYSTEM, "Langchain")
        span.set_attribute(SpanAttributes.LLM_REQUEST_TYPE, request_type.value)

        return span

    @dont_throw
    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain starts running."""

        if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return
        workflow_name = ""
        entity_path = ""

        name = self._get_name_from_callback(serialized, **kwargs)
        kind = (
            TraceloopSpanKindValues.WORKFLOW
            if parent_run_id is None or parent_run_id not in self.spans
            else TraceloopSpanKindValues.TASK
        )

        if kind == TraceloopSpanKindValues.WORKFLOW:
            workflow_name = name
        else:
            workflow_name = self.get_workflow_name(parent_run_id)
            entity_path = self.get_entity_path(parent_run_id)

        span = self._create_task_span(
            run_id,
            parent_run_id,
            name,
            kind,
            workflow_name,
            name,
            entity_path,
            metadata,
        )
        if should_send_prompts():
            span.set_attribute(
                SpanAttributes.TRACELOOP_ENTITY_INPUT,
                json.dumps(
                    {
                        "inputs": inputs,
                        "tags": tags,
                        "metadata": metadata,
                        "kwargs": kwargs,
                    },
                    cls=CallbackFilteredJSONEncoder,
                ),
            )

    @dont_throw
    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain ends running."""
        if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return
        span_holder = self.spans[run_id]
        span = span_holder.span
        if should_send_prompts():
            if kwargs.get("inputs"):
                inputs = kwargs.get("inputs")
                if isinstance(inputs, dict) and "context" in inputs.keys():
                    context = inputs.get("context")
                    chunk_count = len(context)
                    total_words_in_context = 0
                    for chunk in context:
                        total_words_in_context += len(chunk.split())
                    avg_words_per_chunk = int(total_words_in_context / chunk_count)
                    self.metrics.update_avg_words_per_chunk(
                        avg_words_per_chunk=avg_words_per_chunk
                    )
                elif isinstance(inputs, AIMessageChunk):
                    self.total_output_words = len(inputs.content.split())
                    self.metrics.update_llm_tokens(
                        input_t=self.total_input_words,
                        output_t=self.total_output_words,
                    )
            span.set_attribute(
                SpanAttributes.TRACELOOP_ENTITY_OUTPUT,
                json.dumps(
                    {"outputs": outputs, "kwargs": kwargs},
                    cls=CallbackFilteredJSONEncoder,
                ),
            )

        self._end_span(span, run_id)
        if parent_run_id is None:
            context_api.attach(
                context_api.set_value(
                    SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY, False
                )
            )

    @dont_throw
    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        tags: Optional[list[str]] = None,
        parent_run_id: Optional[UUID] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when Chat Model starts running."""

        if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return

        self.total_input_words = 0
        for message in messages:
            for msg in message:
                if isinstance(msg.content, str):
                    self.total_input_words += len(msg.content.split())

        name = self._get_name_from_callback(serialized, kwargs=kwargs)
        span = self._create_llm_span(
            run_id, parent_run_id, name, LLMRequestTypeValues.CHAT, metadata=metadata
        )
        _set_chat_request(span, serialized, messages, kwargs, self.spans[run_id])

    @dont_throw
    def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        """Run on new LLM token. Only available when streaming is enabled."""
        # TODO: add error handling
        span = self.spans[kwargs.get("run_id")].span
        span.add_event("on_llm_new_token")

    @dont_throw
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        tags: Optional[list[str]] = None,
        parent_run_id: Optional[UUID] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when Chat Model starts running."""
        if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return

        name = self._get_name_from_callback(serialized, kwargs=kwargs)
        span = self._create_llm_span(
            run_id, parent_run_id, name, LLMRequestTypeValues.COMPLETION
        )
        _set_llm_request(span, serialized, prompts, kwargs, self.spans[run_id])

    @dont_throw
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Union[UUID, None] = None,
        **kwargs: Any,
    ):
        if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return

        span = self._get_span(run_id)

        model_name = None
        if response.llm_output is not None:
            model_name = response.llm_output.get(
                "model_name"
            ) or response.llm_output.get("model_id")
            if model_name is not None:
                span.set_attribute(SpanAttributes.LLM_RESPONSE_MODEL, model_name)

                if self.spans[run_id].request_model is None:
                    span.set_attribute(SpanAttributes.LLM_REQUEST_MODEL, model_name)

        token_usage = (response.llm_output or {}).get("token_usage") or (
            response.llm_output or {}
        ).get("usage")
        if token_usage is not None:
            prompt_tokens = (
                token_usage.get("prompt_tokens")
                or token_usage.get("input_token_count")
                or token_usage.get("input_tokens")
            )
            completion_tokens = (
                token_usage.get("completion_tokens")
                or token_usage.get("generated_token_count")
                or token_usage.get("output_tokens")
            )
            total_tokens = token_usage.get("total_tokens") or (
                prompt_tokens + completion_tokens
            )

            _set_span_attribute(
                span, SpanAttributes.LLM_USAGE_PROMPT_TOKENS, prompt_tokens
            )
            _set_span_attribute(
                span, SpanAttributes.LLM_USAGE_COMPLETION_TOKENS, completion_tokens
            )
            _set_span_attribute(
                span, SpanAttributes.LLM_USAGE_TOTAL_TOKENS, total_tokens
            )

        _set_chat_response(span, response)
        self._end_span(span, run_id)

    @dont_throw
    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool starts running."""

        if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return

        name = self._get_name_from_callback(serialized, kwargs=kwargs)
        workflow_name = self.get_workflow_name(parent_run_id)
        entity_path = self.get_entity_path(parent_run_id)

        span = self._create_task_span(
            run_id,
            parent_run_id,
            name,
            TraceloopSpanKindValues.TOOL,
            workflow_name,
            name,
            entity_path,
        )
        if should_send_prompts():
            span.set_attribute(
                SpanAttributes.TRACELOOP_ENTITY_INPUT,
                json.dumps(
                    {
                        "input_str": input_str,
                        "tags": tags,
                        "metadata": metadata,
                        "inputs": inputs,
                        "kwargs": kwargs,
                    },
                    cls=CallbackFilteredJSONEncoder,
                ),
            )

    @dont_throw
    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool ends running."""

        if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return

        span = self._get_span(run_id)
        if should_send_prompts():
            span.set_attribute(
                SpanAttributes.TRACELOOP_ENTITY_OUTPUT,
                json.dumps(
                    {"output": output, "kwargs": kwargs},
                    cls=CallbackFilteredJSONEncoder,
                ),
            )
        self._end_span(span, run_id)

    def get_parent_span(self, parent_run_id: Optional[str] = None):
        if parent_run_id is None:
            return None
        return self.spans[parent_run_id]

    def get_workflow_name(self, parent_run_id: str):
        parent_span = self.get_parent_span(parent_run_id)

        if parent_span is None:
            return ""

        return parent_span.workflow_name

    def get_entity_path(self, parent_run_id: str):
        parent_span = self.get_parent_span(parent_run_id)

        if parent_span is None:
            return ""
        elif (
            parent_span.entity_path == ""
            and parent_span.entity_name == parent_span.workflow_name
        ):
            return ""
        elif parent_span.entity_path == "":
            return f"{parent_span.entity_name}"
        else:
            return f"{parent_span.entity_path}.{parent_span.entity_name}"
