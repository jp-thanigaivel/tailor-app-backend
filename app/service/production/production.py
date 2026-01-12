import logging

from starlette import status
from typing_extensions import Any

from app.core.config import settings as app_config
from app.core.logging_context import MDC
from app.constants.production import ProductionModelKeyEnum
from app.dependencies.database.mongodb.database import MongoDBClient
from app.common.models import TokenData, DBPaginationMeta
from app.models.production import Production
from app.schemas.production import GetProductionResponse, \
    CreateProductionRequest, CreateProductionResponse, UpdateProductionRequest, UpdateProductionResponse
from app.service.database.database import MongoDBOperations
from app.utils.app_constant import LOG_CTX_UNIQ_TNX_KEY, RES_C_KEY_DATA, RES_C_KEY_PAGINATION, DOC_OBJ_ID, \
    PY_OBJ_ID, STATUS_TYPE_WARN, STATUS_DESC_NO_DATA, COLL_TODO_PRODUCTION, \
    SEQ_TODO_PRODUCTION_ID, PREFIX_SEQ_TODO_PRODUCTION_ID, COLL_TODO_SEQ_PRODUCTION_ID
from app.core.exceptions import NoDataFoundException
from app.utils.app_obj_mapper import AppObjectMapper
from app.utils.common_functions import DBUtils, CommonUtils
from app.utils.production_constant import Q_ALLOWED_FILTER_FIELDS_production, Q_ALLOWED_SORT_FIELDS_production
from app.validators.production import validate_create_production_request, validate_update_production_request

logger = logging.getLogger(__name__)

db_client = MongoDBClient().get_client()


def process_create_production_entry(create_production_req: CreateProductionRequest, token_data: TokenData):
    logger.info("start processing process_create_production_entry")

    db_name = app_config.data_base
    db_coll = COLL_TODO_PRODUCTION
    batch_number = str(create_production_req.batch_number)
    validate_create_production_request(create_production_req, token_data)
    #logger.info("Check for existing batch_number with {}".format(str(batch_number)))
    #query = CommonUtils.get_query({ProductionModelKeyEnum.BATCH_NUMBER.value: batch_number})
    create_production_req: dict[str, Any] = AppObjectMapper.get_model_dict_with_default_fields_for_create(create_production_req, token_data)

    logger.info("creating production id")
    production_id = DBUtils.get_formatted_sequence(COLL_TODO_SEQ_PRODUCTION_ID, SEQ_TODO_PRODUCTION_ID,
                                                 PREFIX_SEQ_TODO_PRODUCTION_ID)
    MDC.put(LOG_CTX_UNIQ_TNX_KEY, str(batch_number + " " + str(batch_number)))
    create_production_req[ProductionModelKeyEnum.PRODUCTION_ID.value] = production_id

    production_obj: Production = Production(**create_production_req)
    document_id = MongoDBOperations.insert_document(db_name, db_coll, production_obj)
    logger.debug("inserted document_id {}".format(str(document_id)))

    production_json = production_obj.model_dump(by_alias=True,
                                      exclude_unset=True,
                                      mode='json')
    create_production_response: CreateProductionResponse = CreateProductionResponse(**production_json)
    logger.debug("create_production_response {}".format(str(production_json)))
    logger.info("end processing")
    return create_production_response


def process_update_production_entry(update_production_request: UpdateProductionRequest, token_data: TokenData):
    logger.info("start processing process_update_production_entry")

    db_name = app_config.data_base
    db_coll = COLL_TODO_PRODUCTION
    production_id = str(
        update_production_request.production_id)

    logger.info("processing update production id {}".format(production_id))
    production: Production = get_production_obj_by_id(production_id, token_data)
    validate_update_production_request(production, update_production_request, token_data)

    updated_production_obj: Production = AppObjectMapper.update_db_model_from_schema(production,
                                                                                     update_production_request,
                                                                                     token_data)
    filter_condition = CommonUtils.get_query({ProductionModelKeyEnum.PRODUCTION_ID.value: production_id})
    MongoDBOperations.replace_document(db_name, db_coll, filter_condition, updated_production_obj)

    logger.debug("replaced document_id {}".format(str(updated_production_obj.id)))
    production_json = updated_production_obj.model_dump(by_alias=True,
                                                        exclude_unset=True,
                                                        mode='json')
    update_production_response: UpdateProductionResponse = UpdateProductionResponse(**production_json)
    logger.debug("update_production_response {}".format(str(production_json)))
    logger.info("end processing")

    return update_production_response


def get_all_production(query_param: dict[str, str], token_data: TokenData):
    logger.info("start processing get_all_production")

    db_name = app_config.data_base
    db_coll = COLL_TODO_PRODUCTION
    db_pagination_metadata: DBPaginationMeta = AppObjectMapper.get_db_meta(query_param, Q_ALLOWED_FILTER_FIELDS_production,
                                                                           Q_ALLOWED_SORT_FIELDS_production)

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
        production_list = AppObjectMapper.get_model_dict_for_list(db_document, GetProductionResponse)
        logger.info("returning list of production {}".format(len(production_list)))
        return {RES_C_KEY_DATA: production_list, RES_C_KEY_PAGINATION: db_pagination}
    else:
        logger.warning("No production found")
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA)

def get_production_response_by_id(production_id: str, token_data: TokenData) -> dict[str, Any]:
    logger.info("start processing get_production_by_id {}".format(str(production_id)))
    db_production_dict: dict = get_production_dict_by_id(production_id, token_data)
    return get_production_response_from_model(db_production_dict, token_data)

def get_production_obj_by_id(production_id: str, token_data: TokenData) -> Production:
    db_production_dict: dict = get_production_dict_by_id(production_id, token_data)
    return get_production_obj_from_db_dict(db_production_dict, token_data)

def get_production_response_from_model(db_production_dict: dict, token_data: TokenData) -> dict[str, Any]:
    production: Production = get_production_obj_from_db_dict(db_production_dict, token_data)
    production_json:dict = AppObjectMapper.get_model_json(production)
    production_response = AppObjectMapper.get_model_dict_for_one(production_json, GetProductionResponse)
    return {RES_C_KEY_DATA: production_response, RES_C_KEY_PAGINATION: ""}


def get_production_obj_from_db_dict(db_production_dict: dict[str, Any], token_data: TokenData) -> Production:
    doc_id = str(db_production_dict[DOC_OBJ_ID])
    db_production_dict[PY_OBJ_ID] = doc_id
    production: Production = Production(**db_production_dict)
    logger.info("serialized and returning production_dict for {}".format(str(production.production_id)))
    return production


def get_production_dict_by_id(production_id: str, token_data: TokenData) -> dict[str, Any]:
    db_name = app_config.data_base
    db_coll = COLL_TODO_PRODUCTION
    logger.info("get db client with db_name {} db_coll {}".format(str(db_name), str(db_coll)))

    query = CommonUtils.get_query({ProductionModelKeyEnum.PRODUCTION_ID.value: production_id})
    db_response = MongoDBOperations.find_document(db_name=db_name, db_coll=db_coll, filter_condition=query)
    db_response_data = db_response[RES_C_KEY_DATA]

    logger.debug("After db_response_data {}".format(str(db_response_data)))
    if db_response_data is None or len(db_response_data) <= 0:
        logger.warning("No data found for production_id {}".format(str(production_id)))
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " production_id: " + str(production_id))

    production_dict = db_response_data[0]
    logger.info("Returned get_production_dict_by_id production_dict {}".format(str(production_id)))
    return production_dict