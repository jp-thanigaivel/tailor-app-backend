import logging
import threading
from contextlib import contextmanager

from fastapi import Request
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, RandomIdGenerator
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace import SpanKind, Tracer, Status, StatusCode, INVALID_SPAN
from opentelemetry.trace.propagation import tracecontext
from starlette import status

from app.core.config import OTELConfig, OTELConsoleExporterConfig, OTELGrpcExporterConfig
from app.observability.app_observability_utils import AppTraceUtil, HTTP_TRACE_HEADER_KEY
from app.utils.app_constant import STATUS_TYPE_ERROR
from app.core.exceptions import InvalidOTelExporterException

logger = logging.getLogger(__name__)

LIB_VERSION = "1.0"
LIB_SCHEMA_URL = "https://opentelemetry.io/schemas/1.21.0"


def get_trace_provider(otel_config: OTELConfig) -> TracerProvider:
    otel_exporter = otel_config.otel_exporter
    otel_trace_exporter = None
    if isinstance(otel_exporter, OTELConsoleExporterConfig):
        otel_trace_exporter = _get_console_span_exporter(otel_exporter)
    elif isinstance(otel_exporter, OTELGrpcExporterConfig):
        otel_trace_exporter = _get_grpc_span_exporter(otel_exporter)
    else:
        raise InvalidOTelExporterException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                           "Invalid Trace Exporter")

    resource = _create_resource(otel_config)
    trace_processor = BatchSpanProcessor(span_exporter=otel_trace_exporter,
                                         export_timeout_millis=otel_config.otel_exporter_timeout_millis)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(trace_processor)
    return tracer_provider


class AppTracer:
    _instance = None
    _is_initialized = False
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._is_initialized:
            with cls._lock:
                if not cls._is_initialized:
                    cls._instance = super().__new__(cls)
                    cls._is_initialized = True
        return cls._instance

    def __init__(self, otel_config: OTELConfig):
        self.__create_tracer(otel_config)
        self.random_id_gen = RandomIdGenerator()

    def __create_tracer(self, otel_config: OTELConfig):
        self.tracer = trace.get_tracer(instrumenting_module_name=otel_config.app_name,
                                       instrumenting_library_version=LIB_VERSION,
                                       tracer_provider=get_trace_provider(otel_config),
                                       schema_url=LIB_SCHEMA_URL)

    async def __call__(self, request: Request, call_next):
        logger.info("start capturing tracer")
        http_method = str(request.method)
        http_url = str(request.url)
        request_headers = request.headers
        http_span_name = f"{http_method} : {http_url}"
        parent_trace_id = AppTraceUtil.get_trace_context_text_map_propagator(request_headers)
        parent_span_id = None
        with start_app_tracing(span_name=http_span_name, parent_trace_id=parent_trace_id,
                               parent_span_id=parent_span_id) as span:
            response = await call_next(request)
            # Set Status
            http_status = int(response.status_code)
            status_code = StatusCode.ERROR if http_status > 299 else StatusCode.OK
            status_desc = None
            if status_code == StatusCode.ERROR:
                status_type = "SERVER ERROR" if http_status > 499 else "CLIENT ERROR"
                status_desc = f"{str(http_status)}:{status_type}"
            span.set_status(
                Status(
                    status_code=status_code,
                    description=status_desc
                )
            )
            return response

    @classmethod
    def get_tracer(cls):
        # In case of disabled
        if not cls._is_initialized:
            return None
        """
        if not cls._is_initialized:
            raise UnInitializedException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                         "App Tracer Not Initialized")
        """
        return cls._instance.tracer

    @classmethod
    def get_trace_header(cls):
        trace_context = trace.get_current_span().get_span_context()
        headers = None
        if trace_context:
            """
            traceparent_header = "{}-{}-{}-{}".format(
                format(trace_context.trace_flags, '02x'),
                trace_context.trace_id,
                trace_context.span_id,
                format(trace_context.trace_flags, '02x')
            )
            """
            traceparent_header = "{}-{}-{}-{}".format(
                AppTraceUtil.get_hexadecimal_value_trace_version(),
                AppTraceUtil.get_hexadecimal_value_trace_id(trace_context.trace_id),
                AppTraceUtil.get_hexadecimal_value_span_id(trace_context.span_id),
                AppTraceUtil.get_hexadecimal_value_trace_flag()
            )

            headers = {
                HTTP_TRACE_HEADER_KEY: traceparent_header,
            }
        return headers


@contextmanager
def start_app_tracing(span_name: str, span_kind: SpanKind = SpanKind.INTERNAL, attributes: dict = None,
                      parent_trace_id: int = None, parent_span_id: int = None, parent_span_is_remote: bool = False,
                      parent_trace_header: dict = None):
    logger.info(f"In Start App Span {span_name}")
    tracer: Tracer = AppTracer.get_tracer()
    if tracer is None:
        logger.info("App Tracer is not initialized. Ignoring span")
        yield INVALID_SPAN
        return

    logger.info(f"Creating App Span {span_name}")
    parent_span_context = None
    if parent_trace_id and parent_span_id:
        logger.info(f"Received parent span id {parent_span_id} and parent trace id {parent_trace_id}")
        span_context = trace.SpanContext(
            trace_id=parent_trace_id,
            span_id=parent_span_id,
            is_remote=True,
            trace_flags=trace.TraceFlags(int("1", 16))
        )
        """
        paa = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        trace_context = tracecontext.TraceContextTextMapPropagator().extract(
            carrier={'traceparent': paa},
            )
        """
        trace_context = trace.set_span_in_context(
            trace.NonRecordingSpan(span_context), Context()
        )
        parent_span_context = trace_context
    if parent_trace_header and parent_trace_header.get(HTTP_TRACE_HEADER_KEY, None):
        trace_context = tracecontext.TraceContextTextMapPropagator().extract(
            carrier={HTTP_TRACE_HEADER_KEY: parent_trace_header.get(HTTP_TRACE_HEADER_KEY)},
        )
        parent_span_context = trace_context
    else:
        logger.info("No Span found")

    with tracer.start_as_current_span(name=span_name, context=parent_span_context, kind=span_kind,
                                      attributes=attributes) as span:
        logger.info(f"Starting App Span Context {span_name}")
        yield span
        logger.info(f"Existing App Span Context {span_name}")


"""
WARNING : BELOW ARE THE INTERNAL METHODS SHOULD NOT USED OUTSIDE THIS FILE
"""


def _create_resource(otel_config: OTELConfig) -> Resource:
    return Resource.create(attributes={"service.name": otel_config.app_name,
                                       "deployment.environment": otel_config.environment})


def _get_console_span_exporter(otel_exporter_config: OTELConsoleExporterConfig):
    return ConsoleSpanExporter()


def _get_grpc_span_exporter(otel_exporter_config: OTELGrpcExporterConfig):
    return OTLPSpanExporter(endpoint=otel_exporter_config.exporter_url,
                            insecure=otel_exporter_config.insecure)
