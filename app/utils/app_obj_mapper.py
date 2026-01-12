import hashlib
import logging

from pydantic import BaseModel
from typing_extensions import Any, Type

from app.core.config import get_app_secret
from app.constants.database import CreateEntityModelKeyEnum
from app.common.models import (
    StatusResponse, Pagination, Quantity, Money, TimeQuantity,
    TimeUnit, TokenData, DBPaginationMeta, BaseMongoModel
)
from app.models.otp import OTPRequest, OtpGenerationPolicyId
from app.utils.app_constant import (
    RESOURCE_DB_OWNER_ID, RESOURCE_DB_ORG_ID,
    RESOURCE_DB_CREATED_ON, RESOURCE_DB_CREATED_BY, REQUEST_CURSOR, REQUEST_SORT, REQUEST_PAGE, REQUEST_LIMIT,
    DOC_OBJ_ID, PY_OBJ_ID
)
from app.utils.common_functions import DateUtils, CommonUtils

logger = logging.getLogger(__name__)


class AppObjectMapper:
    @classmethod
    def get_status_obj(cls, status_code, status_type, status_desc):
        status = StatusResponse(statusCode=str(status_code), statusType=status_type, statusDesc=status_desc)
        return status.model_dump()

    @classmethod
    def get_pagination_obj(cls, count, previous_page, next_page, total_count=None):
        pagination_obj = Pagination(count=count, previousPage=previous_page, nextPage=next_page, totalCount=total_count)
        return pagination_obj.model_dump()

    @classmethod
    def get_response_obj(cls, status, data, paginated_object=None):
        response = {"status": status, "data": data}
        if paginated_object is not None:
            response["paginationInfo"] = paginated_object
        return response

    @classmethod
    def get_model_dict_with_default_fields_for_create(cls, req_model: BaseModel, token_data: TokenData) -> dict[str, Any]:
        req_dict: dict[str, Any] = req_model.model_dump(by_alias=True, exclude_unset=True, mode='json')
        req_dict: dict[str, Any] = cls.set_default_rbac_fields(req_dict, token_data)
        req_dict: dict[str, Any] = cls.set_default_trans_fields(req_dict, token_data, True)
        return req_dict

    @classmethod
    def set_default_rbac_fields(cls,  req_dict: dict[str, Any], token_data: TokenData) -> dict[str, Any]:
        req_dict[CreateEntityModelKeyEnum.ORG_ID.value] = token_data.org_id
        req_dict[CreateEntityModelKeyEnum.BUSINESS_UNIT_ID.value] = token_data.org_id
        req_dict[CreateEntityModelKeyEnum.OWNER_ID.value] = token_data.user_id
        return req_dict

    @classmethod
    def update_db_model_from_schema(cls, db_model_obj: BaseMongoModel, update_req: BaseModel,
                                    token_data: TokenData) -> BaseMongoModel:
        update_data = update_req.model_dump(by_alias=False, exclude_unset=True, mode='json')
        for field, value in update_data.items():
            setattr(db_model_obj, field, value)
        db_model_obj.updated_by = token_data.user_id
        db_model_obj.updated_on = DateUtils.get_system_datetime_string()
        return db_model_obj

    @classmethod
    def set_default_trans_fields(cls, req_dict: dict[str, Any], token_data: TokenData, is_create) -> dict[str, Any]:
        current_date_time = DateUtils.get_system_datetime_string()
        user_id = token_data.user_id
        if is_create:
            req_dict[CreateEntityModelKeyEnum.CREATED_BY.value] = user_id
            req_dict[CreateEntityModelKeyEnum.CREATED_ON.value] = current_date_time
        req_dict[CreateEntityModelKeyEnum.UPDATED_BY.value] = user_id
        req_dict[CreateEntityModelKeyEnum.UPDATED_ON.value] = current_date_time
        return req_dict

    @classmethod
    def get_db_meta(cls, query_param: dict[str, Any], allowed_filter: dict[str, Any], allowed_sort: dict[str, Any]) -> DBPaginationMeta:
        cursor = query_param.get(REQUEST_CURSOR)
        sort_key = query_param.get(REQUEST_SORT)
        page_number = int(query_param.get(REQUEST_PAGE)) if query_param.get(REQUEST_PAGE) else None
        page_size = int(query_param.get(REQUEST_LIMIT)) if query_param.get(REQUEST_LIMIT) else None
        filter_condition = CommonUtils.get_query_filter_condition(allowed_filter, query_param)
        sort_condition = CommonUtils.get_query_sort_condition(query_param, allowed_sort)
        return DBPaginationMeta(cursor=cursor, sort_key=sort_key, page_number=page_number, page_size=page_size,
                                filter_condition=filter_condition, sort_condition=sort_condition)

    @classmethod
    def get_model_dict_for_list(cls,  db_document: list[dict[str, Any]], model_class: Type[BaseModel]) -> list[
        dict[str, Any]]:
        model_list = []
        for each_db_document in db_document:
            doc_id = str(each_db_document[DOC_OBJ_ID])
            each_db_document[PY_OBJ_ID] = doc_id
            logger.debug("each_db_document {}".format(str(each_db_document)))

            logger.info("converting to py-obj for doc_id {}".format(str(doc_id)))
            model_res = AppObjectMapper.convert_to_model(model_class, each_db_document)
            model_json = AppObjectMapper.get_model_json(model_res)
            logger.debug("converted to py-obj customer_json {}".format(str(model_json)))
            model_list.append(model_json)
        logger.info("returning list of model")
        return model_list

    @classmethod
    def get_model_json(cls, db_model_obj:BaseModel) -> dict[str, Any]:
        return db_model_obj.model_dump(by_alias=True, exclude_unset=True, mode='json')

    @classmethod
    def get_model_dict_for_one(cls, db_document: dict[str, Any], model_class: Type[BaseModel]) -> dict[str, Any]:
        try:
            model_res = AppObjectMapper.convert_to_model(model_class, db_document)
            model_json = AppObjectMapper.get_model_json(model_res)
            return model_json
        except Exception as e:
            raise

    @classmethod
    def convert_to_model(cls, model_class: Type[BaseModel], data: dict[str, Any]) -> BaseModel:
        try:
            model_instance = model_class(**data)
            return model_instance
        except Exception as e:
            raise

    @classmethod
    def copy_default_trans_fields_from_parent(cls, parent_object, update_object):
        update_object[RESOURCE_DB_CREATED_BY] = parent_object[RESOURCE_DB_CREATED_BY]
        update_object[RESOURCE_DB_CREATED_ON] = parent_object[RESOURCE_DB_CREATED_ON]
        update_object[RESOURCE_DB_ORG_ID] = parent_object[RESOURCE_DB_ORG_ID]
        update_object[RESOURCE_DB_OWNER_ID] = parent_object[RESOURCE_DB_OWNER_ID]
        return update_object

    @classmethod
    def get_obj_qty(cls, qty, unit):
        return Quantity(qty=qty, unit=unit)

    @classmethod
    def get_obj_money(cls, price, currency):
        return Money(price=price, currency=currency)

    @classmethod
    def get_dict_money(cls, price, currency):
        return {"price": price, "currency": currency}

    @classmethod
    def get_conv_id(cls, product_id, stock_id):
        return str(product_id) + str("|") + str(stock_id)

    @classmethod
    def get_conv_unit(cls, from_unit, to_unit):
        return str(from_unit) + str("|") + str(to_unit)

    @classmethod
    def get_multiple_document(cls, db_name, db_coll, doc_name, document_entity):
        return {
            'db_name': db_name,
            'db_coll': db_coll,
            'doc_name': doc_name,
            'document_entity': document_entity
        }

    @classmethod
    def get_razorpay_create_order(cls, amount: Money, order_id, partial_payment=False, order_notes: dict = None):
        create_order = {
            'amount': (amount.price * 100),
            'currency': amount.currency,
            'receipt': order_id,
            'partial_payment': partial_payment
        }
        if order_notes:
            create_order.update({'notes': order_notes})
        return create_order

    @classmethod
    def get_phonepe_create_order_json(cls, amount: Money, order_id, merchant_id, redirect_url, callback_url):
        pay_page_request = {
            "merchantId": merchant_id,
            "merchantTransactionId": CommonUtils.get_uniqueid_str(),
            "merchantUserId": CommonUtils.get_uniqueid_str(),
            "amount": int(amount.price * 100),
            "callbackUrl": callback_url,
            "redirectUrl": redirect_url,
            "redirectMode": "REDIRECT",
            "merchantOrderId": order_id,
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        return pay_page_request

    @classmethod
    def get_stripe_create_order_json(cls, amount: Money, order_id, success_url, cancel_url):
        session_request = {
            "client_reference_id": order_id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "mode": 'payment',
            "line_items": [
                {
                    'price_data': {
                        'currency': str(amount.currency.value),
                        'unit_amount': int(amount.price * 100),
                    }
                },
            ]
        }
        return session_request

    @classmethod
    def get_time_quantity_obj(cls, qty: int, unit: TimeUnit):
        return TimeQuantity(qty=qty, unit=unit)

    @classmethod
    def get_time_quantity_dict(cls, qty: int, unit: TimeUnit):
        return {"qty": qty, "unit": unit}

    @classmethod
    def get_default_otp_request(cls, otp_key, org_id, owner_id,
                                otp_expiry_time_unit=None) \
            -> OTPRequest:
        created_on = DateUtils.get_current_datetime()
        created_by = str(owner_id)
        if otp_expiry_time_unit is None:
            otp_expiry_time_unit = get_app_secret().otp_expiry_seconds
        otp_req = {"otp_key": otp_key,
                   "otp_generation_policy": OtpGenerationPolicyId.DEFAULT,
                   "otp_expiry_time_unit": AppObjectMapper.get_time_quantity_dict(otp_expiry_time_unit,
                                                                                  TimeUnit.SECOND),
                   "org_id": org_id,
                   "owner_id": str(owner_id),
                   "created_on": created_on,
                   "created_by": created_by,
                   "updated_on": created_on,
                   "updated_by": created_by
                   }
        return OTPRequest(**otp_req)

    @classmethod
    def get_otp_request(cls, org_id, owner_id, otp_generation_policy, otp_expiry_time_unit, **key_args) -> OTPRequest:
        otp_req = {"org_id": org_id, "owner_id": str(owner_id),
                   "otpGenerationPolicy": otp_generation_policy, "otpTemplateId": key_args,
                   "otp_expiry_time_unit": otp_expiry_time_unit}
        return OTPRequest(**otp_req)

    @classmethod
    def get_whatsapp_api_header(cls, token: str, token_type: str):
        return {"Authorization": (token_type + " " + token), "Content-Type": "application/json"}


    @classmethod
    def get_hash_sha512(cls, payload: str):
        to_ascii_string = payload
        to_sha512_string = to_ascii_string.encode("utf-8")
        sha512_string = hashlib.sha512(to_sha512_string).hexdigest()
        return sha512_string

    @classmethod
    def get_ease_buzz_initiate_payment_header(cls):
        return {"Content-Type": "application/x-www-form-urlencoded"}

    @classmethod
    def get_default_address_for_in_store_purchase(cls):
        req = {
                "addressLine1": "NA",
                "city": "NA",
                "district": "NA",
                "state": "NA",
                "country": "NA",
                "postal_code": 000000
            }
        return req
