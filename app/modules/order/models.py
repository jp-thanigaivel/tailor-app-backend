from typing import List, Optional, Dict, Any
from app.common.models import PhoneNumber
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class OrderType(str, Enum):
    ENTERPRISE = "ENTERPRISE"
    INDIVIDUAL = "INDIVIDUAL"

class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    RECEIVED = "RECEIVED"
    STITCHING = "STITCHING"
    READY = "READY"
    DELIVERED = "DELIVERED"

class PaymentType(str, Enum):
    ADVANCE = "Advance"
    ORDER_PAYMENT = "OrderPayment"
    FINAL = "FINAL"

class OrderItemStatus(str, Enum):
    CUTTING = "CUTTING"
    STITCHING = "STITCHING"
    READY = "READY"

class Quantity(BaseModel):
    qty: float
    unit: str

class OrderItemQuantity(BaseModel):
    qty: Quantity
    count: float

class Money(BaseModel):
    price: float
    currency: str = "INR"

class Address(BaseModel):
    address_line1: Optional[str] = Field(None, alias="addressLine1")
    address_line2: Optional[str] = Field(None, alias="addressLine2")
    address_line3: Optional[str] = Field(None, alias="addressLine3")
    city: str
    district: str
    state: str
    country: str = "India"
    postal_code: int = Field(default=0, alias="postalCode")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")

class Measurement(BaseModel):
    measurement_type: str = Field(..., alias="measurementType")
    measurement_name: str = Field(..., alias="measurementName")
    measurement_json: Dict[str, float] = Field(..., alias="measurementJson")

class OrderItem(BaseModel):
    order_id: str = Field(..., alias="orderId")
    order_item_id: str = Field(..., alias="orderItemId")
    profile_id: str = Field(..., alias="profileId")
    profile_name: str = Field(..., alias="profileName")
    order_item_type: str = Field(..., alias="orderItemType")
    order_item_status: OrderItemStatus = Field(..., alias="orderItemStaus")
    measurement: Measurement
    order_item_quantity: OrderItemQuantity = Field(..., alias="orderItemQuantity")
    order_item_amount: Money = Field(..., alias="orderItemAmount")
    order_item_tax_amount: Money = Field(default_factory=lambda: Money(price=0.0), alias="orderItemTaxAmount")
    order_item_discount: Money = Field(default_factory=lambda: Money(price=0.0), alias="orderItemDiscount")
    order_item_total_amount: Money = Field(..., alias="orderItemTotalAmount")
    order_notes: Optional[str] = Field(None, alias="orderNotes")

class PaymentMethodRef(BaseModel):
    external_reference_id: Optional[str] = Field(None, alias="externalReferenceId")

class PaymentDetail(BaseModel):
    payment_id: Optional[str] = Field(None, alias="paymentId")
    payment_type: Optional[PaymentType] = Field(None, alias="paymentType")
    payment_amount: Optional[Money] = Field(None, alias="paymentAmount")
    payment_method: Optional[str] = Field(None, alias="paymentMethod") # CASH/UPI/CARD
    payment_method_ref: Optional[PaymentMethodRef] = Field(None, alias="paymentMethodRef")
    payment_date: Optional[datetime] = Field(None, alias="paymentDate")

    class Config:
        populate_by_name = True

class Order(BaseModel):
    order_id: str = Field(..., alias="orderId")
    order_date: datetime = Field(..., alias="orderDate")
    estimated_order_delivery_date: datetime = Field(..., alias="estimatedOrderDeliveryDate")
    delivery_date: Optional[datetime] = Field(None, alias="deliveryDate")
    order_type: OrderType = Field(..., alias="orderType")
    order_status: OrderStatus = Field(..., alias="orderStatus")
    customer_id: str = Field(..., alias="customerId")
    customer_phone_number: Optional[PhoneNumber] = Field(None, alias="customerPhoneNumber")
    customer_address: Optional[Address] = Field(None, alias="customerAddress")
    order_notes: Optional[str] = Field(None, alias="orderNotes")
    
    order_amount_without_tax: Money = Field(..., alias="orderAmountWithoutTax")
    order_tax_amount: Money = Field(..., alias="orderTaxAmount")
    order_discount_amount: Money = Field(..., alias="orderDiscountAmount")
    order_amount_with_tax: Money = Field(..., alias="orderAmountWithTax")
    order_total_amount: Money = Field(..., alias="orderTotalAmount")
    order_rnd_amount: Money = Field(default_factory=lambda: Money(price=0.0), alias="orderRndAmount")
    
    payment_details: List[PaymentDetail] = Field(default_factory=list, alias="paymentDetails")

    class Config:
        populate_by_name = True

class OrderAudit(BaseModel):
    order_id: str = Field(..., alias="orderId")
    action: str
    action_by: str = Field(..., alias="actionBy")
    action_date: datetime = Field(default_factory=datetime.now, alias="actionDate")
    changes: Dict[str, Any]
