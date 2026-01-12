from starlette import status
from app.core.dependencies import TenantContext
from app.modules.customer.service import CustomerService
from app.modules.customer.models import Customer
# from app.models.production import Production # Keep if still needed for production
from app.utils.app_constant import STATUS_TYPE_ERROR, STATUS_DESC_INVALID_REQUEST
from app.core.exceptions import NoDataFoundException, InvalidRequestException

def validate_customer(customer_id: str, context: TenantContext):
    try:
        return CustomerService.get_customer_by_id(context, customer_id)
    except NoDataFoundException as exp:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} customer_id '{customer_id}' is not found"
        ) from exp

def validate_production(production_id: str, context: TenantContext):
    try:
        from app.service.production.production import get_production_obj_by_id
        # Note: Production hasn't been refactored to modules yet, 
        # but we should adapt it to use context if possible. 
        # For now, we'll keep the old call but pass the necessary data.
        return get_production_obj_by_id(production_id, context)
    except NoDataFoundException as exp:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} "
            f"production_id '{production_id}' is not found"
        ) from exp