import logging
import threading

from fastapi import Request, Response
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from starlette import status

from app.core.config import OTELConfig, OTELConsoleExporterConfig, OTELGrpcExporterConfig
from app.observability.app_observability_utils import AppMetricName, AppMetricUnit, _active_requests_count_attrs, \
    AppMetricAttribute, _duration_attrs
from app.utils.app_constant import RESPONSE_HEADER_RESPONSE_LENGTH_KEY, \
    RESPONSE_HEADER_REQUEST_LENGTH_KEY, STATUS_TYPE_ERROR
from app.core.exceptions import InvalidOTelExporterException
from app.utils.common_functions import DateUtils

logger = logging.getLogger(__name__)

LIB_VERSION = "1.0"
LIB_SCHEMA_URL = "https://opentelemetry.io/schemas/1.21.0"


def get_metric_provider(otel_config: OTELConfig) -> MeterProvider:
    otel_exporter = otel_config.otel_exporter
    otel_metric_exporter = None
    if isinstance(otel_exporter, OTELConsoleExporterConfig):
        otel_metric_exporter = _get_console_metric_exporter(otel_exporter)
    elif isinstance(otel_exporter, OTELGrpcExporterConfig):
        otel_metric_exporter = _get_grpc_metric_exporter(otel_exporter)
    else:
        raise InvalidOTelExporterException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                           "Invalid Metric Exporter")

    resource = _create_resource(otel_config)
    metric_readers = PeriodicExportingMetricReader(otel_metric_exporter,
                                                   export_interval_millis=otel_config.otel_exporter_interval_millis,
                                                   export_timeout_millis=otel_config.otel_exporter_timeout_millis)
    metrics_provider = MeterProvider(metric_readers=[metric_readers], resource=resource)
    return metrics_provider


class AppMetrics:
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
        self.__create_metrics(otel_config)

    def __create_metrics(self, otel_config: OTELConfig):
        meter_provider = get_metric_provider(otel_config)
        self.meter = metrics.get_meter(name=otel_config.app_name + ".meter", version=LIB_VERSION,
                                       meter_provider=meter_provider,
                                       schema_url=LIB_SCHEMA_URL)
        self.active_requests_counter = self.meter.create_up_down_counter(
            name=AppMetricName.ACTIVE_REQUEST.value,
            unit=AppMetricUnit.REQUEST.value,
            description="Number of active HTTP server requests & "
                        "measures the number of concurrent HTTP requests that are currently in-flight",
        )
        self.http_server_duration = self.meter.create_histogram(
            name=AppMetricName.REQUEST_DURATION.value,
            unit=AppMetricUnit.MILLI_SECONDS.value,
            description="Duration of HTTP server requests",
        )
        """
        self.http_request_size = self.meter.create_histogram(
            name=AppMetricName.REQUEST_SIZE.value,
            unit=AppMetricUnit.BYTES.value,
            description="Size of HTTP server request bodies.",
        )
        """

        self.http_response_size = self.meter.create_histogram(
            name=AppMetricName.RESPONSE_SIZE.value,
            unit=AppMetricUnit.BYTES.value,
            description="Size of HTTP server response bodies",
        )

        """
        self.http_request_count = self.meter.create_counter(
            name=AppMetricName.REQUEST_COUNT.value,
            unit=AppMetricUnit.ONE.value,
            description="Number of HTTP Request Count",
        )
        """

    async def __call__(self, request: Request, call_next):
        try:
            logger.info("start capturing metrics")
            start_time = DateUtils.current_milli_time()
            default_request_attribute = _get_request_metric_attribute(request)
            active_requests_attribute = _get_active_request_count_attrs(default_request_attribute)
            self.active_requests_counter.add(1, active_requests_attribute)
            # process the request and get the response
            response = await call_next(request)
        except Exception as exp:
            logger.error("Exception occurred")
            raise exp
        finally:
            if response:
                logger.info("start exporting metrics")
                default_response_attribute = _get_response_metric_attribute(response)
                default_attribute = {**default_request_attribute, **default_response_attribute}
                # default_request_attribute.update(default_response_attribute)
                duration_attribute = _get_duration_attrs(default_attribute)

                response_length = 0
                if response and response.headers:
                    response_length = int(response.headers.get(RESPONSE_HEADER_RESPONSE_LENGTH_KEY, 0))
                end_time = DateUtils.current_milli_time()
                response_time = end_time - start_time

                self.active_requests_counter.add(-1, active_requests_attribute)
                self.http_server_duration.record(response_time, duration_attribute)
                self.http_response_size.record(response_length, duration_attribute)
                # self.http_request_count.add(1, default_request_attribute)
                logger.info("end exporting metrics")
        return response


"""
WARNING : BELOW ARE THE INTERNAL METHODS SHOULD NOT USED OUTSIDE THIS FILE
"""


def _get_active_request_count_attrs(default_attribute):
    active_requests_count_attrs = {
        key: default_attribute[key]
        for key in _active_requests_count_attrs.intersection(default_attribute.keys())
    }
    return active_requests_count_attrs


def _get_duration_attrs(default_attribute):
    duration_attrs = {
        key: default_attribute[key]
        for key in _duration_attrs.intersection(default_attribute.keys())
    }
    return duration_attrs


def _get_request_metric_attribute(request: Request):
    # From request
    client_ip = str(request.client.host) if request.client.host else "-"
    client_port = str(request.client.port) if request.client.host else "-"
    http_method = str(request.method)
    http_url = str(request.url)
    request_length = request.headers.get(RESPONSE_HEADER_REQUEST_LENGTH_KEY, 0)
    http_protocol = request.scope.get("scheme", "http")
    http_protocol_version = request.scope.get("http_version", "1.1")
    server = request.scope.get("server") or ["0.0.0.0", 80]
    port = int(server[1])
    server_host = server[0] + (":" + str(port) if str(port) != "80" else "")
    full_path = request.scope.get("root_path", "") + request.scope.get("path", "")
    full_http_url = request.scope.get("scheme", "http") + "://" + server_host + full_path

    default_attribute = {
        AppMetricAttribute.HTTP_METHOD.value: http_method,
        AppMetricAttribute.HTTP_ROUTE.value: full_path,
        AppMetricAttribute.HTTP_PROTOCOL.value: http_protocol,
        AppMetricAttribute.HTTP_PROTOCOL_VERSION.value: http_protocol_version,
        AppMetricAttribute.HTTP_SERVER_ADDRESS.value: server_host,
        AppMetricAttribute.HTTP_SERVER_PORT.value: port,
        AppMetricAttribute.HTTP_URL_SCHEMA.value: http_protocol
    }
    return default_attribute


def _get_response_metric_attribute(response: Response) -> dict:
    """

    :rtype: dict
    """
    # From response
    http_status = int(response.status_code)
    default_attribute = {
        AppMetricAttribute.HTTP_STATUS_CODE.value: http_status
    }
    return default_attribute


def _create_resource(otel_config: OTELConfig) -> Resource:
    return Resource.create(attributes={"service.name": otel_config.app_name,
                                       "deployment.environment": otel_config.environment})


def _get_console_metric_exporter(otel_exporter_config: OTELConsoleExporterConfig):
    return ConsoleMetricExporter()


def _get_grpc_metric_exporter(otel_exporter_config: OTELGrpcExporterConfig):
    return OTLPMetricExporter(endpoint=otel_exporter_config.exporter_url,
                              insecure=otel_exporter_config.insecure)
