from enum import Enum
from typing import Optional, Any
from pydantic import Field, BaseModel
from app.common.models import BaseMongoModel, UserStatusEnum, UserName, CurrencyEnum, RoleEnum
from app.common.models import Address

class User(BaseMongoModel):
    user_id: str = Field(default=None, alias='userId')
    user_name: UserName = Field(..., alias='userName')
    password: str = Field(..., alias='password')
    phone_number: int = Field(..., alias='phoneNumber')
    alt_phone_number: Optional[int] = Field(default=None, alias='altPhoneNumber')
    email_id: Optional[str] = Field(default=None, alias='emailId')
    address: Optional[list[Address]] = Field(None, alias='address')
    user_currency: CurrencyEnum = Field(default=CurrencyEnum.INR, alias='userCurrency')
    is_active: UserStatusEnum = Field(default=UserStatusEnum.ACTIVE, alias='isActive')
    user_roles: list[RoleEnum] = Field(default=[RoleEnum.USER], alias='userRoles')

    class Config:
        populate_by_name = True
        use_enum_values = True
