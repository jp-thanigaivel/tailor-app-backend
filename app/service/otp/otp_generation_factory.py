import logging
from datetime import datetime

from starlette import status

from app.models.otp import OtpGenerationPolicyId
from app.service.otp.otp_generation.default_opt_gen_policy import DefaultOtpGen
from app.utils.app_constant import STATUS_TYPE_ERROR, STATUS_DESC_NOT_IMPLEMENTED
from app.core.exceptions import NotImplementedException, InvalidException
from app.utils.otp_constant import KEY_N_OTP_EXPIRY_TIME

logger = logging.getLogger(__name__)


class OtpGenPolicyFactory:
    def __init__(self):
        self.default_otp_gen = DefaultOtpGen()

    def get_otp_policy_impl(self, otp_policy_gen):
        logger.info("In get_otp_policy_impl {}".format(str(otp_policy_gen)))
        match otp_policy_gen:
            case OtpGenerationPolicyId.DEFAULT.value:
                return self.default_otp_gen
            case default:
                raise NotImplementedException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                              STATUS_DESC_NOT_IMPLEMENTED
                                              + " otp_policy_gen:" + str(otp_policy_gen))


otp_gen_policy_factory: OtpGenPolicyFactory = OtpGenPolicyFactory()


def get_otp_value(otp_generation_policy_id: str, db_otp_expiry_time: datetime) -> str:
    logger.info("In get_otp_value {}".format(str(otp_generation_policy_id)))
    policy_gen = otp_gen_policy_factory.get_otp_policy_impl(otp_generation_policy_id)
    otp_policy_gen_request = {KEY_N_OTP_EXPIRY_TIME: db_otp_expiry_time}
    generated_otp = policy_gen.process_data(otp_policy_gen_request)
    if generated_otp is None:
        logger.error("otp value is none ")
        raise InvalidException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                               (" no otp:" + str(otp_generation_policy_id)))
    logger.info("otp generated")
    return generated_otp
