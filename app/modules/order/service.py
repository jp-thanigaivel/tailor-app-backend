import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import status
from app.core.dependencies import TenantContext
from app.core.exceptions import InvalidRequestException, NoDataFoundException, DataBaseException
from app.modules.order.repository import order_repo, order_item_repo, payment_repo, order_audit_repo
from app.modules.order.schemas import (
    CreateOrderRequest, UpdateOrderRequest, OrderResponse, 
    CreatePaymentRequest, OrderAuditResponse, CreateOrderItemRequest, 
    UpdateOrderItemRequest, OrderItemResponse, OrderItemStatusUpdateRequest,
    UpdateOrderStatusRequest
)
from app.modules.order.models import OrderStatus, OrderType, OrderItemStatus, PaymentType
from app.modules.profile.repository import profile_repo
from app.modules.profile.schemas import MeasurementConfig
from app.modules.customer.service import CustomerService
from app.utils.common_functions import DBUtils
from app.utils.app_constant import (
    COLL_TODO_SEQ_ORDER_ID, SEQ_TODO_ORDER_ID, PREFIX_SEQ_TODO_ORDER_ID,
    COLL_TODO_SEQ_ORDER_ITEM_ID, SEQ_TODO_ORDER_ITEM_ID, PREFIX_SEQ_TODO_ORDER_ITEM_ID,
    COLL_TODO_SEQ_PAYMENT_ID, SEQ_TODO_PAYMENT_ID, PREFIX_SEQ_TODO_PAYMENT_ID
)
from app.common.utils import MetadataUtils

logger = logging.getLogger(__name__)

ITEM_STATUS_TRANSITIONS = {
    OrderItemStatus.CUTTING: [OrderItemStatus.STITCHING],
    OrderItemStatus.STITCHING: [OrderItemStatus.CUTTING, OrderItemStatus.READY],
    OrderItemStatus.READY: []
}

ORDER_STATUS_TRANSITIONS = {
    OrderStatus.DRAFT: [OrderStatus.RECEIVED],
    OrderStatus.RECEIVED: [OrderStatus.DRAFT, OrderStatus.STITCHING],
    OrderStatus.STITCHING: [OrderStatus.RECEIVED, OrderStatus.READY],
    OrderStatus.READY: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: []
}

class OrderService:
    @staticmethod
    def _calculate_order_totals(context: TenantContext, order_id: str) -> Dict[str, Any]:
        items = order_item_repo.get_all(context, {"orderId": order_id})
        amount_without_tax = 0.0
        tax_amount = 0.0
        discount_amount = 0.0
        
        for item in items:
            item_data = item.model_dump(by_alias=True)
            qty = item_data["orderItemQuantity"]["qty"]["qty"]
            count = item_data["orderItemQuantity"]["count"]
            price = item_data["orderItemAmount"]["price"]
            
            item_base = price * (qty * count)
            item_tax = item_data.get("orderItemTaxAmount", {}).get("price", 0.0)
            item_disc = item_data.get("orderItemDiscount", {}).get("price", 0.0)
            
            amount_without_tax += item_base
            tax_amount += item_tax
            discount_amount += item_disc
            
        total_amount = amount_without_tax + tax_amount - discount_amount
        
        return {
            "orderAmountWithoutTax": {"price": amount_without_tax, "currency": "INR"},
            "orderTaxAmount": {"price": tax_amount, "currency": "INR"},
            "orderDiscountAmount": {"price": discount_amount, "currency": "INR"},
            "orderAmountWithTax": {"price": total_amount, "currency": "INR"},
            "orderTotalAmount": {"price": total_amount, "currency": "INR"},
            "orderRndAmount": {"price": 0.0, "currency": "INR"}
        }

    @staticmethod
    def _check_order_status_for_edit(order_status: OrderStatus, action: str = "edit items"):
        if order_status != OrderStatus.DRAFT:
             raise InvalidRequestException(
                status.HTTP_400_BAD_REQUEST, "ERROR", 
                f"Items can only be added/updated/deleted in DRAFT status. Current status: {order_status}"
            )

    @staticmethod
    def _validate_and_populate_item(context: TenantContext, item_in: CreateOrderItemRequest) -> Dict[str, Any]:
        # Validation
        profile = profile_repo.get(context, {"profileId": item_in.profile_id})
        if not profile:
             raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Profile not found")
        
        if item_in.order_item_type not in MeasurementConfig.ALLOWED_TYPES:
             raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", f"Invalid item type: {item_in.order_item_type}")
        
        # Find measurement in profile
        profile_measurements = profile.measurements
        target_measurement = next((m for m in profile_measurements if m.get("measurementName") == item_in.measurement.measurement_name), None)
        
        if not target_measurement:
             raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", f"Measurement {item_in.measurement.measurement_name} not found in profile")
        
        if target_measurement.get("measurementType") != item_in.order_item_type:
              raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", f"Measurement type mismatch. Expected {item_in.order_item_type}, found {target_measurement.get('measurementType')}")

        item_data = item_in.model_dump(by_alias=True)
        item_data["profileName"] = profile.profile_name
        item_data["measurement"]["measurementType"] = target_measurement["measurementType"]
        item_data["measurement"]["measurementJson"] = target_measurement["measurementJson"]
        return item_data

    @staticmethod
    def create_order(context: TenantContext, obj_in: CreateOrderRequest) -> OrderResponse:
        logger.info(f"Creating order for customer: {obj_in.customer_id}")
        
        # Validate Customer
        customer = CustomerService.get_customer_by_id(context, obj_in.customer_id)
        
        order_id = DBUtils.get_formatted_sequence(
            COLL_TODO_SEQ_ORDER_ID, SEQ_TODO_ORDER_ID, PREFIX_SEQ_TODO_ORDER_ID
        )
        
        order_data = obj_in.model_dump(by_alias=True)
        order_data["orderId"] = order_id
        order_data["orderDate"] = datetime.now()
        order_data["customerAddress"] = customer.customer_address.model_dump(by_alias=True) if customer.customer_address else None
        order_data["customerPhoneNumber"] = customer.phone_number.model_dump(by_alias=True)
        
        if not order_data.get("estimatedOrderDeliveryDate"):
            days = 7 if obj_in.order_type == OrderType.INDIVIDUAL else 14
            order_data["estimatedOrderDeliveryDate"] = order_data["orderDate"] + timedelta(days=days)

        # Initialize Payments
        input_payments = order_data.get("paymentDetails") or []
        for payment in input_payments:
            payment["paymentId"] = DBUtils.get_formatted_sequence(
                COLL_TODO_SEQ_PAYMENT_ID, SEQ_TODO_PAYMENT_ID, PREFIX_SEQ_TODO_PAYMENT_ID
            )
            if not payment.get("paymentDate"):
                payment["paymentDate"] = datetime.now()

        # Initial Totals (Order is created without items)
        order_data.update({
            "orderAmountWithoutTax": {"price": 0.0, "currency": "INR"},
            "orderTaxAmount": {"price": 0.0, "currency": "INR"},
            "orderDiscountAmount": {"price": 0.0, "currency": "INR"},
            "orderAmountWithTax": {"price": 0.0, "currency": "INR"},
            "orderTotalAmount": {"price": 0.0, "currency": "INR"},
            "orderRndAmount": {"price": 0.0, "currency": "INR"}
        })

        total_payment = sum(p["paymentAmount"]["price"] for p in input_payments)
        if total_payment > order_data["orderTotalAmount"]["price"] and order_data["orderTotalAmount"]["price"] > 0:
                     raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Total payment exceeds order total")

        MetadataUtils.prepare_create_metadata(order_data, context.user_id, context)
        order_repo.create(context, order_data)
        
        # Audit
        order_audit_repo.create(context, {
            "orderId": order_id, "action": "CREATE", "actionBy": context.user_id,
            "actionDate": datetime.now(), "changes": {"status": obj_in.order_status}
        })
        
        order_data["orderItems"] = []
        return OrderResponse(**order_data)

    @staticmethod
    def get_order_by_id(context: TenantContext, order_id: str) -> OrderResponse:
        order = order_repo.get(context, {"orderId": order_id})
        if not order:
            raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        order_data = order.model_dump(by_alias=True)
        return OrderResponse(**order_data)

    @staticmethod
    def get_all_orders(context: TenantContext, query_params: Dict[str, Any]) -> Dict[str, Any]:
        from app.utils.app_obj_mapper import AppObjectMapper
        from app.utils.order_constant import Q_ALLOWED_FILTER_FIELDS_order, Q_ALLOWED_SORT_FIELDS_order
        
        db_pagination_meta = AppObjectMapper.get_db_meta(
            query_params, 
            Q_ALLOWED_FILTER_FIELDS_order, 
            Q_ALLOWED_SORT_FIELDS_order
        )
        
        result = order_repo.get_all_with_pagination(
            context,
            filter_query=db_pagination_meta.filter_condition,
            page_size=db_pagination_meta.page_size,
            page_number=db_pagination_meta.page_number,
            cursor=db_pagination_meta.cursor,
            sort_condition=db_pagination_meta.sort_condition
        )
        
        orders = [OrderResponse(**order.model_dump(by_alias=True)) for order in result["data"]]
        return {
            "data": orders,
            "pagination": result["pagination"]
        }

    @staticmethod
    def update_order(context: TenantContext, order_id: str, obj_in: UpdateOrderRequest) -> OrderResponse:
        existing_order = order_repo.get(context, {"orderId": order_id})
        if not existing_order:
             raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        current_status = existing_order.order_status
        new_status = obj_in.order_status
        
        if new_status and new_status != current_status:
            # Transition Logic
            allowed = ORDER_STATUS_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                 raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", f"Invalid status transition: {current_status} -> {new_status}")

            if new_status == OrderStatus.RECEIVED:
                 # Validate at least one item
                 items = order_item_repo.get_all(context, {"orderId": order_id})
                 if not items or len(items) == 0:
                      raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Order must have at least one item to move to RECEIVED status")
            
            if new_status == OrderStatus.STITCHING:
                 # Validate at least one item
                 items = order_item_repo.get_all(context, {"orderId": order_id})
                 if not items or len(items) == 0:
                      raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Order must have at least one item to move to STITCHING status")

            if new_status == OrderStatus.READY:
                 # Validate all items are READY
                 items = order_item_repo.get_all(context, {"orderId": order_id})
                 if not items:
                      raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Order must have items to be READY")
                 for item in items:
                      if item.order_item_status != OrderItemStatus.READY:
                           raise InvalidRequestException(
                                status.HTTP_400_BAD_REQUEST, "ERROR", 
                                f"All items must be READY before moving order to READY. Item {item.order_item_id} is {item.order_item_status}"
                            )

        update_data = obj_in.model_dump(exclude_unset=True, by_alias=True)
        
        if new_status == OrderStatus.RECEIVED and current_status == OrderStatus.DRAFT:
             # Automatic recalculation
             totals = OrderService._calculate_order_totals(context, order_id)
             update_data.update(totals)

        if new_status == OrderStatus.DELIVERED:
            if not update_data.get("deliveryDate"):
                update_data["deliveryDate"] = datetime.now()

        MetadataUtils.prepare_update_metadata(update_data, context.user_id)
        order_repo.update(context, {"orderId": order_id}, update_data)
        
        # Audit
        audit_data = {
            "orderId": order_id, "action": "UPDATE", "actionBy": context.user_id,
            "actionDate": datetime.now(), "changes": update_data
        }
        order_audit_repo.create(context, audit_data)
             
        return OrderService.get_order_by_id(context, order_id)

    @staticmethod
    def update_order_status(context: TenantContext, order_id: str, status_in: UpdateOrderStatusRequest) -> OrderResponse:
        existing_order = order_repo.get(context, {"orderId": order_id})
        if not existing_order:
             raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        current_status = existing_order.order_status
        new_status = status_in.order_status
        
        if new_status != current_status:
            allowed = ORDER_STATUS_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                 raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", f"Invalid status transition: {current_status} -> {new_status}")
            
            if new_status == OrderStatus.RECEIVED:
                 items = order_item_repo.get_all(context, {"orderId": order_id})
                 if not items or len(items) == 0:
                      raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Order must have at least one item to move to RECEIVED status")
            
            if new_status == OrderStatus.STITCHING:
                 items = order_item_repo.get_all(context, {"orderId": order_id})
                 if not items or len(items) == 0:
                      raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Order must have at least one item to move to STITCHING status")

            if new_status == OrderStatus.READY:
                 items = order_item_repo.get_all(context, {"orderId": order_id})
                 if not items:
                      raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Order must have items to be READY")
                 for item in items:
                      if item.order_item_status != OrderItemStatus.READY:
                           raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", f"All items must be READY before moving order to READY")

        update_data = {"orderStatus": new_status}
        if new_status == OrderStatus.RECEIVED and current_status == OrderStatus.DRAFT:
             totals = OrderService._calculate_order_totals(context, order_id)
             update_data.update(totals)
        
        if new_status == OrderStatus.DELIVERED:
             update_data["deliveryDate"] = datetime.now()

        MetadataUtils.prepare_update_metadata(update_data, context.user_id)
        order_repo.update(context, {"orderId": order_id}, update_data)
        
        # Audit
        order_audit_repo.create(context, {
            "orderId": order_id, "action": "ORDER_STATUS_UPDATE", "actionBy": context.user_id,
            "actionDate": datetime.now(), 
            "changes": {"from": current_status, "to": new_status, "notes": status_in.notes}
        })
        
        return OrderService.get_order_by_id(context, order_id)

    @staticmethod
    def calculate_order_totals_endpoint(context: TenantContext, order_id: str) -> OrderResponse:
        order = order_repo.get(context, {"orderId": order_id})
        if not order: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        if order.order_status != OrderStatus.RECEIVED:
             raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Order calculation is only allowed in RECEIVED status")
        
        totals = OrderService._calculate_order_totals(context, order_id)
        MetadataUtils.prepare_update_metadata(totals, context.user_id)
        order_repo.update(context, {"orderId": order_id}, totals)
        
        return OrderService.get_order_by_id(context, order_id)

    @staticmethod
    def add_order_item(context: TenantContext, order_id: str, item_in: CreateOrderItemRequest) -> OrderItemResponse:
        order = order_repo.get(context, {"orderId": order_id})
        if not order: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        OrderService._check_order_status_for_edit(order.order_status, "add items")
        if order.order_status != OrderStatus.DRAFT:
             raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Can only add items in DRAFT status")

        item_data = OrderService._validate_and_populate_item(context, item_in)
        item_data["orderId"] = order_id
        item_data["orderItemId"] = DBUtils.get_formatted_sequence(
            COLL_TODO_SEQ_ORDER_ITEM_ID, SEQ_TODO_ORDER_ITEM_ID, PREFIX_SEQ_TODO_ORDER_ITEM_ID
        )
        
        # Calculation
        qty = item_data["orderItemQuantity"]["qty"]["qty"]
        count = item_data["orderItemQuantity"]["count"]
        price = item_data["orderItemAmount"]["price"]
        tax = item_data.get("orderItemTaxAmount", {}).get("price", 0.0) if item_data.get("orderItemTaxAmount") else 0.0
        disc = item_data.get("orderItemDiscount", {}).get("price", 0.0) if item_data.get("orderItemDiscount") else 0.0
        item_data["orderItemTotalAmount"] = {"price": (price * qty * count) + tax - disc, "currency": "INR"}

        MetadataUtils.prepare_create_metadata(item_data, context.user_id, context)
        order_item_repo.create(context, item_data)
        
        # Re-calculate Order Totals
        totals = OrderService._calculate_order_totals(context, order_id)
        order_repo.update(context, {"orderId": order_id}, totals)
        
        return OrderItemResponse(**item_data)

    @staticmethod
    def update_order_item(context: TenantContext, order_id: str, item_id: str, item_in: UpdateOrderItemRequest) -> OrderItemResponse:
        order = order_repo.get(context, {"orderId": order_id})
        if not order: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        existing_item = order_item_repo.get(context, {"orderItemId": item_id, "orderId": order_id})
        if not existing_item: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Item not found")

        OrderService._check_order_status_for_edit(order.order_status, "update items")
        
        updated_data = OrderService._validate_and_populate_item(context, item_in)
        
        # Re-calculate item total
        qty = updated_data["orderItemQuantity"]["qty"]["qty"]
        count = updated_data["orderItemQuantity"]["count"]
        price = updated_data["orderItemAmount"]["price"]
        tax = updated_data.get("orderItemTaxAmount", {}).get("price", 0.0) if updated_data.get("orderItemTaxAmount") else 0.0
        disc = updated_data.get("orderItemDiscount", {}).get("price", 0.0) if updated_data.get("orderItemDiscount") else 0.0
        updated_data["orderItemTotalAmount"] = {"price": (price * qty * count) + tax - disc, "currency": "INR"}

        MetadataUtils.prepare_update_metadata(updated_data, context.user_id)
        updated_item = order_item_repo.update(context, {"orderItemId": item_id, "orderId": order_id}, updated_data)
        
        # Since we are replacing, we should always re-calculate order totals
        totals = OrderService._calculate_order_totals(context, order_id)
        order_repo.update(context, {"orderId": order_id}, totals)
             
        return OrderItemResponse(**updated_item.model_dump(by_alias=True))

    @staticmethod
    def update_order_item_status(context: TenantContext, order_id: str, item_id: str, status_in: OrderItemStatusUpdateRequest) -> OrderItemResponse:
        order = order_repo.get(context, {"orderId": order_id})
        if not order: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        existing_item = order_item_repo.get(context, {"orderItemId": item_id, "orderId": order_id})
        if not existing_item: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Item not found")

        current_status = existing_item.order_item_status
        new_status = status_in.order_item_status
        
        if new_status != current_status:
            allowed = ITEM_STATUS_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                 raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", f"Invalid status transition for item: {current_status} -> {new_status}")

        update_data = {"orderItemStaus": new_status}
        MetadataUtils.prepare_update_metadata(update_data, context.user_id)
        updated_item = order_item_repo.update(context, {"orderItemId": item_id, "orderId": order_id}, update_data)
        
        # Audit
        order_audit_repo.create(context, {
            "orderId": order_id, "action": "ITEM_STATUS_UPDATE", "actionBy": context.user_id,
            "actionDate": datetime.now(), 
            "changes": {"orderItemId": item_id, "from": current_status, "to": new_status, "notes": status_in.notes}
        })
        
        return OrderItemResponse(**updated_item.model_dump(by_alias=True))

    @staticmethod
    def delete_order_item(context: TenantContext, order_id: str, item_id: str) -> bool:
        order = order_repo.get(context, {"orderId": order_id})
        if not order: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        OrderService._check_order_status_for_edit(order.order_status, "delete items")
        if order.order_status != OrderStatus.DRAFT:
             raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Items can only be deleted in DRAFT status")

        success = order_item_repo.delete(context, {"orderItemId": item_id, "orderId": order_id})
        if success:
             totals = OrderService._calculate_order_totals(context, order_id)
             order_repo.update(context, {"orderId": order_id}, totals)
        return success

    @staticmethod
    def get_order_items(context: TenantContext, order_id: str) -> List[OrderItemResponse]:
        items = order_item_repo.get_all(context, {"orderId": order_id})
        return [OrderItemResponse(**item.model_dump(by_alias=True)) for item in items]

    @staticmethod
    def get_order_item_by_id(context: TenantContext, order_id: str, item_id: str) -> OrderItemResponse:
        item = order_item_repo.get(context, {"orderItemId": item_id, "orderId": order_id})
        if not item:
            raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order item not found")
        return OrderItemResponse(**item.model_dump(by_alias=True))

    @staticmethod
    def add_payment(context: TenantContext, order_id: str, payment_in: CreatePaymentRequest) -> OrderResponse:
        order = order_repo.get(context, {"orderId": order_id})
        if not order: raise NoDataFoundException(status.HTTP_404_NOT_FOUND, "WARN", "Order not found")
        
        payment_data = payment_in.model_dump(by_alias=True)
        payment_data["paymentId"] = DBUtils.get_formatted_sequence(
            COLL_TODO_SEQ_PAYMENT_ID, SEQ_TODO_PAYMENT_ID, PREFIX_SEQ_TODO_PAYMENT_ID
        )
        if not payment_data.get("paymentDate"):
            payment_data["paymentDate"] = datetime.now()
            
        current_payments = order.model_dump(by_alias=True).get("paymentDetails") or []
        total_paid = sum(p["paymentAmount"]["price"] for p in current_payments) + payment_data["paymentAmount"]["price"]
        
        if total_paid > order.order_total_amount.price:
             raise InvalidRequestException(status.HTTP_400_BAD_REQUEST, "ERROR", "Total payment exceeds order amount")
             
        current_payments.append(payment_data)
        
        # Update payments
        order_repo.update(context, {"orderId": order_id}, {"paymentDetails": current_payments})
        
        order_audit_repo.create(context, {
            "orderId": order_id, "action": "PAYMENT", "actionBy": context.user_id,
            "actionDate": datetime.now(), "changes": {"paymentId": payment_data["paymentId"]}
        })
        
        return OrderService.get_order_by_id(context, order_id)

    @staticmethod
    def get_order_audit(context: TenantContext, order_id: str) -> List[OrderAuditResponse]:
        audits = order_audit_repo.get_all(context, {"orderId": order_id})
        return [OrderAuditResponse(**a.model_dump(by_alias=True)) for a in audits]
