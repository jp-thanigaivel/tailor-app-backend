from fastapi import APIRouter, Depends, status, Request, Query
from typing import Optional


from app.common.models import APIResponse
from app.core.dependencies import get_tenant_context, TenantContext
from app.core.exceptions import get_standard_response
from app.modules.order.schemas import (
    CreateOrderRequest, UpdateOrderRequest, CreatePaymentRequest, CreateOrderItemRequest,
    UpdateOrderItemRequest, OrderResponse, UpdateOrderStatusRequest,
    OrderItemStatusUpdateRequest, GetOrdersResponse
)
from app.modules.order.service import OrderService

router = APIRouter(prefix="/order", tags=["Order"])

# --- Order Endpoints ---

@router.get("/", response_model=APIResponse)
def get_orders(
    request: Request,
    context: TenantContext = Depends(get_tenant_context)
):
    query_params = dict(request.query_params)
    data = OrderService.get_all_orders(context, query_params)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    obj_in: CreateOrderRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.create_order(context, obj_in)
    return {
        "status": get_standard_response(status.HTTP_201_CREATED, "SUCCESS", "Order Created")["status"],
        "data": data
    }

@router.get("/{orderId}", response_model=APIResponse)
def get_order_by_id(
    orderId: str,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.get_order_by_id(context, orderId)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.patch("/{orderId}", response_model=APIResponse)
def update_order(
    orderId: str,
    obj_in: UpdateOrderRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.update_order(context, orderId, obj_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Order updated successfully")["status"],
        "data": data
    }

@router.patch("/{orderId}/status", response_model=APIResponse)
def update_order_status(
    orderId: str,
    status_in: UpdateOrderStatusRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.update_order_status(context, orderId, status_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Order status updated successfully")["status"],
        "data": data
    }

@router.post("/{orderId}/payment", response_model=APIResponse)
def add_payment(
    orderId: str,
    payment_in: CreatePaymentRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.add_payment(context, orderId, payment_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Payment added successfully")["status"],
        "data": data
    }

@router.post("/{orderId}/calculate", response_model=APIResponse)
def calculate_order(
    orderId: str,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.calculate_order_totals_endpoint(context, orderId)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Order totals recalculated")["status"],
        "data": data
    }

@router.get("/{orderId}/audit", response_model=APIResponse)
def get_order_audit(
    orderId: str,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.get_order_audit(context, orderId)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

# --- Item Endpoints ---

@router.get("/{orderId}/item", response_model=APIResponse)
def get_order_items(
    orderId: str,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.get_order_items(context, order_id=orderId)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.get("/{orderId}/item/{orderItemId}", response_model=APIResponse)
def get_order_item_by_id(
    orderId: str,
    orderItemId: str,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.get_order_item_by_id(context, orderId, orderItemId)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.post("/{orderId}/item", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def add_order_item(
    orderId: str,
    item_in: CreateOrderItemRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.add_order_item(context, order_id=orderId, item_in=item_in)
    return {
        "status": get_standard_response(status.HTTP_201_CREATED, "SUCCESS", "Item added successfully")["status"],
        "data": data
    }

@router.patch("/{orderId}/item/{orderItemId}", response_model=APIResponse)
def update_order_item(
    orderId: str,
    orderItemId: str,
    item_in: UpdateOrderItemRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.update_order_item(context, order_id=orderId, item_id=orderItemId, item_in=item_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Item updated successfully")["status"],
        "data": data
    }

@router.patch("/{orderId}/item/{orderItemId}/status", response_model=APIResponse)
def update_order_item_status(
    orderId: str,
    orderItemId: str,
    status_in: OrderItemStatusUpdateRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = OrderService.update_order_item_status(context, orderId, orderItemId, status_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Item status updated successfully")["status"],
        "data": data
    }

@router.delete("/{orderId}/item/{orderItemId}", response_model=APIResponse)
def delete_order_item(
    orderId: str,
    orderItemId: str,
    context: TenantContext = Depends(get_tenant_context)
):
    OrderService.delete_order_item(context, order_id=orderId, item_id=orderItemId)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Item deleted successfully")["status"],
        "data": ""
    }
