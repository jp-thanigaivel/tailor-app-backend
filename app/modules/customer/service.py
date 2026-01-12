import logging
from typing import List, Optional
from fastapi import status
from app.modules.customer.repository import customer_repo
from app.modules.customer.schemas import CreateCustomerRequest, UpdateCustomerRequest, CustomerResponse
from app.core.dependencies import TenantContext
from app.core.exceptions import EntityAlreadyExistException, NoDataFoundException
from app.utils.common_functions import DBUtils
from app.utils.app_constant import COLL_TODO_SEQ_CUSTOMER_ID, SEQ_TODO_CUSTOMER_ID, PREFIX_SEQ_TODO_CUSTOMER_ID
from app.common.utils import MetadataUtils

logger = logging.getLogger(__name__)

class CustomerService:
    @staticmethod
    def create_customer(context: TenantContext, obj_in: CreateCustomerRequest):
        logger.info(f"Creating customer: {obj_in.customer_name}")
        
        # Check for existing customer with same name
        #existing_name = customer_repo.get(context, {"customerName": obj_in.customer_name})
        #if existing_name:
        #    raise EntityAlreadyExistException(
        #        error_code=status.HTTP_400_BAD_REQUEST,
        #        error_type="ERROR",
        #        error_desc=f"Customer with name {obj_in.customer_name} already exists"
        #    )

        # Check for existing customer with same phone number
        existing_phone = customer_repo.get(context, {"phoneNumber.phoneNumber": obj_in.phone_number.phone_number})
        if existing_phone:
            raise EntityAlreadyExistException(
                error_code=status.HTTP_400_BAD_REQUEST,
                error_type="ERROR",
                error_desc=f"Customer with phone number {obj_in.phone_number.phone_number} already exists"
            )

        # Generate Customer ID
        customer_id = DBUtils.get_formatted_sequence(
            COLL_TODO_SEQ_CUSTOMER_ID, 
            SEQ_TODO_CUSTOMER_ID,
            PREFIX_SEQ_TODO_CUSTOMER_ID
        )
        
        # Prepare data for DB
        data = obj_in.model_dump(by_alias=True)
        data["customerId"] = customer_id
        
        # Add metadata
        MetadataUtils.prepare_create_metadata(data, context.user_id, context)
        
        customer_repo.create(context, data)
        return CustomerResponse(**data)

    @staticmethod
    def get_all_customers(context: TenantContext, phone_number: Optional[str] = None, skip: int = 0, limit: int = 100):
        query = {}
        if phone_number:
            query["phoneNumber.phoneNumber"] = phone_number
            
        customers = customer_repo.get_all(context, filter_query=query, skip=skip, limit=limit)
        return [CustomerResponse(**c.model_dump(by_alias=True)) for c in customers]

    @staticmethod
    def get_customer_by_id(context: TenantContext, customer_id: str):
        customer = customer_repo.get(context, {"customerId": customer_id})
        if not customer:
            raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Customer not found"
            )
        return CustomerResponse(**customer.model_dump(by_alias=True))

    @staticmethod
    def update_customer(context: TenantContext, customer_id: str, obj_in: UpdateCustomerRequest):
        CustomerService.get_customer_by_id(context, customer_id) # ensures existence
        
        data = obj_in.model_dump(exclude_unset=True, by_alias=True)
        MetadataUtils.prepare_update_metadata(data, context.user_id)
        
        updated = customer_repo.update(context, {"customerId": customer_id}, data)
        return CustomerResponse(**updated.model_dump(by_alias=True))

    @staticmethod
    def delete_customer(context: TenantContext, customer_id: str):
        success = customer_repo.delete(context, {"customerId": customer_id})
        if not success:
            raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Customer not found or not authorized to delete"
            )
        return success
