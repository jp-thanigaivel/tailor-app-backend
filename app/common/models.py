from datetime import datetime
from enum import Enum
from typing import Optional, Any, List
from pydantic import BaseModel, Field

# Enums
class UserStatusEnum(str, Enum):
    PENDING_VERIFICATION = 'PENDING_VERIFICATION'
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    BLOCKED = 'BLOCKED'

class CurrencyEnum(str, Enum):
    INR = 'INR'
    USD = 'USD'

class RoleEnum(str, Enum):
    ADMIN = 'admin'
    USER = 'user'
    CUSTOMER_SUPPORT = 'customerRep'

class TimeUnit(str, Enum):
    SECOND = "SECOND"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"

class AddressTypeEnum(str, Enum):
    PRIMARY = 'PRIMARY'
    OFFICE = 'OFFICE'
    SHIPPING = 'SHIPPING'
    BILLING = 'BILLING'

class UnitEnum(str, Enum):
    KG = 'KG'
    GM = 'GM'
    LTR = 'LTR'
    M3 = 'M3'

# Shared Sub-models
class UserName(BaseModel):
    first_name: str = Field(..., alias="firstName")
    middle_name: Optional[str] = Field(default=None, alias="middleName")
    last_name: Optional[str] = Field(default=None, alias="lastName")

    class Config:
        populate_by_name = True
        use_enum_values = True

class PhoneNumber(BaseModel):
    country_code: int = Field(..., alias="countryCode", ge=1, le=999)
    phone_number: str = Field(..., alias="phoneNumber", min_length=10, max_length=10)

    class Config:
        populate_by_name = True

class Address(BaseModel):
    id: str = Field(default="1", alias="id")
    address_type: AddressTypeEnum = Field(default=AddressTypeEnum.PRIMARY, alias="addressType")
    address_line_1: str = Field(..., alias="addressLine1")
    address_line_2: Optional[str] = Field(None, alias="addressLine2")
    address_line_3: Optional[str] = Field(None, alias="addressLine3")
    city: str = Field(..., alias="city")
    district: str = Field(..., alias="district")
    state: str = Field(..., alias="state")
    country: str = Field(..., alias="country")
    postal_code: int = Field(default=0, alias="postal_code")
    phone_number: Optional[PhoneNumber] = Field(None, alias='phoneNumber')

    class Config:
        populate_by_name = True

# Base Mongo Model
class BaseMongoModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    org_id: str = Field(..., alias="orgId")
    business_unit_id: str = Field(..., alias="businessUnitId")
    owner_id: str = Field(..., alias="ownerId")
    created_on: str = Field(..., alias="createdOn")
    updated_on: str = Field(..., alias="updatedOn")
    created_by: str = Field(..., alias="createdBy")
    updated_by: str = Field(..., alias="updatedBy")

    class Config:
        populate_by_name = True
        use_enum_values = True

# Response Models
class StatusResponse(BaseModel):
    statusCode: str
    statusType: str
    statusDesc: Optional[str] = None

class TokenData(BaseModel):
    user_id: str
    org_id: str
    user_roles: List[str]
    expiry: float

    class Config:
        populate_by_name = True

class Money(BaseModel):
    price: float = Field(..., alias='price')
    currency: CurrencyEnum = Field(..., alias='currency')

    class Config:
        populate_by_name = True
        use_enum_values = True

class Quantity(BaseModel):
    qty: float = Field(..., gt=0, alias="qty")
    unit: UnitEnum = Field(..., alias="unit")

    class Config:
        populate_by_name = True
        use_enum_values = True

class TimeQuantity(BaseModel):
    qty: int = Field(..., alias="qty")
    unit: TimeUnit = Field(..., alias="unit")

    class Config:
        populate_by_name = True
        use_enum_values = True

class DBPaginationMeta(BaseModel):
    cursor: Optional[str]
    sort_key: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int]
    filter_condition: Optional[dict]
    sort_condition: Optional[list]
    is_backward: bool = False

    class Config:
        populate_by_name = True

class AppDTO(BaseModel):
    auth: TokenData = Field(...)
    request_data: Any = Field(...)
    response_data: Any = Field(None)

    class Config:
        populate_by_name = True

class Pagination(BaseModel):
    count: Optional[int]
    nextPage: Optional[str] = None
    previousPage: Optional[str] = None
    totalCount: Optional[int]

class APIResponse(BaseModel):
    status: StatusResponse
    data: Any
