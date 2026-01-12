import logging

from bson import ObjectId

from app.utils.app_constant import DOC_OBJ_ID, KEY_N_ALIAS_UPDATED_ON, KEY_N_ALIAS_UPDATED_BY
from app.utils.common_functions import DateUtils
from app.utils.product_constant import KEY_PRODUCT_ID, KEY_PRODUCT_IS_AVAILABLE, KEY_PRODUCT_IS_PRE_BOOK_ALLOWED, \
    KEY_COUPON_CODE, KEY_COUPON_CODE_STATUS, KEY_COUPON_CODE_ATTR

logger = logging.getLogger(__name__)


def q_product_availability_update(b_json_id, product_id, product_availability, is_pre_book_allowed, updated_by):
    q_key_id = DOC_OBJ_ID
    q_filter_product_id = f"{KEY_PRODUCT_ID}"
    q_key_product_available = f"{KEY_PRODUCT_IS_AVAILABLE}"
    q_key_pre_book_allowed = f"{KEY_PRODUCT_IS_PRE_BOOK_ALLOWED}"
    q_key_product_updated_on = f"{KEY_N_ALIAS_UPDATED_ON}"
    q_key_product_updated_by = f"{KEY_N_ALIAS_UPDATED_BY}"
    logger.info("In q_product_detail ")
    update_dict = {
        q_key_product_available: product_availability,
        q_key_product_updated_on: DateUtils.get_current_datetime(),
        q_key_product_updated_by: updated_by
    }
    if is_pre_book_allowed is not None:
        update_dict[q_key_pre_book_allowed] = is_pre_book_allowed

    update_query = {
        "$set": update_dict
    }
    filter_query = {
        q_key_id: ObjectId(b_json_id),
        q_filter_product_id: product_id
    }

    logger.info("Final filter_query {} update_query {}".format(str(filter_query), str(update_query)))
    return filter_query, update_query


def q_coupon_detail_update(b_json_id, coupon_code, coupon_status, coupon_attribute, updated_by):
    logger.info("In q_pre_book_order_detail_update ")
    q_key_id = f"{DOC_OBJ_ID}"
    q_key_coupon_code = f"{KEY_COUPON_CODE}"
    q_key_coupon_status = f"{KEY_COUPON_CODE_STATUS}"
    q_key_coupon_attr = f"{KEY_COUPON_CODE_ATTR}"
    q_key_order_updated_on = f"{KEY_N_ALIAS_UPDATED_ON}"
    q_key_order_updated_by = f"{KEY_N_ALIAS_UPDATED_BY}"

    update_dict = {
        q_key_coupon_status: coupon_status,
        q_key_order_updated_on: DateUtils.get_current_datetime(),
        q_key_order_updated_by: updated_by
    }

    if coupon_attribute is not None:
        update_dict[q_key_coupon_attr] = coupon_attribute

    update_query = {
        "$set": update_dict
    }
    filter_query = {
        q_key_id: ObjectId(b_json_id),
        q_key_coupon_code: coupon_code
    }
    logger.info("Final filter_query {} update_query {}".format(str(filter_query), str(update_query)))
    return filter_query, update_query

