"""OpenTelemetry tracing stub (OTEL) — local-first, no external collector required."""
import os
from typing import Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    _otel_available = True
except ImportError:
    _otel_available = False

def setup_tracing(app=None, service_name: str = "purple-api"):
    if not _otel_available:
        return None
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    # Console for local dev
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    # OTLP if configured
    if endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except Exception:
            pass
    trace.set_tracer_provider(provider)
    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(app)
            SQLAlchemyInstrumentor().instrument()
            RedisInstrumentor().instrument()
        except Exception:
            pass
    return trace.get_tracer(service_name)

def get_tracer(name: str = "purple"):
    if _otel_available:
        return trace.get_tracer(name)
    # No-op tracer
    class _NoopSpan:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def set_attribute(self, *a, **kw): pass
        def record_exception(self, *a, **kw): pass
    class _NoopTracer:
        def start_as_current_span(self, *a, **kw): return _NoopSpan()
    return _NoopTracer()
