import re
from enum import Enum

from opentelemetry.sdk.trace import RandomIdGenerator
from opentelemetry.trace import SpanKind

HTTP_TRACE_HEADER_REGEX = re.compile(
    r"^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})(-.*)?[ \t]*$"
)
HTTP_TRACE_HEADER_KEY = "traceparent"


class AppMetricName(Enum):
    # HTTP SERVER
    ACTIVE_REQUEST = "http.server.active_requests"
    REQUEST_DURATION = "http.server.duration"
    # REQUEST_SIZE = "http.server.request.size"
    RESPONSE_SIZE = "http.server.response.size"
    # REQUEST_COUNT = "http.server.requests"

    # HTTP CLIENT
    "http.client.duration"
    "http.client.request.size"
    "http.client.response.size"

    # Process
    "process.runtime.jvm.memory.init"  # UpDownCounter
    "process.runtime.jvm.system.cpu.utilization"  # gauge
    "process.runtime.jvm.buffer.usage"  # UpDownCounter

    # DB
    "db.client.connections.usage"  # UpDownCounter


class AppMetricUnit(Enum):
    MILLI_SECONDS = "ms"
    BYTES = "By"
    REQUEST = "requests"
    ONE = "1"


class AppMetricAttribute(Enum):
    HTTP_APP_ERROR = "error.type"
    HTTP_METHOD = "http.request.method"
    HTTP_STATUS_CODE = "http.response.status_code"
    HTTP_ROUTE = "http.route"
    HTTP_PROTOCOL = "network.protocol.name"
    HTTP_PROTOCOL_VERSION = "network.protocol.version"
    HTTP_SERVER_ADDRESS = "server.address"
    HTTP_SERVER_PORT = "server.port"
    HTTP_URL_SCHEMA = "url.scheme"


_duration_attrs = {
    AppMetricAttribute.HTTP_APP_ERROR.value,
    AppMetricAttribute.HTTP_METHOD.value,
    AppMetricAttribute.HTTP_STATUS_CODE.value,
    AppMetricAttribute.HTTP_ROUTE.value,
    AppMetricAttribute.HTTP_PROTOCOL.value,
    AppMetricAttribute.HTTP_PROTOCOL_VERSION.value,
    AppMetricAttribute.HTTP_SERVER_ADDRESS.value,
    AppMetricAttribute.HTTP_SERVER_PORT.value,
    AppMetricAttribute.HTTP_URL_SCHEMA.value
}

_active_requests_count_attrs = {
    AppMetricAttribute.HTTP_METHOD.value,
    AppMetricAttribute.HTTP_SERVER_ADDRESS.value,
    AppMetricAttribute.HTTP_SERVER_PORT.value,
    AppMetricAttribute.HTTP_URL_SCHEMA.value
}


class AppTraceUtil:
    _random_generator: RandomIdGenerator = RandomIdGenerator()

    @classmethod
    def get_hexadecimal_value(cls, span_id: int, bit: str = "032x") -> str:
        return format(span_id, bit)

    @classmethod
    def get_hexadecimal_value_trace_version(cls, trace_version: int = 00) -> str:
        return format(trace_version, '02x')

    @classmethod
    def get_hexadecimal_value_trace_id(cls, trace_id: int) -> str:
        return format(trace_id, '032x')

    @classmethod
    def get_hexadecimal_value_span_id(cls, span_id: int) -> str:
        return format(span_id, '016x')

    @classmethod
    def get_hexadecimal_value_trace_flag(cls, trace_flag: int = 1) -> str:
        return format(trace_flag, '02x')

    @classmethod
    def get_trace_id(cls) -> int:
        return cls._random_generator.generate_trace_id()

    @classmethod
    def get_span_id(cls) -> int:
        return cls._random_generator.generate_span_id()

    @classmethod
    def get_trace_context_text_map_propagator(cls, http_header: dict):
        trace_header = http_header.get(HTTP_TRACE_HEADER_KEY, None)
        if trace_header:
            match = HTTP_TRACE_HEADER_REGEX.match(http_header)
            if match:
                version, trace_id, span_id, trace_flags = match.groups()
                """
                return {
                    "version": version,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "trace_flags": trace_flags,
                }
                """
                return trace_id, span_id
            return None


class AppTraceSpanEnum(Enum):
    SPAN_NAME_DB_OPERATION_INSERT = "INSERT"
    SPAN_NAME_DB_OPERATION_SELECT = "SELECT"
    SPAN_NAME_DB_OPERATION_UPSERT = "UPSERT"
    SPAN_NAME_DB_OPERATION_REPLACE = "REPLACE"
    SPAN_NAME_DB_OPERATION_DELETE = "DELETE"

    SPAN_NAME_DB_ATTRIBUTE_COLLECTION_NAME = "db.mongodb.collection"
    SPAN_NAME_DB_ATTRIBUTE_SYSTEM = "db.system"
    SPAN_NAME_DB_ATTRIBUTE_NAME = "db.name"
    SPAN_NAME_DB_ATTRIBUTE_STATEMENT = "db.statement"
    SPAN_NAME_DB_ATTRIBUTE_OPERATION = "db.operation"

    SPAN_NAME_HTTP_METHOD_GET = "GET"
    SPAN_NAME_HTTP_METHOD_POST = "POST"
    SPAN_NAME_HTTP_METHOD_PUT = "PUT"
    SPAN_NAME_HTTP_METHOD_PATCH = "PATCH"
    SPAN_NAME_HTTP_METHOD_DELETE = "DELETE"

    SPAN_NAME_HTTP_ATTRIBUTE_ERROR_TYPE = "error.type"
    SPAN_NAME_HTTP_ATTRIBUTE_METHOD = "http.request.method"
    SPAN_NAME_HTTP_ATTRIBUTE_RESPONSE_STATUS_CODE = "http.response.status_code"
    SPAN_NAME_HTTP_ATTRIBUTE_NETWORK_ADDRESS = "network.peer.address"
    SPAN_NAME_HTTP_ATTRIBUTE_REQ_RESEND_COUNT = "http.request.resend_count"
    SPAN_NAME_HTTP_ATTRIBUTE_SERVER_ADDRESS = "server.address"
    SPAN_NAME_HTTP_ATTRIBUTE_SERVER_PORT = "server.port"
    SPAN_NAME_HTTP_ATTRIBUTE_URL_FULL = "url.full"

    SPAN_NAME_MSG_OPERATION_PUBLISHER = "publish"
    SPAN_NAME_MSG_OPERATION_CREATE = "create"
    SPAN_NAME_MSG_OPERATION_RECEIVE = "receive"
    SPAN_NAME_MSG_OPERATION_DELIVER = "deliver"

    SPAN_NAME_MSG_ATTRIBUTE_ERROR_TYPE = "error.type"
    SPAN_NAME_MSG_ATTRIBUTE_OPERATION = "messaging.operation"
    SPAN_NAME_MSG_ATTRIBUTE_SYSTEM = "messaging.system"
    SPAN_NAME_MSG_ATTRIBUTE_SERVER_ADDRESS = "server.address"
    SPAN_NAME_MSG_ATTRIBUTE_SERVER_PORT = "server.port"

    SPAN_KIND_DB = SpanKind.CLIENT
    SPAN_KIND_HTTP_CLIENT = SpanKind.CLIENT
    SPAN_KIND_MSG_PUBLISHER = SpanKind.PRODUCER
    SPAN_KIND_MSG_RECEIVER = SpanKind.CONSUMER
