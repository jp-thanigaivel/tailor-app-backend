import logging
from datetime import datetime

from starlette import status

from app.core.config import settings as app_config
from app.models.otp import OTPRequest, OTPDetail, OTPDetailResponse, VerifyOTP
from app.service.database.database import MongoDBOperations
from app.service.otp.otp_generation_factory import get_otp_value
from app.utils.app_constant import COLL_TODO_OTP_DETAIL, RES_C_KEY_DATA, STATUS_TYPE_WARN, STATUS_DESC_NO_DATA, \
    DOC_OBJ_ID, PY_OBJ_ID, STATUS_TYPE_ERROR
from app.core.exceptions import NoDataFoundException, NotMatchException, OTPExpiredException, \
    InvalidRequestException
from app.utils.common_functions import CommonUtils, DateUtils
from app.utils.otp_constant import KEY_N_OTP_VALUE, KEY_N_OTP_KEY, KEY_N_OTP_EXPIRY_TIME

logger = logging.getLogger(__name__)


def generate_otp(otp_request: OTPRequest) -> OTPDetailResponse:
    logger.info("In generate_otp")
    otp_key = otp_request.otp_key
    otp_generation_policy = otp_request.otp_generation_policy
    otp_expiry_time_unit = otp_request.otp_expiry_time_unit
    updated_by = otp_request.updated_by

    logger.info("Check for existing entry {}".format(str(otp_key)))
    is_update = False
    b_json_id = None
    db_otp_expiry_time = None
    try:
        otp_detail_obj = get_otp_obj_by_id(otp_key)
        logger.info("Found otp_detail for otp_key {} ".format(str(otp_key)))
        b_json_id = otp_detail_obj.id
        db_otp_expiry_time = otp_detail_obj.otp_expiry_time
        is_update = True
    except NoDataFoundException as exp:
        logger.info("No otp_detail found for otp_key {} ".format(str(otp_key)))

    logger.info("get otp_value by policy id {}".format(str(otp_generation_policy)))
    otp_value = get_otp_value(otp_generation_policy, db_otp_expiry_time)
    logger.info("generated otp_value {}".format(str(otp_value)))

    hours_to_add, minutes_to_add, seconds_to_add = CommonUtils.get_time_value(otp_expiry_time_unit)
    expire_time: datetime = DateUtils.add_time_to_current_datetime(hours_to_add, minutes_to_add, seconds_to_add)

    # Create OTP Detail
    if not is_update:
        logger.info("In create otp_detail {}".format(str(otp_key)))
        otp_request_dict = otp_request.model_dump(exclude_none=True)
        otp_request_dict[KEY_N_OTP_VALUE] = otp_value
        otp_request_dict[KEY_N_OTP_EXPIRY_TIME] = expire_time
        otp_detail = OTPDetail(**otp_request_dict)
        logger.info("created otp_detail_request {}".format(str(otp_key)))

        _insert_otp_request(otp_detail)
        logger.info("otp detail inserted for {} with {}".format(str(otp_key), str(expire_time)))
    else:
        logger.info("In update otp_detail {}".format(str(otp_key)))
        _update_otp_detail(b_json_id, otp_key, otp_value, expire_time, updated_by)
        logger.info("otp detail updated for {} with {}".format(str(otp_key), str(expire_time)))

    return OTPDetailResponse(otp_key=str(otp_key), otp_value=otp_value, otp_expiry_time=expire_time)


def verify_otp_service(verify_otp_request: VerifyOTP) -> bool:
    logger.info("in verify_otp_service {} {}".format(str(verify_otp_request.otp_key), str(verify_otp_request.otp_value)))
    otp_key = verify_otp_request.otp_key
    otp_value = verify_otp_request.otp_value
    otp_detail_obj: OTPDetail = get_otp_obj_by_id(otp_key)
    db_otp_value = str(otp_detail_obj.otp_value)
    db_expiry_value = otp_detail_obj.otp_expiry_time

    # Verify Expiry
    current_time = DateUtils.get_current_datetime()
    is_active = DateUtils.compare_date1_gte(db_expiry_value, current_time)
    logger.info("opt entry is_active {}".format(str(is_active)))
    if not is_active:
        logger.error("otp is not active {}".format(str(otp_key)))
        raise OTPExpiredException(status.HTTP_400_BAD_REQUEST, STATUS_TYPE_ERROR, "otp expired")

    # Verify Match
    if db_otp_value != otp_value:
        logger.error("Otp not matched db_otp_value {} otp_value {} for {}".format(str(db_otp_value),
                                                                                  str(otp_value),
                                                                                  str(otp_key)))
        raise NotMatchException(status.HTTP_400_BAD_REQUEST, STATUS_TYPE_ERROR, "Not matched")

    logger.info("opt matched {}".format(str(otp_key)))
    _delete_otp_detail_by_id(otp_key)
    logger.info("opt deleted {}".format(str(otp_key)))
    return is_active


"""
WARNING : BELOW ARE THE INTERNAL METHODS SHOULD BE USED OUTSIDE THIS FILE
"""


def _insert_otp_request(otp_detail_obj: OTPDetail):
    logger.info("inserting otp details")
    db_name = app_config.data_base
    db_coll = COLL_TODO_OTP_DETAIL

    document_id = MongoDBOperations.insert_document(db_name, db_coll, otp_detail_obj)
    logger.debug("inserted document_id {}".format(str(document_id)))
    otp_detail_obj.id = str(document_id)


def get_otp_by_otp_key(otp_key):
    logger.info("In get_otp_by_otp_key {}".format(str(otp_key)))
    db_name = app_config.data_base
    db_coll = COLL_TODO_OTP_DETAIL
    query = CommonUtils.get_query({KEY_N_OTP_KEY: otp_key})
    db_response = MongoDBOperations.find_document(db_name=db_name, db_coll=db_coll, filter_condition=query)
    db_response_data = db_response[RES_C_KEY_DATA]

    logger.debug("After db_response_data {}".format(str(db_response_data)))
    if db_response_data is None or len(db_response_data) <= 0:
        logger.warning("No data found for order_id {}".format(str(otp_key)))
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " otp_key: " + str(otp_key))

    otp_detail_dict = db_response_data[0]
    return otp_detail_dict


def get_otp_obj_by_id(otp_key) -> OTPDetail:
    logger.info("In get_otp_obj_by_id {}".format(str(otp_key)))
    otp_detail_dict = get_otp_by_otp_key(otp_key)
    doc_id = str(otp_detail_dict[DOC_OBJ_ID])
    otp_detail_dict[PY_OBJ_ID] = doc_id
    otp_detail = OTPDetail(**otp_detail_dict)
    logger.info("serialized and returning order_dict for {}".format(str(otp_key)))
    return otp_detail


def _update_otp_detail(b_json_id, otp_key, otp_value, otp_expiry_time, updated_by):
    db_name = app_config.data_base
    db_coll = COLL_TODO_OTP_DETAIL

    #filter_query, update_query = q_otp_detail_update(b_json_id, otp_key, otp_value, otp_expiry_time, updated_by)
    otp_detail_document_updated = MongoDBOperations.upsert_document(db_name, db_coll, {}, {})
    logger.info("Upsert document count {}".format(str(otp_detail_document_updated)))

    if otp_detail_document_updated == 0:
        logger.error("No document updated in otp_detail collection {}".format(str(db_coll)))
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " No document_updated in otp_detail")


def _delete_otp_detail_by_id(otp_key):
    logger.info("start processing _delete_otp_detail_by_id {}".format(str(otp_key)))
    db_name = app_config.data_base
    db_coll = COLL_TODO_OTP_DETAIL
    logger.info("get db client with db_name {} db_coll {}".format(str(db_name), str(db_coll)))

    query = CommonUtils.get_query({KEY_N_OTP_KEY: otp_key})
    count = MongoDBOperations.delete_document(db_name=db_name, db_coll=db_coll, query=query)

    logger.info("After db_response_count {}".format(str(count)))
    if count <= 0:
        logger.warning("No data found to delete for otp_key {}".format(str(otp_key)))
        raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, STATUS_TYPE_WARN,
                                      STATUS_DESC_NO_DATA + " otp_key: " + str(otp_key))
