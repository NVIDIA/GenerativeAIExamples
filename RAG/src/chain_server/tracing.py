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

"""Module for configuring objects used to create OpenTelemetry traces."""

import os
from functools import wraps

from langchain.callbacks.base import BaseCallbackHandler as langchain_base_cb_handler
from llama_index.core.callbacks.simple_llm_handler import SimpleLLMHandler as llama_index_base_cb_handler
from opentelemetry import context, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import get_global_textmap, set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from RAG.tools.observability.langchain import opentelemetry_callback as langchain_otel_cb
from RAG.tools.observability.llamaindex import opentelemetry_callback as llama_index_otel_cb

# Configure tracer used by the Chain Server to create spans
resource = Resource.create({SERVICE_NAME: "chain-server"})
provider = TracerProvider(resource=resource)
if os.environ.get("ENABLE_TRACING") == "true":
    processor = SimpleSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("chain-server")

if os.environ.get("ENABLE_TRACING") == "true":
    # Configure Propagator used for processing trace context received by the Chain Server
    propagator = TraceContextTextMapPropagator()

    # Configure Langchain OpenTelemetry callback handler
    langchain_cb_handler = langchain_otel_cb.OpenTelemetryCallbackHandler(tracer)

    # Configure LlamaIndex OpenTelemetry callback handler
    llama_index_cb_handler = llama_index_otel_cb.OpenTelemetryCallbackHandler(tracer)

else:
    propagator = CompositePropagator([])  # No-op propagator
    langchain_cb_handler = langchain_base_cb_handler()
    llama_index_cb_handler = llama_index_base_cb_handler()

set_global_textmap(propagator)

# Wrapper Function to perform LlamaIndex instrumentation
def llamaindex_instrumentation_wrapper(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        prompt = kwargs.get("prompt")
        ctx = get_global_textmap().extract(request.headers)
        if ctx is not None:
            context.attach(ctx)
        result = func(*args, **kwargs)
        return await result

    return wrapper


# Wrapper Function to perform Langchain instrumentation
def langchain_instrumentation_method_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(langchain_cb_handler, *args, **kwargs)
        return result

    return wrapper


# Wrapper Class to perform Langchain instrumentation
def langchain_instrumentation_class_wrapper(func):
    class WrapperClass(func):
        def __init__(self, *args, **kwargs):
            self.cb_handler = langchain_cb_handler
            super().__init__(*args, **kwargs)

    return WrapperClass


def inject_context(ctx):
    carrier = {}
    get_global_textmap().inject(carrier, context=ctx)
    return carrier


# Wrapper Function to perform instrumentation
def instrumentation_wrapper(func):
    def wrapper(self, *args, **kwargs):
        span_name = func.__name__
        span = tracer.start_span(span_name)
        span_ctx = trace.set_span_in_context(span)
        carrier = inject_context(span_ctx)
        [span.set_attribute(f"{kw}", kwargs[kw]) for kw in kwargs]
        result = func(self, carrier, *args, **kwargs)
        span.end()
        return result

    return wrapper
