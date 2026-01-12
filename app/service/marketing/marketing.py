import logging
from datetime import datetime

from starlette import status
from typing_extensions import Any

from app.core.config import settings as app_config
from app.core.logging_context import MDC
from app.constants.marketing import MarketingModelKeyEnum
from app.dependencies.database.mongodb.database import MongoDBClient
from app.common.models import TokenData, DBPaginationMeta
from app.models.marketing import Marketing
from app.schemas.marketing import CreateMarketingRequest, CreateMarketingResponse, GetMarketingResponse, \
    UpdateMarketingRequest, UpdateMarketingResponse
from app.service.database.database import MongoDBOperations
from app.utils.app_constant import LOG_CTX_UNIQ_TNX_KEY, RES_C_KEY_DATA, RES_C_KEY_PAGINATION, DOC_OBJ_ID, \
    PY_OBJ_ID, STATUS_TYPE_WARN, STATUS_DESC_NO_DATA, COLL_TODO_SEQ_MARKETING_ID, SEQ_TODO_MARKETING_ID, \
    PREFIX_SEQ_TODO_MARKETING_ID, COLL_TODO_MARKETING
from app.core.exceptions import NoDataFoundException, InvalidRequestException
from app.utils.app_obj_mapper import AppObjectMapper
from app.utils.common_functions import DBUtils, CommonUtils
from app.utils.marketing_constant import Q_ALLOWED_FILTER_FIELDS_marketing, Q_ALLOWED_SORT_FIELDS_marketing
from app.validators.marketing import validate_update_marking_request, pre_validation_for_delete, \
    validate_create_marketing_request

logger = logging.getLogger(__name__)

db_client = MongoDBClient().get_client()


def process_create_marketing_entry(create_marketing_req: CreateMarketingRequest, token_data: TokenData):
    logger.info("start processing process_create_marketing_entry")

    db_name = app_config.data_base
    db_coll = COLL_TODO_MARKETING
    validate_create_marketing_request(create_marketing_req, token_data)
    contact_phone_number = str(create_marketing_req.contact_phone_number)
    create_marketing_req: dict[str, Any] = AppObjectMapper.get_model_dict_with_default_fields_for_create(create_marketing_req, token_data)

    logger.info("creating marketing id")
    marketing_id = DBUtils.get_formatted_sequence(COLL_TODO_SEQ_MARKETING_ID, SEQ_TODO_MARKETING_ID,
                                                 PREFIX_SEQ_TODO_MARKETING_ID)
    MDC.put(LOG_CTX_UNIQ_TNX_KEY, str(contact_phone_number + " " + str(contact_phone_number)))
    create_marketing_req[MarketingModelKeyEnum.MARKETING_ID.value] = marketing_id

    marketing_obj: Marketing = Marketing(**create_marketing_req)
    document_id = MongoDBOperations.insert_document(db_name, db_coll, marketing_obj)
    logger.debug("inserted document_id {}".format(str(document_id)))

    marketing_json = marketing_obj.model_dump(by_alias=True,
                                      exclude_unset=True,
                                      mode='json')
    create_marketing_response: CreateMarketingResponse = CreateMarketingResponse(**marketing_json)
    logger.debug("create_marketing_response {}".format(str(marketing_json)))
    logger.info("end processing")
    return create_marketing_response


def get_all_marketing(query_param: dict[str, str], token_data: TokenData):
    logger.info("start processing get_all_marketing")

    db_name = app_config.data_base
    db_coll = COLL_TODO_MARKETING
    db_pagination_metadata: DBPaginationMeta = AppObjectMapper.get_db_meta(query_param, Q_ALLOWED_FILTER_FIELDS_marketing,
                                                                           Q_ALLOWED_SORT_FIELDS_marketing)

    logger.info(
        "get db client with db_name {} db_coll {} filter_condition {} sort_key {}".format(str(db_name), str(db_coll),
                                                                                          str(db_pagination_metadata.filter_condition),
                                                                                          str(db_pagination_metadata.sort_key)))
    db_response = MongoDBOperations.find_document_with_pagination(db_name=db_name, db_coll=db_coll,
                                                                  filter_condition=db_pagination_metadata.filter_condition,
                                                                  page_size=db_pagination_metadata.page_size,
                                                                  page_number=db_pagination_metadata.page_number,
                                                                  cursor=db_pagination_metadata.cursor,
                                                                  sort_condition=db_pagination_metadata.sort_condition)
    db_document = db_response[RES_C_KEY_DATA]
    db_pagination = db_response[RES_C_KEY_PAGINATION]

    logger.info("Received response from db db_pagination {}".format(str(db_pagination)))
    logger.debug("Received response from db data {} ".format(str(db_document)))

    if db_document and len(db_document) > 0:
        marketing_list = AppObjectMapper.get_model_dict_for_list(db_document, GetMarketingResponse)
        logger.info("returning list of marketing {}".format(len(marketing_list)))
        return {RES_C_KEY_DATA: marketing_list, RES_C_KEY_PAGINATION: db_pagination}
    else:
        logger.warning("No marketing found")
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA)

def process_update_marketing_entry(update_marketing_request: UpdateMarketingRequest, token_data: TokenData):
    logger.info("start processing process_update_marketing_entry")

    db_name = app_config.data_base
    db_coll = COLL_TODO_MARKETING
    marketing_id = str(update_marketing_request.marketing_id)

    logger.info("processing update marketing id {}".format(str(marketing_id)))
    marketing: Marketing = get_marketing_obj_by_id(marketing_id, token_data)
    validate_update_marking_request(marketing, update_marketing_request, token_data)

    updated_marketing_obj: Marketing = AppObjectMapper.update_db_model_from_schema(marketing, update_marketing_request, token_data)
    filter_condition = CommonUtils.get_query({MarketingModelKeyEnum.MARKETING_ID.value: marketing_id})
    MongoDBOperations.replace_document(db_name, db_coll, filter_condition, updated_marketing_obj)
    logger.debug("replaced document_id {}".format(str(updated_marketing_obj.id)))
    marketing_json = updated_marketing_obj.model_dump(by_alias=True,
                                              exclude_unset=True,
                                              mode='json')
    update_marketing_response: UpdateMarketingResponse = UpdateMarketingResponse(**marketing_json)
    logger.debug("update_marketing_response {}".format(str(marketing_json)))
    logger.info("end processing")
    return update_marketing_response

def get_marketing_response_by_id(marketing_id: str, token_data: TokenData) -> dict[str, Any]:
    logger.info("start processing get_marketing_by_id {}".format(str(marketing_id)))
    db_marketing_dict: dict = get_marketing_dict_by_id(marketing_id, token_data)
    return get_marketing_response_from_model(db_marketing_dict, token_data)

def get_marketing_obj_by_id(marketing_id: str, token_data: TokenData) -> Marketing:
    db_marketing_dict: dict = get_marketing_dict_by_id(marketing_id, token_data)
    return get_marketing_obj_from_db_dict(db_marketing_dict, token_data)

def get_marketing_response_from_model(db_marketing_dict: dict, token_data: TokenData) -> dict[str, Any]:
    marketing: Marketing = get_marketing_obj_from_db_dict(db_marketing_dict, token_data)
    marketing_json:dict = AppObjectMapper.get_model_json(marketing)
    marketing_response = AppObjectMapper.get_model_dict_for_one(marketing_json, GetMarketingResponse)
    return {RES_C_KEY_DATA: marketing_response, RES_C_KEY_PAGINATION: ""}


def get_marketing_obj_from_db_dict(db_marketing_dict: dict[str, Any], token_data: TokenData) -> Marketing:
    doc_id = str(db_marketing_dict[DOC_OBJ_ID])
    db_marketing_dict[PY_OBJ_ID] = doc_id
    marketing: Marketing = Marketing(**db_marketing_dict)
    logger.info("serialized and returning marketing_dict for {}".format(str(marketing.marketing_id)))
    return marketing


def get_marketing_dict_by_id(marketing_id: str, token_data: TokenData) -> dict[str, Any]:
    db_name = app_config.data_base
    db_coll = COLL_TODO_MARKETING
    logger.info("get db client with db_name {} db_coll {}".format(str(db_name), str(db_coll)))

    query = CommonUtils.get_query({MarketingModelKeyEnum.MARKETING_ID.value: marketing_id})
    db_response = MongoDBOperations.find_document(db_name=db_name, db_coll=db_coll, filter_condition=query)
    db_response_data = db_response[RES_C_KEY_DATA]

    logger.debug("After db_response_data {}".format(str(db_response_data)))
    if db_response_data is None or len(db_response_data) <= 0:
        logger.warning("No data found for marketing_id {}".format(str(marketing_id)))
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " marketing_id: " + str(marketing_id))

    marketing_dict = db_response_data[0]
    logger.info("Returned get_marketing_dict_by_id marketing_dict {}".format(str(marketing_id)))
    return marketing_dict

def delete_marketing_by_id(marketing_id: str, token_data: TokenData):
    db_name = app_config.data_base
    db_coll = COLL_TODO_MARKETING
    logger.info(f"Delete request for marketing_id {marketing_id} in db {db_name}, coll {db_coll}")

    # Pre-validation step (can add permission checks, status checks, etc.)
    pre_validation_for_delete(marketing_id, token_data)

    query = CommonUtils.get_query({MarketingModelKeyEnum.MARKETING_ID.value: marketing_id})
    count = MongoDBOperations.delete_document(db_name=db_name, db_coll=db_coll, query=query)

    logger.info("After db_response_count {}".format(str(count)))
    if count <= 0:
        logger.warning("No data found to delete for marketing_id {}".format(str(marketing_id)))
        raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, STATUS_TYPE_WARN,
                                      STATUS_DESC_NO_DATA + " marketing_id: " + str(marketing_id))
    logger.info("Deleted marketing_id {}".format(str(marketing_id)))

def marketing_by_range(query_param: dict[str, str], token_data: TokenData) -> dict[str, Any]:
    db_name = app_config.data_base
    db_coll = COLL_TODO_MARKETING
    logger.info(f"Fetching marketing data by range {query_param}")

    db_pagination_metadata: DBPaginationMeta = AppObjectMapper.get_db_meta(query_param,
                                                                           Q_ALLOWED_FILTER_FIELDS_marketing,
                                                                           Q_ALLOWED_SORT_FIELDS_marketing)

    db_response = MongoDBOperations.find_document(db_name=db_name, db_coll=db_coll,
                                                  filter_condition=db_pagination_metadata.filter_condition)
    db_response_data = db_response[RES_C_KEY_DATA]

    if not db_response_data:
        logger.warning("No marketing data found for the given period")
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN, STATUS_DESC_NO_DATA)
    logger.info("Fetched marketing data successfully")
    return {RES_C_KEY_DATA: db_response_data}