from datetime import datetime

from pydantic import Field

from app.constants.marketing import ConcreteGrade, PlacingMode, PlacingType, MarketingOrderStatus
from app.common.models import CreateEntity, Quantity, Money, PhoneNumber


class Marketing(CreateEntity):
    id: str = Field(default=None, alias="id")
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
    order_status: MarketingOrderStatus = Field(default=MarketingOrderStatus.PENDING.value, alias='orderStatus')
    contact_phone_number: PhoneNumber = Field(..., alias='phoneNumber')

    class Config:
        populate_by_name = True
        use_enum_values = True