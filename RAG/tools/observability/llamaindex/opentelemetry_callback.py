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

import threading
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from llama_index.core.callbacks.base_handler import BaseCallbackHandler
from llama_index.core.callbacks.schema import BASE_TRACE_EVENT, CBEventType, EventPayload
from llama_index.core.callbacks.token_counting import get_llm_token_counts
from llama_index.core.utilities.token_counting import TokenCounter
from llama_index.core.utils import get_tokenizer
from opentelemetry.context import Context, attach, detach
from opentelemetry.trace import Status, StatusCode, Tracer, get_tracer, set_span_in_context
from opentelemetry.trace.span import Span

global_root_trace = ContextVar("trace", default=None)


@dataclass
class SpanWithContext:
    """Object for tracking a span, its context, and its context token"""

    span: Span
    context: Context
    token: object

    def __init__(self, span: Span, context: Context, token: object, thread_identity):
        self.span = span
        self.context = context
        self.token = token
        self.thread_identity = thread_identity


class OpenTelemetryCallbackHandler(BaseCallbackHandler):
    """Callback handler for creating OpenTelemetry traces from llamaindex traces and events."""

    def __init__(
        self, tracer: Optional[Tracer] = get_tracer(__name__), tokenizer: Optional[Callable[[str], List]] = None,
    ) -> None:
        """Initializes the OpenTelemetryCallbackHandler.

        Args:
            tracer: Optional[Tracer]: A OpenTelemetry tracer used to create OpenTelemetry spans
        """
        super().__init__(event_starts_to_ignore=[], event_ends_to_ignore=[])
        self._tracer = tracer
        self._event_map: Dict[str, SpanWithContext] = {}
        self.tokenizer = tokenizer or get_tokenizer()
        self._token_counter = TokenCounter(tokenizer=self.tokenizer)

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        pass

    def end_trace(self, trace_id: Optional[str] = None, trace_map: Optional[Dict[str, List[str]]] = None,) -> None:
        pass

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        parent_ctx = None
        # Case where the parent of this event is another event
        if parent_id in self._event_map:
            parent_ctx = self._event_map[parent_id].context
        # Case where the parent of this event is the root trace, and the root trace exists
        elif parent_id is BASE_TRACE_EVENT and global_root_trace.get() is not None:
            parent_ctx = global_root_trace.get().context

        span_prefix = "llamaindex.event."
        span = self._tracer.start_span(span_prefix + event_type.value, context=parent_ctx)
        ctx = set_span_in_context(span)
        token = attach(ctx)
        self._event_map[event_id] = SpanWithContext(
            span=span, context=ctx, token=token, thread_identity=threading.get_ident()
        )

        span.set_attribute("event_id", event_id)
        if payload is not None:
            if event_type is CBEventType.QUERY:
                span.set_attribute("query.text", payload[EventPayload.QUERY_STR])
            elif event_type is CBEventType.RETRIEVE:
                pass
            elif event_type is CBEventType.EMBEDDING:
                span.set_attribute("embedding.model", payload[EventPayload.SERIALIZED]['model_name'])
                span.set_attribute("embedding.batch_size", payload[EventPayload.SERIALIZED]['embed_batch_size'])
                span.set_attribute("embedding.class_name", payload[EventPayload.SERIALIZED]['class_name'])
            elif event_type is CBEventType.SYNTHESIZE:
                span.set_attribute("synthesize.query_text", payload[EventPayload.QUERY_STR])
            elif event_type is CBEventType.CHUNKING:
                for i, chunk in enumerate(payload[EventPayload.CHUNKS]):
                    span.set_attribute(f"chunk.{i}", chunk)
            elif event_type is CBEventType.TEMPLATING:
                if payload[EventPayload.QUERY_WRAPPER_PROMPT]:
                    span.set_attribute("query_wrapper_prompt", payload[EventPayload.QUERY_WRAPPER_PROMPT])
                if payload[EventPayload.SYSTEM_PROMPT]:
                    span.set_attribute("system_prompt", payload[EventPayload.SYSTEM_PROMPT])
                if payload[EventPayload.TEMPLATE]:
                    span.set_attribute("template", payload[EventPayload.TEMPLATE])
                if payload[EventPayload.TEMPLATE_VARS]:
                    for key, var in payload[EventPayload.TEMPLATE_VARS].items():
                        span.set_attribute(f"template_variables.{key}", var)
            elif event_type is CBEventType.LLM:
                span.set_attribute("llm.class_name", payload[EventPayload.SERIALIZED]['class_name'])
                if EventPayload.PROMPT in payload:
                    span.set_attribute("llm.formatted_prompt", payload[EventPayload.PROMPT])
                else:
                    span.set_attribute("llm.messages", str(payload[EventPayload.MESSAGES]))
                span.set_attribute("llm.additional_kwargs", str(payload[EventPayload.ADDITIONAL_KWARGS]))
            elif event_type is CBEventType.NODE_PARSING:
                span.set_attribute("node_parsing.num_documents", len(payload[EventPayload.DOCUMENTS]))
            elif event_type is CBEventType.EXCEPTION:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(payload[EventPayload.EXCEPTION])
        return event_id

    def on_event_end(
        self, event_type: CBEventType, payload: Optional[Dict[str, Any]] = None, event_id: str = "", **kwargs: Any,
    ) -> None:
        if event_id in self._event_map:
            span = self._event_map[event_id].span
            span.set_attribute("event_id", event_id)
            if payload is not None:
                if CBEventType.EXCEPTION in payload:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(payload[EventPayload.EXCEPTION])
                elif event_type is CBEventType.QUERY:
                    pass
                elif event_type is CBEventType.RETRIEVE:
                    for i, node_with_score in enumerate(payload[EventPayload.NODES]):
                        node = node_with_score.node
                        score = node_with_score.score
                        span.set_attribute(f"query.node.{i}.id", node.hash)
                        span.set_attribute(f"query.node.{i}.score", score)
                        span.set_attribute(f"query.node.{i}.text", node.text)
                elif event_type is CBEventType.EMBEDDING:
                    texts = payload.get(EventPayload.CHUNKS, [])
                    vectors = payload.get(EventPayload.EMBEDDINGS, [])
                    total_chunk_tokens = 0
                    for text, vector in zip(texts, vectors):
                        span.set_attribute(f"embedding_text_{texts.index(text)}", text)
                        span.set_attribute(f"embedding_vector_{vectors.index(vector)}", vector)
                        total_chunk_tokens += self._token_counter.get_string_tokens(text)
                    span.set_attribute(f"embedding_token_usage", total_chunk_tokens)
                elif event_type is CBEventType.SYNTHESIZE:
                    pass
                elif event_type is CBEventType.CHUNKING:
                    pass
                elif event_type is CBEventType.TEMPLATING:
                    pass
                elif event_type is CBEventType.LLM:
                    span.set_attribute(
                        "response.text",
                        str(payload.get(EventPayload.RESPONSE, "")) or str(payload.get(EventPayload.COMPLETION, "")),
                    )
                    token_counts = get_llm_token_counts(self._token_counter, payload, event_id)
                    span.set_attribute("llm_prompt.token_usage", token_counts.prompt_token_count)
                    span.set_attribute("llm_completion.token_usage", token_counts.completion_token_count)
                    span.set_attribute("total_tokens_used", token_counts.total_token_count)
                elif event_type is CBEventType.NODE_PARSING:
                    span.set_attribute("node_parsing.num_nodes", len(payload[EventPayload.NODES]))

            if self._event_map[event_id].thread_identity == threading.get_ident():
                detach(self._event_map[event_id].token)
            self._event_map.pop(event_id, None)
            span.end()
