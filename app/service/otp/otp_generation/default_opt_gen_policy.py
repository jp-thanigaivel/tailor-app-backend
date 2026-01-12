import logging
import math
import random

from starlette import status

from app.interface.application_interface import OtpGenerationInterface
from app.utils.app_constant import STATUS_TYPE_ERROR
from app.core.exceptions import OtpGenerationException
from app.utils.common_functions import DateUtils
from app.utils.otp_constant import KEY_N_OTP_EXPIRY_TIME

logger = logging.getLogger(__name__)


class DefaultOtpGen(OtpGenerationInterface):
    def process_data(self, request_dict) -> str:
        db_expiry_value = request_dict.get(KEY_N_OTP_EXPIRY_TIME)
        if db_expiry_value:
            logger.info("Check for existing db_expiry_time")
            current_time = DateUtils.get_current_datetime()
            diff_seconds = DateUtils.get_diff_sec(db_expiry_value, current_time)
            logger.info("diff_seconds {} db_expiry_value {} current_time {} ".format(str(diff_seconds),
                                                                                     str(db_expiry_value),
                                                                                     str(current_time)))
            if int(diff_seconds) > 0:
                logger.warning("diff_seconds {} db_expiry_value {} current_time {} "
                               "Not allow found existing otp active try after".format(str(diff_seconds),
                                                                                      str(db_expiry_value),
                                                                                      str(current_time)))
                raise OtpGenerationException(status.HTTP_400_BAD_REQUEST, STATUS_TYPE_ERROR,
                                             "Not allow found existing otp active try after {} Seconds"
                                             .format(str(int(diff_seconds))))
        random_str = ""
        for i in range(6):
            index = math.floor(random.random() * 10)
            random_str += str(index)
        return random_str
