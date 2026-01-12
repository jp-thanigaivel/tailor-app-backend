from typing import Optional
from pydantic import Field, EmailStr
from app.common.models import BaseMongoModel, Address, PhoneNumber
from app.constants.customer import CustomerBizTypeEnum

class Customer(BaseMongoModel):
    customer_id: str = Field(..., alias='customerId')
    customer_name: str = Field(..., min_length=1, alias='customerName')
    customer_biz_type: CustomerBizTypeEnum = Field(..., alias='customerBizType')
    customer_address: Optional[Address] = Field(default=None, alias='customerAddress')
    customer_email_id: Optional[EmailStr] = Field(default=None, alias='customerEmailId')
    phone_number: PhoneNumber = Field(..., alias='phoneNumber')

    class Config:
        populate_by_name = True
        use_enum_values = True
