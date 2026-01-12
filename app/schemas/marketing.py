from datetime import datetime

from pydantic import Field
from typing_extensions import Optional

from app.constants.marketing import MarketingOrderStatus, ConcreteGrade, PlacingMode, PlacingType
from app.common.models import PhoneNumber, Money, Quantity
from app.common.models import CreateSchema


class CreateMarketingRequest(CreateSchema):
    enquiry_date: datetime = Field(..., alias='enquiryDate')
    site_location: str = Field(..., alias='siteLocation')
    customer_id: str = Field(..., alias="customerId")
    concrete_grade: ConcreteGrade = Field(..., alias='concreteGrade')
    qty: Quantity = Field(..., alias='qty')
    placing_mode: PlacingMode = Field(..., alias='placingMode')
    placing_type: PlacingType = Field(..., alias='placingType')
    unit_price: Money = Field(..., alias='unitPrice')
    commited_date: datetime = Field(..., alias='commitedDate')
    contact_phone_number: PhoneNumber = Field(..., alias='phoneNumber')


class CreateMarketingResponse(CreateSchema):
    marketing_id: str = Field(..., alias="marketingId")

class GetMarketingResponse(CreateSchema):
    marketing_id: str = Field(..., alias="marketingId")
    customer_id: str = Field(..., alias="customerId")
    enquiry_date: datetime = Field(..., alias='enquiryDate')
    site_location: str = Field(..., alias='siteLocation')
    concrete_grade: ConcreteGrade = Field(..., alias='concreteGrade')
    qty: Quantity = Field(..., alias='qty')
    placing_mode: PlacingMode = Field(..., alias='placingMode')
    placing_type: PlacingType = Field(..., alias='placingType')
    unit_price: Money = Field(..., alias='unitPrice')
    commited_date: datetime = Field(..., alias='commitedDate')
    order_status: MarketingOrderStatus = Field(..., alias='orderStatus')
    contact_phone_number: PhoneNumber = Field(..., alias='phoneNumber')

class UpdateMarketingRequest(CreateSchema):
    marketing_id: str = Field(..., alias="marketingId")
    customer_id: str = Field(None, alias="customerId")
    site_location: Optional[str] = Field(None, alias='siteLocation')
    concrete_grade: Optional[ConcreteGrade] = Field(None, alias='concreteGrade')
    qty: Optional[Quantity] = Field(None, alias='qty')
    placing_mode: Optional[PlacingMode] = Field(None, alias='placingMode')
    placing_type: Optional[PlacingType] = Field(None, alias='placingType')
    unit_price: Optional[Money] = Field(None, alias='unitPrice')
    commited_date: Optional[datetime] = Field(None, alias='commitedDate')
    order_status: Optional[MarketingOrderStatus] = Field(None, alias='orderStatus')
    contact_phone_number: Optional[PhoneNumber] = Field(None, alias='phoneNumber')

class UpdateMarketingResponse(CreateSchema):
    marketing_id: str = Field(..., alias="marketingId")