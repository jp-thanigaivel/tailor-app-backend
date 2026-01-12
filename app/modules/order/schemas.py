from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from app.modules.order.models import OrderType, OrderStatus, OrderItemStatus, PaymentType, Money, Address, Measurement, Quantity, OrderItemQuantity
from app.common.models import PhoneNumber

class MeasurementSchema(BaseModel):
    measurement_name: str = Field(..., alias="measurementName")
    measurement_type: Optional[str] = Field(None, alias="measurementType")
    measurement_json: Optional[Dict[str, float]] = Field(None, alias="measurementJson")

    class Config:
        populate_by_name = True

class OrderItemBase(BaseModel):
    profile_id: str = Field(..., alias="profileId")
    order_item_type: str = Field(..., alias="orderItemType")
    order_item_status: OrderItemStatus = Field(OrderItemStatus.CUTTING, alias="orderItemStaus")
    measurement: MeasurementSchema
    order_item_quantity: OrderItemQuantity = Field(..., alias="orderItemQuantity")
    order_item_amount: Money = Field(..., alias="orderItemAmount")
    order_item_tax_amount: Optional[Money] = Field(None, alias="orderItemTaxAmount")
    order_item_discount: Optional[Money] = Field(None, alias="orderItemDiscount")
    order_item_notes: Optional[str] = Field(None, alias="orderItemNotes")

    class Config:
        populate_by_name = True

class CreateOrderItemRequest(OrderItemBase):
    pass

class UpdateOrderItemRequest(OrderItemBase):
    pass

class OrderItemStatusUpdateRequest(BaseModel):
    order_item_status: OrderItemStatus = Field(..., alias="orderItemStaus")
    notes: Optional[str] = None

    class Config:
        populate_by_name = True

class OrderItemResponse(OrderItemBase):
    profile_name: str = Field(..., alias="profileName")
    order_id: str = Field(..., alias="orderId")
    order_item_id: str = Field(..., alias="orderItemId")
    order_item_total_amount: Money = Field(..., alias="orderItemTotalAmount")

class PaymentMethodRefSchema(BaseModel):
    external_reference_id: Optional[str] = Field(None, alias="externalReferenceId")

class PaymentDetailBase(BaseModel):
    payment_type: PaymentType = Field(..., alias="paymentType")
    payment_amount: Money = Field(..., alias="paymentAmount")
    payment_method: str = Field(..., alias="paymentMethod") # CASH/UPI/CARD
    payment_method_ref: Optional[PaymentMethodRefSchema] = Field(None, alias="paymentMethodRef")
    payment_date: Optional[datetime] = Field(None, alias="paymentDate")

    class Config:
        populate_by_name = True

class CreatePaymentRequest(PaymentDetailBase):
    @field_validator('payment_amount')
    def validate_payment_amount(cls, v):
        if v.price <= 0:
            raise ValueError("Payment amount must be greater than zero")
        return v

class CreateOrderRequest(BaseModel):
    customer_id: str = Field(..., alias="customerId")
    order_type: OrderType = Field(..., alias="orderType")
    order_status: OrderStatus = Field(OrderStatus.DRAFT, alias="orderStatus")
    estimated_order_delivery_date: Optional[datetime] = Field(None, alias="estimatedOrderDeliveryDate")
    order_notes: Optional[str] = Field(None, alias="orderNotes")
    payment_details: List[CreatePaymentRequest] = Field(default_factory=list, alias="paymentDetails")

    class Config:
        populate_by_name = True

class UpdateOrderRequest(BaseModel):
    order_status: Optional[OrderStatus] = Field(None, alias="orderStatus")
    estimated_order_delivery_date: Optional[datetime] = Field(None, alias="estimatedOrderDeliveryDate")
    delivery_date: Optional[datetime] = Field(None, alias="deliveryDate")
    order_notes: Optional[str] = Field(None, alias="orderNotes")
    
    class Config:
        populate_by_name = True

class UpdateOrderStatusRequest(BaseModel):
    order_status: OrderStatus = Field(..., alias="orderStatus")
    notes: Optional[str] = None

    class Config:
        populate_by_name = True

class OrderResponse(BaseModel):
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
    order_rnd_amount: Money = Field(..., alias="orderRndAmount")
    payment_details: List[Dict[str, Any]] = Field(default_factory=list, alias="paymentDetails")

    class Config:
        populate_by_name = True

class GetOrdersResponse(BaseModel):
    data: List[OrderResponse]
    pagination: Optional[Any] = None

class OrderAuditResponse(BaseModel):
    order_id: str = Field(..., alias="orderId")
    action: str
    action_by: str = Field(..., alias="actionBy")
    action_date: datetime = Field(..., alias="actionDate")
    changes: Dict[str, Any]

    class Config:
        populate_by_name = True
