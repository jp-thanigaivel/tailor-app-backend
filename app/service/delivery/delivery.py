import logging

from starlette import status
from typing_extensions import Any

from app.core.config import settings as app_config
from app.core.logging_context import MDC
from app.constants.delivery import DeliveryModelKeyEnum
from app.dependencies.database.mongodb.database import MongoDBClient
from app.common.models import TokenData, DBPaginationMeta
from app.models.delivery import Delivery
from app.schemas.delivery import (
    CreateDeliveryRequest,
    CreateDeliveryResponse,
    GetDeliveryResponse,
    UpdateDeliveryRequest,
    UpdateDeliveryResponse
)
from app.service.database.database import MongoDBOperations
from app.utils.app_constant import (
    LOG_CTX_UNIQ_TNX_KEY, RES_C_KEY_DATA, RES_C_KEY_PAGINATION, DOC_OBJ_ID, PY_OBJ_ID,
    STATUS_TYPE_WARN, STATUS_DESC_NO_DATA,
    COLL_TODO_SEQ_DELIVERY_ID, SEQ_TODO_DELIVERY_ID, PREFIX_SEQ_TODO_DELIVERY_ID,
    COLL_TODO_DELIVERY
)
from app.core.exceptions import NoDataFoundException
from app.utils.app_obj_mapper import AppObjectMapper
from app.utils.common_functions import DBUtils, CommonUtils
from app.utils.delivery_constant import Q_ALLOWED_FILTER_FIELDS_delivery, Q_ALLOWED_SORT_FIELDS_delivery
from app.validators.delivery import validate_create_delivery_request, validate_update_delivery_request

logger = logging.getLogger(__name__)
db_client = MongoDBClient().get_client()


def process_create_delivery_entry(create_delivery_req_obj: CreateDeliveryRequest, token_data: TokenData):
    logger.info("start processing process_create_delivery_entry")

    db_name = app_config.data_base
    db_coll = COLL_TODO_DELIVERY
    validate_create_delivery_request(create_delivery_req_obj, token_data)
    create_delivery_req: dict[str, Any] = AppObjectMapper.get_model_dict_with_default_fields_for_create(create_delivery_req_obj, token_data)


    logger.info("creating delivery id")
    delivery_id = DBUtils.get_formatted_sequence(COLL_TODO_SEQ_DELIVERY_ID, SEQ_TODO_DELIVERY_ID, PREFIX_SEQ_TODO_DELIVERY_ID)
    MDC.put(LOG_CTX_UNIQ_TNX_KEY, f"delivery-{delivery_id}")
    create_delivery_req["deliveryId"] = delivery_id

    delivery_obj: Delivery = Delivery(**create_delivery_req)
    document_id = MongoDBOperations.insert_document(db_name, db_coll, delivery_obj)
    logger.debug("inserted document_id {}".format(str(document_id)))

    delivery_json = delivery_obj.model_dump(by_alias=True, exclude_unset=True, mode='json')
    create_delivery_response: CreateDeliveryResponse = CreateDeliveryResponse(**delivery_json)

    logger.debug("create_delivery_response {}".format(str(delivery_json)))
    logger.info("end processing")
    return create_delivery_response


def get_all_deliveries(query_param: dict[str, str], token_data: TokenData):
    logger.info("start processing get_all_deliveries")

    db_name = app_config.data_base
    db_coll = COLL_TODO_DELIVERY
    db_pagination_metadata: DBPaginationMeta = AppObjectMapper.get_db_meta(
        query_param, Q_ALLOWED_FILTER_FIELDS_delivery, Q_ALLOWED_SORT_FIELDS_delivery
    )

    logger.info(f"get db client with db_name {db_name} db_coll {db_coll} filter {db_pagination_metadata.filter_condition}")

    db_response = MongoDBOperations.find_document_with_pagination(
        db_name=db_name,
        db_coll=db_coll,
        filter_condition=db_pagination_metadata.filter_condition,
        page_size=db_pagination_metadata.page_size,
        page_number=db_pagination_metadata.page_number,
        cursor=db_pagination_metadata.cursor,
        sort_condition=db_pagination_metadata.sort_condition
    )

    db_document = db_response[RES_C_KEY_DATA]
    db_pagination = db_response[RES_C_KEY_PAGINATION]

    if db_document and len(db_document) > 0:
        delivery_list = AppObjectMapper.get_model_dict_for_list(db_document, GetDeliveryResponse)
        return {RES_C_KEY_DATA: delivery_list, RES_C_KEY_PAGINATION: db_pagination}
    else:
        raise NoDataFoundException(
            status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
            STATUS_DESC_NO_DATA
        )


def process_update_delivery_entry(update_delivery_request: UpdateDeliveryRequest, token_data: TokenData):
    logger.info("start processing process_update_delivery_entry")

    db_name = app_config.data_base
    db_coll = COLL_TODO_DELIVERY
    delivery_id = str(update_delivery_request.delivery_id)

    logger.info(f"processing update delivery id {delivery_id}")
    delivery: Delivery = get_delivery_obj_by_id(delivery_id, token_data)
    validate_update_delivery_request(delivery, update_delivery_request, token_data)

    updated_delivery_obj: Delivery = AppObjectMapper.update_db_model_from_schema(
        delivery, update_delivery_request, token_data
    )

    filter_condition = CommonUtils.get_query({DeliveryModelKeyEnum.DELIVERY_ID.value: delivery_id})
    MongoDBOperations.replace_document(db_name, db_coll, filter_condition, updated_delivery_obj)

    logger.debug(f"replaced document_id {updated_delivery_obj.id}")
    delivery_json = updated_delivery_obj.model_dump(by_alias=True, exclude_unset=True, mode='json')
    update_delivery_response = UpdateDeliveryResponse(**delivery_json)

    logger.info("end processing")
    return update_delivery_response


def get_delivery_response_by_id(delivery_id: str, token_data: TokenData) -> dict[str, Any]:
    logger.info(f"start processing get_delivery_by_id {delivery_id}")
    db_delivery_dict = get_delivery_dict_by_id(delivery_id, token_data)
    return get_delivery_response_from_model(db_delivery_dict, token_data)


def get_delivery_obj_by_id(delivery_id: str, token_data: TokenData) -> Delivery:
    db_delivery_dict = get_delivery_dict_by_id(delivery_id, token_data)
    return get_delivery_obj_from_db_dict(db_delivery_dict, token_data)


def get_delivery_response_from_model(db_delivery_dict: dict, token_data: TokenData) -> dict[str, Any]:
    delivery: Delivery = get_delivery_obj_from_db_dict(db_delivery_dict, token_data)
    delivery_json: dict = AppObjectMapper.get_model_json(delivery)
    delivery_response = AppObjectMapper.get_model_dict_for_one(delivery_json, GetDeliveryResponse)
    return {RES_C_KEY_DATA: delivery_response, RES_C_KEY_PAGINATION: ""}


def get_delivery_obj_from_db_dict(db_delivery_dict: dict[str, Any], token_data: TokenData) -> Delivery:
    doc_id = str(db_delivery_dict[DOC_OBJ_ID])
    db_delivery_dict[PY_OBJ_ID] = doc_id
    delivery: Delivery = Delivery(**db_delivery_dict)
    logger.info(f"serialized and returning delivery_dict for {delivery.delivery_id}")
    return delivery


def get_delivery_dict_by_id(delivery_id: str, token_data: TokenData) -> dict[str, Any]:
    db_name = app_config.data_base
    db_coll = COLL_TODO_DELIVERY

    query = CommonUtils.get_query({DeliveryModelKeyEnum.DELIVERY_ID.value: delivery_id})
    db_response = MongoDBOperations.find_document(db_name=db_name, db_coll=db_coll, filter_condition=query)
    db_response_data = db_response[RES_C_KEY_DATA]

    if not db_response_data:
        raise NoDataFoundException(
            status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
            STATUS_DESC_NO_DATA + f" delivery_id: {delivery_id}"
        )

    delivery_dict = db_response_data[0]
    return delivery_dict
