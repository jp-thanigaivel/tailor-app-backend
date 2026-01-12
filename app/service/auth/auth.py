import logging
from datetime import datetime

from jose import JWTError
from jose.exceptions import JWTClaimsError, ExpiredSignatureError
from pydantic import ValidationError
from starlette import status

from app.config import app_secret
from app.core.config import settings as app_config
from app.core.logging_context import MDC
from app.config.app_secret import AuthConfig
from app.common.models import TokenData
from app.models.otp import OTPRequest, OTPDetailResponse, VerifyOTP
from app.common.models import ROLES, User, UserLogin, UserOTPRequest
from app.service.database.database import MongoDBOperations
from app.service.otp.otp_utils import generate_otp, verify_otp_service
from app.utils.app_constant import COLL_TODO_USER, STATUS_DESC_INVALID_CREDENTIAL, STATUS_TYPE_ERROR, \
    LOG_CTX_UNIQ_TNX_KEY, STATUS_DESC_USR_NOT_ACTIVE, RES_C_KEY_DATA, \
    STATUS_DESC_AUTH_TOKEN_REQUIRED, \
    STATUS_DESC_AUTH_TOKEN_EXPIRED, STATUS_DESC_AUTH_INVALID_ACCESS_TYPE, STATUS_DESC_AUTH_INVALID_ROLE, \
    STATUS_DESC_USR_NOT_EXIST, STATUS_DESC_AUTH_TOKEN_INVALID_INFO, \
    STATUS_DESC_AUTH_NOT_AUTHORIZED_FOR_ACTION, STATUS_DESC_AUTH_INVALID_TOKEN, STATUS_DESC_NOT_ALLOWED
from app.core.exceptions import AuthorizeException, NotAllowedException
from app.utils.app_obj_mapper import AppObjectMapper
from app.utils.auth_constant import KEY_ACCESS_TOKEN, KEY_ACCESS_TOKEN_TYPE, KEY_REFRESH_TOKEN
from app.utils.common_functions import CommonUtils, CalculateUtils
from app.utils.user_constant import KEY_PHONE_NUMBER

logger = logging.getLogger(__name__)
auth_config: AuthConfig = app_secret.app_secret.auth_config
ACCESS_SECRET_KEY = auth_config.access_secret_key
REFRESH_SECRET_KEY = auth_config.refresh_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = auth_config.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = auth_config.refresh_token_expire_minutes
VALUE_ACCESS_TOKEN_TYPE = auth_config.access_token_type


def generate_user_otp(user_login: UserOTPRequest):
    logger.info("Start processing generate_user_otp")
    phone_number = user_login.phone_number
    password = user_login.password
    logger.info("Start Processing generate_user_otp phone_number {}".format(str(phone_number)))
    MDC.put(LOG_CTX_UNIQ_TNX_KEY, str(phone_number))

    logger.info("authenticate_user")
    user_dict = __authenticate_user(phone_number, password)
    user: User = __get_user_obj(user_dict)
    otp_request: OTPRequest = AppObjectMapper.get_default_otp_request(str(user.phone_number),
                                                                      user.org_id, user.owner_id)
    logger.info("user authenticated generate_otp for user")
    otp_response: OTPDetailResponse = generate_otp(otp_request)
    return otp_response.model_dump(by_alias=True, exclude_unset=True, mode='json')


def verify_user_otp(verify_otp_request: VerifyOTP):
    logger.info("Verify user otp {}".format(str(verify_otp_request.otp_key)))
    is_active = verify_otp_service(verify_otp_request)
    phone_number = verify_otp_request.otp_key
    logger.info("OTP is valid for {}".format(str(phone_number)))
    user_dict = __get_user_detail(int(phone_number))
    logger.info("create_access_token {}".format(str(phone_number)))
    access_token = __create_access_token(user_dict, ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = __create_refresh_token(user_dict, REFRESH_TOKEN_EXPIRE_MINUTES)
    logger.info("return access token")
    return {KEY_ACCESS_TOKEN: access_token, KEY_REFRESH_TOKEN: refresh_token,
            KEY_ACCESS_TOKEN_TYPE: VALUE_ACCESS_TOKEN_TYPE}


def process_sign_request(user_login: UserLogin):
    logger.info("Start processing sign_request")
    phone_number = user_login.phone_number
    password = user_login.password
    logger.info("Start Processing sign_request phone_number {}".format(str(phone_number)))
    MDC.put(LOG_CTX_UNIQ_TNX_KEY, str(phone_number))

    logger.info("authenticate_user")
    user_dict = __authenticate_user(phone_number, password)

    logger.info("create_access_token")
    access_token = __create_access_token(user_dict, ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = __create_refresh_token(user_dict, REFRESH_TOKEN_EXPIRE_MINUTES)

    logger.info("return access token")
    return {KEY_ACCESS_TOKEN: access_token, KEY_REFRESH_TOKEN: refresh_token,
            KEY_ACCESS_TOKEN_TYPE: VALUE_ACCESS_TOKEN_TYPE}


def check_user_authorize_oauth_2(request_header):
    logger.info("In check_user_authorize_oauth_2")
    bearer_token = request_header.get("Authorization")
    if bearer_token is None:
        logger.warning("Authorization header required")
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_TOKEN_REQUIRED)

    logger.info("received bearer_token")
    try:
        auth_scheme, token = bearer_token.split(None, 1)
    except Exception as exp:
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_INVALID_TOKEN)

    # Check for Bearer Type
    if auth_scheme.lower() != VALUE_ACCESS_TOKEN_TYPE:
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_INVALID_TOKEN)
    try:
        decoded_token_data = CommonUtils.decode_jwt_token(token, ACCESS_SECRET_KEY)
    except (JWTError, ExpiredSignatureError, JWTClaimsError) as exp:
        logger.error("Invalid Token  error_messages {}".format(str(exp)))
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_INVALID_TOKEN)

    try:
        token_data: TokenData = CommonUtils.decode_default_token_data(decoded_token_data)
    except ValidationError as exp:
        logger.warning("ValidationError : Invalid token no required information")
        error_messages = str([{"loc": error["loc"], "msg": error["msg"]} for error in exp.errors()])
        logger.error("ValidationError  error_messages {}".format(str(error_messages)))
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_TOKEN_INVALID_INFO)

    expiry = token_data.expiry
    current_time = datetime.utcnow().timestamp()
    logger.info("Check token expiry current_time {}".format(str(current_time)))
    if expiry is not None and expiry < float(str(current_time)):
        logger.warning("token expired expires {} current_time {}".format(str(expiry), str(current_time)))
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_TOKEN_EXPIRED)

    logger.info("user authorized")
    return token_data


def check_user_resource_authorize_oauth_2(token_data: TokenData, resource, action):
    user_id = token_data.user_id
    org_id = token_data.org_id
    roles = token_data.user_roles
    expiry = token_data.expiry

    logger.info("Received roles {} resource {} action {}".format(str(roles), str(resource), str(action)))

    for role in roles:
        logger.debug("Check role {} ".format(str(role)))
        # Later change to DB/Cache call
        configured_role = ROLES.get(role)
        if configured_role:
            logger.info("Found configured role {}".format(str(role)))
            configured_resource = configured_role.get(resource)
            if configured_resource:
                logger.info("Found configured resource {}".format(str(resource)))
                access_type = configured_resource.get('accessScope')
                access_action = configured_resource.get('accessLevel')
                if action in access_action:
                    logger.info("Found configured action {}".format(str(action)))
                    if access_type == 'own':
                        return {'owner_id': user_id, 'org_id': org_id}
                    elif access_type == 'all':
                        return {'org_id': org_id}
                    logger.error("Invalid access_type configured {} should be {}/{}".format(str(access_type),
                                                                                            str('own'),
                                                                                            str(all)))
                    raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                             STATUS_DESC_AUTH_INVALID_ACCESS_TYPE)
                else:
                    logger.error("STATUS_DESC_AUTH_NOT_AUTHORIZED_FOR_ACTION Required action {} not found in "
                                 "configuration".format(str(action)))
                    raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                             STATUS_DESC_AUTH_NOT_AUTHORIZED_FOR_ACTION
                                             + " " + str(action)
                                             # + " on resource " + str(resource)
                                             )
    logger.error("Invalid role or action")
    logger.error(
        "No role/action found for given (token)roles {} resource {} action {}".format(str(roles), str(resource),
                                                                                      str(action)))
    raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                             STATUS_DESC_AUTH_INVALID_ROLE)


def refresh_access_token_oauth_2(request_header):
    logger.info("In refresh_access_token_oauth_2")
    bearer_token = request_header.get("Authorization")
    if bearer_token is None:
        logger.warning("Authorization header required")
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_TOKEN_REQUIRED)

    logger.info("received bearer_token")
    try:
        auth_scheme, token = bearer_token.split(None, 1)
    except Exception as exp:
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_INVALID_TOKEN)

    # Check for Bearer Type
    if auth_scheme.lower() != VALUE_ACCESS_TOKEN_TYPE:
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_INVALID_TOKEN)
    decoded_token_data = CommonUtils.decode_jwt_token(token, REFRESH_SECRET_KEY)

    try:
        token_data: TokenData = CommonUtils.decode_default_token_data(decoded_token_data)
    except ValidationError as exp:
        logger.warning("ValidationError : Invalid token no required information")
        error_messages = str([{"loc": error["loc"], "msg": error["msg"]} for error in exp.errors()])
        logger.error("ValidationError  error_messages {}".format(str(error_messages)))
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_TOKEN_INVALID_INFO)

    expiry = token_data.expiry
    current_time = datetime.utcnow().timestamp()
    time_diff = CalculateUtils.precise_subtraction(expiry, current_time)
    logger.info("Check token token_expiry {} current_time {} time_diff {}"
                .format(str(expiry), str(current_time), str(time_diff)))
    if expiry < float(str(current_time)):
        logger.warning("token expired expires {} current_time {}".format(str(expiry), str(current_time)))
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_TOKEN_EXPIRED)

    # Check time difference is less than CONFIGURED TIME
    to_seconds = CalculateUtils.precise_multiplication(REFRESH_TOKEN_EXPIRE_MINUTES, 60)
    if float(time_diff) < float(to_seconds):
        logger.warning("time difference {} cannot be greater than configured value to_seconds {}"
                       .format(str(time_diff), str(to_seconds)))
        raise NotAllowedException(status.HTTP_400_BAD_REQUEST, STATUS_TYPE_ERROR, STATUS_DESC_NOT_ALLOWED
                                  + " token refresh. Since token valid for {} Minutes".format(
            str(int(to_seconds / 60))))

    logger.info("user authorized to refresh access token")
    token_data_dict = token_data.model_dump(exclude_none=True)
    access_token = __create_access_token(token_data_dict, ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = __create_refresh_token(token_data_dict, REFRESH_TOKEN_EXPIRE_MINUTES)

    logger.info("return access token")
    return {KEY_ACCESS_TOKEN: access_token, KEY_REFRESH_TOKEN: refresh_token,
            KEY_ACCESS_TOKEN_TYPE: VALUE_ACCESS_TOKEN_TYPE}


#####
# WARNING BELOW METHODS ONLY FOR INTERNAL USE
#####

def __create_access_token(user_dict, duration_in_min):
    payload = CommonUtils.get_default_token_data(user_dict, duration_in_min)
    encoded_jwt = CommonUtils.create_jwt_token(payload, ACCESS_SECRET_KEY)
    return encoded_jwt


def __create_refresh_token(user_dict, duration_in_min):
    payload = CommonUtils.get_default_token_data(user_dict, duration_in_min)
    encoded_jwt = CommonUtils.create_jwt_token(payload, REFRESH_SECRET_KEY)
    return encoded_jwt


def __authenticate_user(phone_number, password):
    logger.info("In authenticate_user with phone_number {}".format(str(phone_number)))
    user_dict = __get_user_detail(phone_number)
    is_active = user_dict.get("is_active")
    if not is_active:
        logger.warning("No User not active with phone_number {}".format(str(phone_number)))
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_USR_NOT_ACTIVE)

    hashed_password = user_dict.get("password")
    logger.info("Check password")

    is_matched = CommonUtils.verify_password(password, hashed_password)
    logger.info("is password matched {}".format(str(is_matched)))
    if is_matched:
        logger.info("User credentials matched")
        return user_dict
    else:
        logger.error("Invalid Credentials")
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_INVALID_CREDENTIAL)


def __get_user_detail(phone_number):
    logger.info("In __user_detail with phone_number {}".format(str(phone_number)))

    logger.info("Check user existence phone_number {}".format(str(phone_number)))
    db_name = app_config.data_base
    db_coll = COLL_TODO_USER
    query = CommonUtils.get_query({KEY_PHONE_NUMBER: phone_number})
    db_response = MongoDBOperations.find_document(db_name=db_name, db_coll=db_coll, filter_condition=query)
    db_response_data = db_response[RES_C_KEY_DATA]

    logger.debug("After db_response_data {}".format(str(db_response_data)))
    if db_response_data and len(db_response_data) > 0:
        logger.info("Found {} user".format(str(db_response_data)))
        user_dict = db_response_data[0]
        is_active = user_dict.get("is_active")
        if not is_active:
            logger.warning("No User not active with phone_number {}".format(str(phone_number)))
            raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                     STATUS_DESC_USR_NOT_ACTIVE)

        return user_dict
    else:
        logger.warning("No User found with phone_number {}".format(str(phone_number)))
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_USR_NOT_EXIST)


def __get_user_obj(user_dict) -> User:
    return User(**user_dict)