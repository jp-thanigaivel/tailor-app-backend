import logging
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace import SpanKind, StatusCode, Status, INVALID_SPAN, Tracer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation import tracecontext

from app.core.config import OTELConfig, OTELConsoleExporterConfig, OTELGrpcExporterConfig

logger = logging.getLogger(__name__)

LIB_VERSION = "1.0"
LIB_SCHEMA_URL = "https://opentelemetry.io/schemas/1.21.0"

class TelemetryManager:
    _tracer: Optional[Tracer] = None
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def initialize(cls, otel_config: OTELConfig):
        if not otel_config.is_enabled:
            logger.info("Telemetry is disabled")
            return

        with cls._lock:
            if cls._initialized:
                return

            resource = Resource.create(attributes={
                "service.name": otel_config.app_name,
                "deployment.environment": otel_config.environment
            })

            exporter_config = otel_config.otel_exporter
            if isinstance(exporter_config, OTELConsoleExporterConfig):
                exporter = ConsoleSpanExporter()
            elif isinstance(exporter_config, OTELGrpcExporterConfig):
                exporter = OTLPSpanExporter(
                    endpoint=str(exporter_config.exporter_url),
                    insecure=exporter_config.insecure
                )
            else:
                logger.warning("Unknown telemetry exporter config, skipping initialization")
                return

            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(
                exporter, 
                export_timeout_millis=otel_config.otel_exporter_timeout_millis
            )
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            
            cls._tracer = trace.get_tracer(
                instrumenting_module_name=otel_config.app_name,
                instrumenting_library_version=LIB_VERSION,
                schema_url=LIB_SCHEMA_URL
            )
            cls._initialized = True
            logger.info("Telemetry initialized successfully")

    @classmethod
    def get_tracer(cls) -> Optional[Tracer]:
        return cls._tracer

@contextmanager
def start_span(
    span_name: str, 
    kind: SpanKind = SpanKind.INTERNAL, 
    attributes: Optional[Dict[str, Any]] = None,
    parent_context: Optional[Context] = None
):
    tracer = TelemetryManager.get_tracer()
    if tracer is None:
        yield INVALID_SPAN
        return

    with tracer.start_as_current_span(
        name=span_name, 
        context=parent_context, 
        kind=kind, 
        attributes=attributes
    ) as span:
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

def inject_trace_headers(headers: Dict[str, str]):
    trace_context = trace.get_current_span().get_span_context()
    if trace_context and trace_context.is_valid:
        traceparent_header = "00-{:032x}-{:016x}-{:02x}".format(
            trace_context.trace_id,
            trace_context.span_id,
            trace_context.trace_flags
        )
        headers["traceparent"] = traceparent_header
    return headers

def extract_trace_context(headers: Dict[str, str]) -> Context:
    return tracecontext.TraceContextTextMapPropagator().extract(carrier=headers)
