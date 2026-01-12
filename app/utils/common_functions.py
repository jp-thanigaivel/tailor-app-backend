import base64
import json
import logging
import random
import string
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from bson import ObjectId
from jose import jwt
from passlib.context import CryptContext
from pymongo import ReturnDocument
from starlette import status
from typing_extensions import Any

from app.core.config import settings, get_app_secret, AuthConfig
from app.dependencies.database.mongodb.database import MongoDBClient
from app.common.models import TokenData, TimeQuantity, TimeUnit
from app.utils.app_constant import LOG_CTX_CID_KEY, Q_FILTER_CONDITION_AND, Q_FILTER_OPR_EQUALS, Q_AGG_TOTAL_COUNT, \
    INVALID_ARGUMENT_FOR_ARITHMETIC_OPR, STATUS_TYPE_ERROR, STATUS_DESC_NOT_IMPLEMENTED, \
    STATUS_DESC_INVALID_REQUEST_PARAM
from app.core.exceptions import NotImplementedException, InvalidRequestException

logger = logging.getLogger(__name__)
db_client = MongoDBClient().get_client()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



class CommonUtils:
    @classmethod
    def get_uniqueid(cls):
        return uuid.uuid4()

    @classmethod
    def get_uniqueid_str(cls):
        return str(uuid.uuid4())

    @classmethod
    def generate_or_get_cid(cls, request_headers):
        headers = request_headers
        if headers and headers.get(LOG_CTX_CID_KEY):
            return str(headers.get(LOG_CTX_CID_KEY))
        else:
            return str(cls.get_uniqueid())

    @classmethod
    def decode_string(cls, input_encoded_data):
        return base64.b64decode(input_encoded_data).decode("utf-8")
        # return base64.urlsafe_b64decode(input_encoded_data.encode('utf-8')).decode('utf-8')

    @classmethod
    def encode_string(cls, input_data):
        return base64.b64encode(json.dumps(input_data).encode("utf-8")).decode("utf-8")
        # return base64.urlsafe_b64encode(json.dumps(input_data).encode("utf-8")).decode('utf-8')

    @classmethod
    def get_json_format(cls, input_data):
        return json.loads(input_data)

    @classmethod
    def get_query_filter_condition(cls, allowed_fields, query_params) -> list[dict[Any, Any]]:
        logger.info("In get query filter condition")
        filter_condition = []
        for key, value in query_params.items():
            config_value = allowed_fields.get(key)
            if config_value:
                field_name = config_value.get("field")
                field_opr = config_value.get("filter_opr")
                field_type = config_value.get("field_type")
                try:
                    if field_type == 'datetime':
                        value = datetime.fromisoformat(value)
                    elif field_type == 'list':
                        value = value.split(',')
                    elif field_type == 'float':
                        value = float(value)
                    elif field_type == 'int':
                        value = int(value)
                except ValueError as exp:
                    logger.error(f"Unable to convert type from request param {field_name} - {field_type} "
                                 f"error_message {exp}")
                    raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, STATUS_TYPE_ERROR,
                                                  STATUS_DESC_INVALID_REQUEST_PARAM + " " + str(field_name))

                filter_condition.append({field_name: {field_opr: value}})
                logger.info("Given Query Param added to filter condition {} ".format(str(key)))
            else:
                logger.warning("Given Query param is not searchable {} ".format(str(key)))
        logger.info("Final filter_condition {} ".format(str(filter_condition)))
        return {Q_FILTER_CONDITION_AND: filter_condition if len(filter_condition) > 0 else [{}]}

    @classmethod
    def get_query_sort_condition(cls, query_params, allowed_fields=None) -> list[tuple[str, int]]:
        sort_key = query_params.get("sort")
        sort_condition = []
        if sort_key and allowed_fields:
            sort_keys = sort_key.split(',')
            for each_sort_key in sort_keys:
                config_value = allowed_fields.get(each_sort_key)
                if config_value:
                    field_name = config_value.get("field")
                    sort_opr = int(config_value.get("sort_opr"))
                    field_type = config_value.get("field_type")
                    sort_condition.append((field_name, sort_opr))
                    logger.info(
                        "Given Query Param added to sort condition {}|{}".format(str(sort_opr), str(field_name)))
                else:
                    logger.warning("Given Query param is not sortable {} ".format(str(each_sort_key)))
        if len(sort_condition) == 0:
            logger.warning("no sort condition added default sort condition")
            sort_condition = [("updatedOn", -1), ("_id", -1)]
        else:
            logger.info("added default sort condition to existing condition")
            sort_condition.append(("_id", -1))
        return sort_condition

    @classmethod
    def get_query(cls, req_dict):
        logger.info("In get query ")
        filter_condition_list = []
        for key, value in req_dict.items():
            filter_condition = {key: {Q_FILTER_OPR_EQUALS: value}}
            filter_condition_list.append(filter_condition)
        logger.info("Final filter_condition {} ".format(str(filter_condition)))
        return {Q_FILTER_CONDITION_AND: filter_condition_list}

    """
    @classmethod
    def get_query(cls, req_dict):
        logger.info("In get query ")
        filter_condition = {}
        for key, value in req_dict.items():
            filter_condition[key] = {Q_FILTER_OPR_EQUALS: value}
        logger.info("Final filter_condition {} ".format(str(filter_condition)))
        return {Q_FILTER_CONDITION_AND: [filter_condition]}
    """

    @classmethod
    def get_query_with_condition_option(cls, req_dict, q_filter_condition):
        logger.info("In get query with filter condition")
        filter_condition_list = []
        for key, value in req_dict.items():
            filter_condition = {key: {Q_FILTER_OPR_EQUALS: value}}
            filter_condition_list.append(filter_condition)
        logger.info("Final filter_condition {} ".format(str(filter_condition)))
        return {q_filter_condition: filter_condition_list}

    @classmethod
    def get_agg_pipeline_total_count(cls, filter_condition):
        return [
            {"$match": filter_condition},
            {"$count": Q_AGG_TOTAL_COUNT}
        ]

    @classmethod
    def get_hashed_data(cls, input_data):
        return pwd_context.hash(input_data)

    @classmethod
    def verify_password(cls, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_default_token_data(cls, user_dict, valid_till_in_min=None):
        if valid_till_in_min is None:
            valid_till_in_min = get_app_secret().auth_config.access_token_expire_minutes
        token_data = TokenData(user_id=user_dict['user_id'],
                               org_id=user_dict['org_id'],
                               user_roles=user_dict['user_roles'],
                               expiry=DateUtils.add_time_to_current_epoch(minutes_to_add=valid_till_in_min))
        return token_data.model_dump(exclude_none=True)

    @classmethod
    def get_anonymous_user_default_token_data(cls, user_id, org_id, user_roles, expiry):
        token_data = TokenData(user_id=user_id,
                               org_id=org_id,
                               user_roles=user_roles,
                               expiry=expiry)
        return token_data

    @classmethod
    def decode_default_token_data(cls, decoded_token_data):
        return TokenData(**decoded_token_data)

    @classmethod
    def create_jwt_token(cls, payload, secret_key):
        return jwt.encode(claims=payload, key=secret_key, algorithm=get_app_secret().auth_config.algorithm)

    @classmethod
    def decode_jwt_token(cls, token, secret_key):
        return jwt.decode(token=token, key=secret_key, algorithms=[get_app_secret().auth_config.algorithm])

    @classmethod
    def get_query_for_update_list(cls, object_key, object_id, p_embedded_doc_key, embedded_doc_key, embedded_doc_value):
        logger.info("In get query_for_update_list ")

        new_nested_document = {
            "ext_payment_id": "new_payment_id",
            "payment_status": "NEW_STATUS",
        }
        update_query = {
            "$set": {
                "order_payment_detail.$[elem]": new_nested_document
            }
        }

        """
        update_query = {
            "$set": {
                "order_payment_detail.$.payment_id": "PAY001-1",
                "order_payment_detail.$.ext_payment_id": "PAY001",
                "order_payment_detail.$.payment_status": "SUCCESS",
                "order_payment_detail.$.payment_attribute.attribute.new_field": {
                    "payment_id": "PAY001-1",
                    "ext_payment_id": "new_payment_id",
                    "payment_status": "NEW_STATUS",
                    "payment_attribute.attribute.new_field": "TESTNEW"
                }
            }
        }
        """

        filter_query = {
            "_id": ObjectId("64bd040c2fd653917b4f8ecf"),
            "order_payment_detail.payment_id": embedded_doc_value
        }
        # filter_query = {object_key: object_id, p_embedded_doc_key: {"$elemMatch":
        #                                                                {embedded_doc_key: embedded_doc_value}}}

        # filter_query = {"order_payment_detail.payment_id": embedded_doc_value}
        # update_query = {"$set": {p_embedded_doc_key + ".$": embedded_doc_value}}
        logger.info("Final filter_query {} update_query {}".format(str(filter_query), str(update_query)))
        return filter_query, update_query

    @classmethod
    def get_time_value(cls, time_qty_unit: TimeQuantity):
        hours_to_add = 0
        minutes_to_add = 0
        seconds_to_add = 0
        if time_qty_unit.unit == TimeUnit.SECOND:
            seconds_to_add = time_qty_unit.qty
        elif time_qty_unit.unit == TimeUnit.MINUTE:
            minutes_to_add = time_qty_unit.qty
        elif time_qty_unit.unit == TimeUnit.HOUR:
            hours_to_add = time_qty_unit.qty
        else:
            raise NotImplementedException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                          STATUS_DESC_NOT_IMPLEMENTED
                                          + " time_unit:" + str(time_qty_unit.unit))
        return hours_to_add, minutes_to_add, seconds_to_add

    @classmethod
    def is_transition_allowed(cls, trans_config, from_status: str, to_status: str) -> bool:
        logger.info("_is_transition_allowed {} -> {}".format(str(from_status), str(to_status)))
        if from_status in trans_config:
            if to_status in trans_config[from_status]:
                return True
        return False

    @classmethod
    def get_base64_encoded_data(cls, payload: str):
        return base64.b64encode(payload.encode("ascii")).decode()

    @classmethod
    def get_base64_decoded_data(cls, payload: str):
        return base64.b64decode(payload)

    @classmethod
    def get_random_string(cls, length: int = 6, pre_fix: str = None):
        rand_str = "".join(random.choices(string.ascii_uppercase +
                                          string.digits, k=length))
        if pre_fix:
            rand_str = pre_fix + "-" + rand_str
        return rand_str


class DBUtils:
    @classmethod
    def get_next_sequence(cls, collection_name, sequence_name):
        db_collection = db_client[settings.data_base][collection_name]
        result = db_collection.find_one_and_update({"_id": sequence_name},
                                                   {"$inc": {"current_sequence": 1}},
                                                   return_document=ReturnDocument.AFTER)
        if result is None:
            logger.error(f"Sequence document not found: _id={sequence_name} in {settings.data_base}.{collection_name}")
        return result

    @classmethod
    def get_formatted_sequence(cls, collection_name, sequence_name, prefix_char) -> str:
        db_collection = db_client[settings.data_base][collection_name]
        logger.info(f"Fetching sequence from {settings.data_base}.{collection_name} for {sequence_name}")
        sequence_id_sequence = db_collection.find_one_and_update({"_id": sequence_name},
                                                                {"$inc": {"current_sequence": 1}},
                                                                return_document=ReturnDocument.AFTER)
        if sequence_id_sequence is None:
            logger.error(f"Sequence document not found: _id={sequence_name} in {settings.data_base}.{collection_name}")
            raise RuntimeError(f"Database sequence '{sequence_name}' not found in collection '{collection_name}'. "
                             f"Please ensure the sequence is initialized in database '{settings.data_base}'.")
        
        generated_id_seq = sequence_id_sequence.get("current_sequence")
        f_generated_id = prefix_char + f'{generated_id_seq:05d}'
        return f_generated_id


class DateUtils:
    @classmethod
    def get_system_epoc_time(cls):
        return round(time.time())

    @classmethod
    def current_milli_time(cls):
        return round(time.time() * 1000)

    @classmethod
    def get_system_datetime(cls):
        return datetime.now

    @classmethod
    def get_system_date(cls, format="%Y-%m-%d"):
        sys_date = time.strftime(format, time.gmtime())
        return sys_date

    @classmethod
    def get_system_datetime_string(cls, format="%Y-%m-%d %H:%M:%S"):
        current_datetime = datetime.now()
        return current_datetime.strftime(format)

    @classmethod
    def convert_string_datetime(cls, datetime_str, format='%Y-%m-%d %H:%M:%S'):
        sys_datetime = datetime.strptime(datetime_str, format)
        return sys_datetime

    @classmethod
    def get_formatted_datetime_string(cls, datetime_str, current_format='%Y-%m-%d %H:%M:%S',
                                      required_format="%Y-%m-%d %H:%M:%S"):
        sys_datetime = datetime.strptime(datetime_str, current_format)
        formatted_string = sys_datetime.strftime(required_format)
        return formatted_string

    @classmethod
    def get_diff_sec(cls, date_1, date_2):
        if date_1 >= date_2:
            difference = date_1 - date_2
            return difference.total_seconds()
        else:
            return -1

    @classmethod
    def compare_date1_grt(cls, date_1, date_2):
        return date_1 > date_2

    @classmethod
    def compare_date1_gte(cls, date_1, date_2):
        return date_1 >= date_2

    @classmethod
    def get_current_datetime(cls):
        return datetime.now()

    @classmethod
    def convert_datetime_string(cls, datetime_obj, format='%Y-%m-%d %H:%M:%S'):
        datetime_string = datetime_obj.strftime(format)
        return datetime_string

    @classmethod
    def add_time_to_current_datetime(cls, hours_to_add: int = 0, minutes_to_add: int = 0, seconds_to_add: int = 0) \
            -> datetime:
        time_to_add = timedelta(hours=hours_to_add, minutes=minutes_to_add, seconds=seconds_to_add)
        return DateUtils.get_current_datetime() + time_to_add

    @classmethod
    def add_time_to_datetime(cls, start_datetime: datetime, hours_to_add: int = 0, minutes_to_add: int = 0,
                             seconds_to_add: int = 0):
        time_to_add = timedelta(hours=hours_to_add, minutes=minutes_to_add, seconds=seconds_to_add)
        return start_datetime + time_to_add

    @classmethod
    def add_time_to_current_epoch(cls, hours_to_add: int = 0, minutes_to_add: int = 0, seconds_to_add: int = 0):
        time_to_add = timedelta(hours=hours_to_add, minutes=minutes_to_add, seconds=seconds_to_add)
        return float(str((datetime.utcnow() + time_to_add).timestamp()))


class CalculateUtils:

    @classmethod
    def precise_addition(cls, *args):
        if len(args) == 0:
            raise ValueError(INVALID_ARGUMENT_FOR_ARITHMETIC_OPR + " addition")
        result = args[0]
        for num in args[1:]:
            result = Decimal(str(result)) + Decimal(str(num))
        return result

    @classmethod
    def precise_subtraction(cls, *args):
        if len(args) == 0:
            raise ValueError(INVALID_ARGUMENT_FOR_ARITHMETIC_OPR + " subtraction")
        result = args[0]
        for num in args[1:]:
            result = Decimal(str(result)) - Decimal(str(num))
        return result

    @classmethod
    def precise_multiplication(cls, *args):
        if len(args) == 0:
            raise ValueError(INVALID_ARGUMENT_FOR_ARITHMETIC_OPR + " subtraction")
        result = args[0]
        for num in args[1:]:
            result = Decimal(str(result)) * Decimal(str(num))
        return result

    @classmethod
    def precise_division(cls, a, b):
        return Decimal(str(a)) / Decimal(str(b))

    @classmethod
    def absolute_difference(cls, a, b):
        return abs(Decimal(str(a)) - Decimal(str(b)))

    @classmethod
    def get_absolute_value(cls, a):
        return abs(Decimal(str(a)))

