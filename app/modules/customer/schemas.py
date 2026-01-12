from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from app.common.models import Address, PhoneNumber
from app.constants.customer import CustomerBizTypeEnum

class CustomerBase(BaseModel):
    customer_name: str = Field(..., min_length=1, alias='customerName')
    customer_biz_type: CustomerBizTypeEnum = Field(..., alias='customerBizType')
    customer_address: Optional[Address] = Field(default=None, alias='customerAddress')
    customer_email_id: Optional[EmailStr] = Field(None, alias='customerEmailId')
    phone_number: PhoneNumber = Field(..., alias='phoneNumber')

    class Config:
        populate_by_name = True
        use_enum_values = True

class CreateCustomerRequest(CustomerBase):
    pass

class UpdateCustomerRequest(BaseModel):
    customer_name: Optional[str] = Field(None, alias='customerName')
    customer_biz_type: Optional[CustomerBizTypeEnum] = Field(None, alias='customerBizType')
    customer_address: Optional[Address] = Field(None, alias='customerAddress')
    customer_email_id: Optional[EmailStr] = Field(None, alias='customerEmailId')
    phone_number: Optional[PhoneNumber] = Field(None, alias='phoneNumber')

    class Config:
        populate_by_name = True
        use_enum_values = True

class CustomerResponse(CustomerBase):
    customer_id: str = Field(..., alias='customerId')
    id: Optional[str] = Field(None, alias='id')
