import logging

from app.observability.app_observability_utils import AppTraceSpanEnum

logger = logging.getLogger(__name__)


def get_span_name(db_name, db_coll, db_operation):
    span_name = str(db_name) + "." + str(db_coll) + "." + db_operation
    return span_name


def get_span_attributes(db_name, db_coll, db_operation, query_statement):
    span_att = {AppTraceSpanEnum.SPAN_NAME_DB_ATTRIBUTE_COLLECTION_NAME.value: db_coll,
                AppTraceSpanEnum.SPAN_NAME_DB_ATTRIBUTE_SYSTEM.value: "mongodb",
                AppTraceSpanEnum.SPAN_NAME_DB_ATTRIBUTE_NAME.value: db_name,
                AppTraceSpanEnum.SPAN_NAME_DB_ATTRIBUTE_STATEMENT.value: query_statement,
                AppTraceSpanEnum.SPAN_NAME_DB_ATTRIBUTE_OPERATION.value: db_operation}
    return span_att
