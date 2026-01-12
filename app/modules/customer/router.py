from typing import Optional

from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_tenant_context, TenantContext
from app.modules.customer.service import CustomerService
from app.modules.customer.schemas import CreateCustomerRequest, UpdateCustomerRequest
from app.core.exceptions import get_standard_response
from starlette import status

router = APIRouter(tags=["Customer"])

@router.post("/customer", status_code=status.HTTP_201_CREATED)
async def create_customer(
    obj_in: CreateCustomerRequest, 
    context: TenantContext = Depends(get_tenant_context)
):
    data = CustomerService.create_customer(context, obj_in)
    return {
        "status": get_standard_response(status.HTTP_201_CREATED, "SUCCESS", "Customer created successfully")["status"],
        "data": data
    }

@router.get("/customers")
async def get_customers(
    phone_number: Optional[str] = Query(None, alias="phoneNumber"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    context: TenantContext = Depends(get_tenant_context)
):
    data = CustomerService.get_all_customers(context, phone_number=phone_number, skip=skip, limit=limit)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str,
    context: TenantContext = Depends(get_tenant_context)
):
    data = CustomerService.get_customer_by_id(context, customer_id)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.patch("/customer/{customer_id}")
async def update_customer(
    customer_id: str,
    obj_in: UpdateCustomerRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = CustomerService.update_customer(context, customer_id, obj_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Customer updated successfully")["status"],
        "data": data
    }

@router.delete("/customer/{customer_id}")
async def delete_customer(
    customer_id: str,
    context: TenantContext = Depends(get_tenant_context)
):
    CustomerService.delete_customer(context, customer_id)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Customer deleted successfully")["status"],
        "data": ""
    }
