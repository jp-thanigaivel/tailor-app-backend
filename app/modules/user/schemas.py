from typing import Optional, List
from pydantic import BaseModel, Field
from app.common.models import UserName, RoleEnum, UserStatusEnum, CurrencyEnum
from app.common.models import Address

class UserBase(BaseModel):
    user_name: UserName = Field(..., alias='userName')
    phone_number: int = Field(..., alias='phoneNumber')
    alt_phone_number: Optional[int] = Field(None, alias='altPhoneNumber')
    email_id: Optional[str] = Field(None, alias='emailId')
    address: Optional[List[Address]] = Field(None, alias='address')
    user_currency: CurrencyEnum = Field(default=CurrencyEnum.INR, alias='userCurrency')

    class Config:
        populate_by_name = True

class UserCreate(UserBase):
    password: str = Field(..., alias='password')

class UserUpdate(BaseModel):
    user_name: Optional[UserName] = Field(None, alias='userName')
    phone_number: Optional[int] = Field(None, alias='phoneNumber')
    alt_phone_number: Optional[int] = Field(None, alias='altPhoneNumber')
    email_id: Optional[str] = Field(None, alias='emailId')
    address: Optional[List[Address]] = Field(None, alias='address')
    user_currency: Optional[CurrencyEnum] = Field(None, alias='userCurrency')
    is_active: Optional[UserStatusEnum] = Field(None, alias='isActive')
    user_roles: Optional[List[RoleEnum]] = Field(None, alias='userRoles')

    class Config:
        populate_by_name = True

class UserResponse(UserBase):
    user_id: str = Field(..., alias='userId')
    is_active: UserStatusEnum = Field(..., alias='isActive')
    user_roles: List[RoleEnum] = Field(..., alias='userRoles')

class UserLogin(BaseModel):
    phone_number: int = Field(..., alias='phoneNumber')
    password: str = Field(..., alias='password')

class UserOTPRequest(BaseModel):
    phone_number: int = Field(..., alias='phoneNumber')
    password: str = Field(..., alias='password')

