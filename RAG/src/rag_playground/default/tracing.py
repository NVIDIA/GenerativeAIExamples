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

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import get_global_textmap, set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Configure tracer used by the Frontend to create spans
resource = Resource.create({SERVICE_NAME: "frontend"})
provider = TracerProvider(resource=resource)
if os.environ.get("ENABLE_TRACING") == "true":
    processor = SimpleSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("frontend")

# Configure Propagator used for processing trace context received by the Frontend
if os.environ.get("ENABLE_TRACING") == "true":
    propagator = TraceContextTextMapPropagator()
else:
    propagator = CompositePropagator([])  # No-op propagator

set_global_textmap(propagator)

# Include the contents of carrier in an HTTP header
# to propagate the span context into another microservice
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


# Wrapper function for the streaming predict call
def predict_instrumentation_wrapper(func):
    def wrapper(self, *args, **kwargs):
        span_name = func.__name__
        span = tracer.start_span(span_name)
        span_ctx = trace.set_span_in_context(span)
        [span.set_attribute(f"{kw}", kwargs[kw]) for kw in kwargs]
        carrier = inject_context(span_ctx)
        constructed_response = ""
        for chunk in func(self, carrier, *args, **kwargs):
            if chunk:
                constructed_response += chunk
            yield chunk
        span.set_attribute("response", constructed_response)
        span.end()

    return wrapper
