import logging
from datetime import datetime
from enum import Enum

from pydantic import Field, BaseModel

from app.common.models import Quantity, TimeQuantity

logger = logging.getLogger(__name__)


class OtpGenerationPolicyId(str, Enum):
    DEFAULT = "default"


class OTPGenPolicy(BaseModel):
    otp_generation_policy_id: OtpGenerationPolicyId = Field(..., alias="otpGenerationPolicyId")
    default_expiry_time: Quantity = Field(..., alias="defaultExpiryTime")

    class Config:
        populate_by_name = True
        use_enum_values = True


class OTPRequest(BaseModel):
    otp_key: str = Field(..., alias="otpKey")
    otp_generation_policy: OtpGenerationPolicyId = Field(default=OtpGenerationPolicyId.DEFAULT,
                                                         alias="otpGenerationPolicy")
    otp_expiry_time_unit: TimeQuantity = Field(..., alias="otpExpiryTimeUnit")

    class Config:
        populate_by_name = True
        use_enum_values = True


class OTPDetail(BaseModel):
    id: str = Field(default=None, alias="id")
    otp_key: str = Field(..., alias="otpKey")
    otp_value: str = Field(None, alias="otpValue")
    otp_expiry_time: datetime = Field(..., alias="otpExpiryTime")

    class Config:
        populate_by_name = True
        use_enum_values = True


class OTPDetailResponse(BaseModel):
    otp_key: str = Field(..., alias="otpKey")
    otp_value: str = Field(..., alias="otpValue")
    otp_expiry_time: datetime = Field(..., alias="otpExpiryTime")

    class Config:
        populate_by_name = True
        use_enum_values = True


class VerifyOTP(BaseModel):
    otp_key: str = Field(..., alias="otpKey")
    otp_value: str = Field(..., alias="otpValue")

    class Config:
        populate_by_name = True
        use_enum_values = True
