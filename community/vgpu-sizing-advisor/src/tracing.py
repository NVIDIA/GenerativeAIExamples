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

"""Module to enable Observervability and Tracing instrumentation"""

from typing import Any
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.processor.baggage import BaggageSpanProcessor, ALLOW_ALL_BAGGAGE_KEYS
from .observability.langchain_instrumentor import LangchainInstrumentor
from .observability.otel_metrics import OtelMetrics
from opentelemetry.instrumentation.milvus import MilvusInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

def _fastapi_server_request_hook(span: Span, scope: dict[str, Any]):
    """Utility function"""

    if span and span.is_recording():
        for k, v in scope.get("headers"):
            if k == b"x-benchmark-id":
                span.set_attribute("x-benchmark-id", v)


def instrument(app: FastAPI, settings):
    """Function to enable OTLP export and instrumentation for traces and metrics"""

    otel_metrics = None
    if settings.tracing.enabled:
        resource = Resource(attributes={"service.name": "rag"})

        # Observability Metrics
        exporter_grpc = None
        if settings.tracing.otlp_grpc_endpoint != "":
            logger.debug(
                f"configuring otlp grpc exporter {settings.tracing.otlp_grpc_endpoint}"
            )
            exporter_grpc = OTLPMetricExporter(
                endpoint=settings.tracing.otlp_grpc_endpoint, insecure=True
            )
        else:
            logger.debug(f"configuring console exporter {settings.tracing}")
            exporter_grpc = ConsoleSpanExporter()
        otlp_reader = PeriodicExportingMetricReader(exporter_grpc)
        prometheus_reader = PrometheusMetricReader()
        provider = MeterProvider(
            resource=resource, metric_readers=[otlp_reader, prometheus_reader]
        )
        metrics.set_meter_provider(provider)
        otel_metrics = OtelMetrics(service_name="rag")

        # Oberservability Tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        exporter_http = None
        if settings.tracing.otlp_http_endpoint != "":
            logger.debug(
                f"configuring otlp http exporter {settings.tracing.otlp_http_endpoint}"
            )
            exporter_http = OTLPSpanExporter(
                endpoint=settings.tracing.otlp_http_endpoint
            )
        else:
            logger.debug(f"configuring console exporter {settings.tracing}")
            exporter_http = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(exporter_http)
        trace.get_tracer_provider().add_span_processor(
            BaggageSpanProcessor(ALLOW_ALL_BAGGAGE_KEYS)
        )
        trace.get_tracer_provider().add_span_processor(span_processor)
        LangchainInstrumentor().instrument(tracer_provider=trace.get_tracer_provider(), metrics=otel_metrics)
        MilvusInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        FastAPIInstrumentor().instrument_app(
            app,
            tracer_provider=trace.get_tracer_provider(),
            server_request_hook=_fastapi_server_request_hook,
        )
    return otel_metrics