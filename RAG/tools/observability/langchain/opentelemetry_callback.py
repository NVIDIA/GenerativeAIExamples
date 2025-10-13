"""Langchain callback handler to generate opentelemetry traces"""

# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Union
from uuid import UUID

import flatdict
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.callbacks.utils import flatten_dict
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document
from langchain_core.env import get_runtime_environment
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from opentelemetry import baggage
from opentelemetry.context import Context, attach, detach
from opentelemetry.trace import Status, StatusCode, Tracer, get_tracer, set_span_in_context
from opentelemetry.trace.span import Span
from tenacity import RetryCallState

logger = logging.getLogger(__name__)

try:
    # psutil is an optional dependency
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False


@dataclass
class SpanWithContext:
    """Object for tracking a span and its context"""

    span: Span
    context: Context
    token: object


def get_system_metrics() -> Dict[str, Union[float, dict]]:
    """Get CPU and other performance metrics."""
    global _PSUTIL_AVAILABLE
    if not _PSUTIL_AVAILABLE:
        return {}
    try:
        process = psutil.Process(os.getpid())
        metrics: Dict[str, Union[float, dict]] = {}

        with process.oneshot():
            mem_info = process.memory_info()
            metrics["thread_count"] = float(process.num_threads())
            metrics["mem"] = {
                "rss": float(mem_info.rss),
            }
            ctx_switches = process.num_ctx_switches()
            cpu_times = process.cpu_times()
            metrics["cpu"] = {
                "time": {"sys": cpu_times.system, "user": cpu_times.user,},
                "ctx_switches": {
                    "voluntary": float(ctx_switches.voluntary),
                    "involuntary": float(ctx_switches.involuntary),
                },
                "percent": process.cpu_percent(),
            }
        return metrics
    except Exception:
        # If psutil is installed but not compatible with the build,
        # we'll just cease further attempts to use it.
        _PSUTIL_AVAILABLE = False
        logger.debug("Skipping system metrics collection, as psutil library is not present")
        return {}


def _create_span_attr(span: Span, span_attrs: Dict[str, Any], span_end: bool = False) -> None:
    allowed_types = (bool, str, bytes, int, float)

    if span_end:
        runtime_info = get_runtime_environment()
        system_metrics = get_system_metrics()
        runtime_info.update({"system_timezone": time.tzname})
        span_attrs.update({"runtime_info": runtime_info, "system_metrics": system_metrics})

    for attr, val in span_attrs.items():
        if not isinstance(val, allowed_types):
            val = str(val)
        span.set_attribute(attr, val)


def _create_span_event(span: Span, event_name: str, span_event: Dict[str, Any]) -> None:
    span.add_event(str(event_name), span_event)


def _create_span_error(span: Span, error: BaseException) -> None:
    span.set_status(Status(StatusCode.ERROR))
    span.record_exception(error)


def _parse_lc_message(message: BaseMessage) -> Dict[str, Any]:
    keys = ["function_call", "tool_calls", "tool_call_id", "name"]
    if isinstance(message, list):
        message = message[0]
    parsed_message = {"text": message.content, "role": message.type}
    parsed_message.update(
        {
            key: str(message.additional_kwargs.get(key))
            for key in keys
            if message.additional_kwargs.get(key) is not None
        }
    )
    return parsed_message


def _parse_lc_messages(messages: Union[List[BaseMessage], Any]) -> List[Dict[str, Any]]:
    return [_parse_lc_message(message) for message in messages]


class OpenTelemetryCallbackHandler(BaseCallbackHandler):
    """Callback Handler that captures Open Telemetry traces"""

    def __init__(self, tracer: Optional[Tracer] = get_tracer(__name__)) -> None:
        """Initialize callback handler."""
        super().__init__()
        self._tracer = tracer
        self._event_map: Dict[UUID, Dict[str, Any]] = {}
        self.llm_tokens = 0

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Union[UUID, None] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM starts."""
        try:
            llm_start_time = datetime.now()
            self.llm_tokens = 0
            class_name = serialized.get("name", serialized.get("id", ["<unknown>"])[-1])
            if not parent_run_id:
                parent_ctx = baggage.set_baggage("context", str(run_id))
            else:
                parent_ctx = self._event_map[parent_run_id]["span"].context
            span = self._tracer.start_span(f"langchain.llm.{class_name}", context=parent_ctx)
            ctx = set_span_in_context(span)
            token = attach(ctx)
            self._event_map[run_id] = {}
            self._event_map[run_id] = {
                "span": SpanWithContext(span=span, context=ctx, token=token),
                "start_time": llm_start_time,
            }

            data = flatdict.FlatDict(kwargs.items(), delimiter=".")
            span_attrs = {
                "run_type": "llm",
                "model_class_name": class_name,
                "prompts": prompts,
                "serialized_info": flatten_dict(serialized),
                "run_id": run_id,
                "parent_run_id": parent_run_id,
            }
            span_attrs.update(data.items())
            _create_span_attr(span, span_attrs)
            _create_span_event(span, "start", {"time": str(llm_start_time)})
        except Exception as e:
            logger.exception(e)

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Union[UUID, None] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when Chat Model starts running."""
        try:
            chat_model_start_time = datetime.now()
            class_name = serialized.get("name", serialized.get("id", ["<unknown>"])[-1])
            if parent_run_id not in self._event_map:
                parent_ctx = baggage.set_baggage("context", str(run_id))
            else:
                parent_ctx = self._event_map[parent_run_id]["span"].context
            span = self._tracer.start_span(f"langchain.chat_model.{class_name}", context=parent_ctx)
            ctx = set_span_in_context(span)
            token = attach(ctx)
            self._event_map[run_id] = {}
            self._event_map[run_id] = {
                "span": SpanWithContext(span=span, context=ctx, token=token),
                "start_time": chat_model_start_time,
            }
            data = flatdict.FlatDict(kwargs.items(), delimiter=".")
            parsed_messages = _parse_lc_messages(messages)
            self.llm_tokens = 0
            span_attrs = {
                "model_class_name": class_name,
                "messages": parsed_messages,
                "serialized_info": flatten_dict(serialized),
                "run_id": run_id,
                "parent_run_id": parent_run_id,
            }
            span_attrs.update(data.items())
            _create_span_attr(span, span_attrs)
            _create_span_event(span, "start", {"time": str(chat_model_start_time)})
        except Exception as e:
            logger.exception(e)

    def on_llm_new_token(self, token: str, chunk, run_id: UUID, **kwargs: Any) -> None:
        """Run when LLM generates a new token."""

        token_time = datetime.now()
        if run_id in self._event_map:
            self.llm_tokens += 1
            if self.llm_tokens == 1:
                self._event_map[run_id]["first_token_time"] = token_time - self._event_map[run_id]["start_time"]

            span = self._event_map[run_id]["span"].span
            span_event = {"token": str(token), "time": str(token_time)}
            if chunk:
                span_event.update({"chunk": str(chunk)})
            _create_span_event(span, "new_token", span_event)
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any,) -> None:
        """Run when LLM ends running."""
        try:
            llm_end_time = datetime.now()
            if run_id in self._event_map:
                self._event_map[run_id]["end_time"] = llm_end_time
                span = self._event_map[run_id]["span"].span
                response_streaming = False
                if self.llm_tokens:
                    response_streaming = True
                else:
                    self._event_map[run_id]["first_token_time"] = llm_end_time - self._event_map[run_id]["start_time"]

                if response.llm_output and "token_usage" in response.llm_output:
                    prompt_tokens = response.llm_output["token_usage"].get("prompt_tokens", 0)
                    total_tokens = response.llm_output["token_usage"].get("total_tokens", 0)
                    completion_tokens = response.llm_output["token_usage"].get("completion_tokens", 0)

                else:
                    prompt_tokens = completion_tokens = total_tokens = "Token data not available"
                    if response_streaming:
                        completion_tokens = self.llm_tokens

                for generation in response.generations[0]:
                    if hasattr(generation, "message"):
                        response_text = _parse_lc_message(generation.message)
                    else:
                        response_text = generation.text

                span_attrs = {
                    "prompt_tokens": prompt_tokens,
                    "total_tokens": total_tokens,
                    "completion_tokens": completion_tokens,
                    "response_streaming": response_streaming,
                    "response": response_text,
                    "first_token_time_ms": self._event_map[run_id]["first_token_time"].total_seconds() * 1000,
                }
                _create_span_attr(span, span_attrs, True)
                _create_span_event(span, "end", {"time": str(llm_end_time)})
                span.set_status(Status(StatusCode.OK))
                span.end()
                detach(self._event_map[run_id]["span"].token)
                del self._event_map[run_id]
            else:
                logger.debug(f"Run with UUID {run_id} not found.")
        except Exception as e:
            logger.exception(e)

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Run when LLM errors."""
        run_id = kwargs.get("run_id")
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span
            _create_span_error(span, error)
            span.end()
            detach(self._event_map[run_id]["span"].token)
            del self._event_map[run_id]
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Union[UUID, None] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain starts running."""
        try:
            chain_start_time = datetime.now()
            class_name = serialized.get("name", serialized.get("id", ["<unknown>"])[-1])
            if not parent_run_id:
                parent_ctx = baggage.set_baggage("context", str(run_id))
            else:
                parent_ctx = self._event_map[parent_run_id]["span"].context
            span = self._tracer.start_span(f"langchain.chain.{class_name}", context=parent_ctx)
            ctx = set_span_in_context(span)
            token = attach(ctx)
            self._event_map[run_id] = {}
            self._event_map[run_id] = {
                "span": SpanWithContext(span=span, context=ctx, token=token),
                "start_time": chain_start_time,
            }
            if isinstance(inputs, dict):
                chain_input = ",".join([f"{k}={v}\n" for k, v in inputs.items()])
            elif isinstance(inputs, list):
                chain_input = ",".join([str(input) for input in inputs])
            else:
                chain_input = str(inputs)

            data = flatdict.FlatDict(kwargs.items(), delimiter=".")

            span_attrs = {
                "run_type": "chain",
                "chain_class_name": class_name,
                "chain_input": chain_input,
                "serialized_info": flatten_dict(serialized),
                "run_id": run_id,
                "parent_run_id": parent_run_id,
            }
            span_attrs.update(data.items())
            _create_span_attr(span, span_attrs)
            _create_span_event(span, "start", {"time": str(chain_start_time)})
        except Exception as e:
            logging.exception(e)

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: UUID, **kwargs: Any) -> None:
        """Run when chain ends running."""
        try:
            chain_end_time = datetime.now()
            if run_id in self._event_map:
                span = self._event_map[run_id]["span"].span
                self._event_map[run_id]["end_time"] = chain_end_time
                if isinstance(outputs, dict):
                    chain_output = ",".join([f"{k}={v}" for k, v in outputs.items()])
                elif isinstance(outputs, list):
                    chain_output = ",".join(map(str, outputs))
                else:
                    chain_output = str(outputs)
                span_attr = {"chain_output": chain_output}
                _create_span_attr(span, span_attr, True)
                _create_span_event(span, "end", {"time": str(chain_end_time)})
                span.set_status(Status(StatusCode.OK))
                span.end()
                detach(self._event_map[run_id]["span"].token)
                del self._event_map[run_id]
            else:
                logger.debug(f"Run with UUID {run_id} not found.")
        except Exception as e:
            logger.exception(e)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """Run when chain errors."""
        run_id = kwargs.get("run_id")
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span
            _create_span_error(span, error)
            span.end()
            detach(self._event_map[run_id]["span"].token)
            del self._event_map[run_id]
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Union[UUID, None] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool starts running."""
        try:
            tool_start_time = datetime.now()
            class_name = serialized.get("name", serialized.get("id", ["<unknown>"])[-1])
            if not parent_run_id:
                parent_ctx = baggage.set_baggage("context", str(run_id))
            else:
                parent_ctx = self._event_map[parent_run_id]["span"].context
            span = self._tracer.start_span(f"langchain.tool.{class_name}", context=parent_ctx)
            ctx = set_span_in_context(span)
            token = attach(ctx)
            self._event_map[run_id] = {}
            self._event_map[run_id] = {
                "span": SpanWithContext(span=span, context=ctx, token=token),
                "start_time": tool_start_time,
            }
            data = flatdict.FlatDict(kwargs.items(), delimiter=".")
            span_attrs = {
                "run_type": "tool",
                "input_str": input_str,
                "serialized_info": flatten_dict(serialized),
                "run_id": run_id,
                "parent_run_id": parent_run_id,
            }
            span_attrs.update(data.items())
            _create_span_attr(span, span_attrs)
            _create_span_event(span, "end", {"time": str(tool_start_time)})
        except Exception as e:
            logger.exception(e)

    def on_tool_end(
        self,
        output: str,
        observation_prefix: Optional[str] = None,
        llm_prefix: Optional[str] = None,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Run when tool ends running."""
        try:
            tool_end_time = datetime.now()
            if run_id in self._event_map:
                span = self._event_map[run_id]["span"].span
                self._event_map[run_id]["end_time"] = tool_end_time
                span_attrs = {}
                if observation_prefix:
                    span_attrs.update({f"{observation_prefix}": output})
                if llm_prefix:
                    span_attrs.update({"llm_prefix": llm_prefix})
                _create_span_attr(span, span_attrs, True)
                _create_span_event(span, "end", {"time": str(tool_end_time)})
                span.set_status(Status(StatusCode.OK))
                span.end()
                detach(self._event_map[run_id]["span"].token)
                del self._event_map[run_id]
            else:
                logger.debug(f"Run with UUID {run_id} not found.")
        except Exception as e:
            logger.exception(e)

    def on_tool_error(self, error: BaseException, *, run_id=UUID, **kwargs: Any) -> None:
        """Run when tool errors."""
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span
            _create_span_error(span, error)
            span.end()
            detach(self._event_map[run_id]["span"].token)
            del self._event_map[run_id]
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_text(self, text: str, *, run_id: UUID, **kwargs: Any) -> None:
        """Run on arbitrary text."""
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span
            _create_span_attr(span, {"text": text})
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_agent_action(self, action: AgentAction, *, run_id: UUID, **kwargs: Any) -> Any:
        """Run on agent action."""
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span
            span_attrs = {
                "agent_tool": action.tool,
                "agent_tool_input": action.tool_input,
                "agent_log": action.log,
            }
            _create_span_attr(span, span_attrs)
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Run on agent end."""
        run_id = kwargs.get("run_id")
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span
            span_attrs = {
                "agent_output": finish.return_values["output"],
                "agent_log": finish.return_values["output"],
            }
            _create_span_attr(span, span_attrs)
            span.set_status(Status(StatusCode.OK))
            span.end()
            detach(self._event_map[run_id]["span"].token)
            del self._event_map[run_id]
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_retriever_start(
        self,
        serialized: Dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when Retriever starts running."""
        try:
            retriever_start_time = datetime.now()
            class_name = serialized.get("name", serialized.get("id", ["<unknown>"])[-1])
            if not parent_run_id:
                parent_ctx = baggage.set_baggage("context", str(run_id))
            else:
                parent_ctx = self._event_map[parent_run_id]["span"].context
            span = self._tracer.start_span(f"langchain.retriever.{class_name}", context=parent_ctx)
            ctx = set_span_in_context(span)
            token = attach(ctx)
            self._event_map[run_id] = {}
            self._event_map[run_id] = {
                "span": SpanWithContext(span=span, context=ctx, token=token),
                "start_time": retriever_start_time,
            }
            data = flatdict.FlatDict(kwargs.items(), delimiter=".")
            span_attrs = {
                "run_type": "retriever",
                "query": query,
                "class_name": class_name,
                "serialized_info": flatten_dict(serialized),
                "run_id": run_id,
                "parent_run_id": parent_run_id,
            }
            span_attrs.update(data.items())
            _create_span_attr(span, span_attrs)
            _create_span_event(span, "start", {"time": str(retriever_start_time)})
        except Exception as e:
            logger.exception(e)

    def on_retriever_end(
        self, documents: Sequence[Document], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        """Run on retriever end."""
        try:
            retriever_end_time = datetime.now()
            if run_id in self._event_map:
                span = self._event_map[run_id]["span"].span
                self._event_map[run_id]["end_time"] = retriever_end_time
                span_attrs = {"documents": documents}
                _create_span_attr(span, span_attrs, True)
                span.set_status(Status(StatusCode.OK))
                _create_span_event(span, "start", {"time": str(retriever_end_time)})
                span.end()
                detach(self._event_map[run_id]["span"].token)
                del self._event_map[run_id]
            else:
                logger.debug(f"Run with UUID {run_id} not found.")
        except Exception as e:
            logger.exception(e)

    def on_retriever_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any,) -> None:
        """Run on retriever error."""
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span
            _create_span_error(span, error)
            span.end()
            detach(self._event_map[run_id]["span"].token)
            del self._event_map[run_id]
        else:
            logger.debug(f"Run with UUID {run_id} not found.")

    def on_retry(self, retry_state: RetryCallState, *, run_id: UUID, **kwargs: Any,) -> Any:
        """Run on a retry event."""
        if run_id in self._event_map:
            span = self._event_map[run_id]["span"].span

            retry_event_info = {
                "slept": retry_state.idle_for,
                "attempt": retry_state.attempt_number,
            }
            if retry_state.outcome is None:
                retry_event_info["outcome"] = "N/A"
            elif retry_state.outcome.failed:
                retry_event_info["outcome"] = "failed"
                exception = retry_state.outcome.exception()
                retry_event_info["exception"] = str(exception)
                retry_event_info["exception_type"] = exception.__class__.__name__
            else:
                retry_event_info["outcome"] = "success"
                retry_event_info["result"] = str(retry_state.outcome.result())

            retry_event_info["time"] = str(datetime.now())
            _create_span_event(span, "retry", retry_event_info)
        else:
            logger.debug(f"Run with UUID {run_id} not found.")
