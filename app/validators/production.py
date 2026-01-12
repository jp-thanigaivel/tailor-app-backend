from starlette import status

from app.constants.marketing import MarketingOrderStatus
from app.constants.production import ProductionKeyEnum
from app.common.models import TokenData
from app.models.production import Production
from app.schemas.production import CreateProductionRequest, UpdateProductionRequest
from app.service.delivery.delivery import get_all_deliveries
from app.service.marketing.marketing import get_marketing_obj_by_id
from app.utils.app_constant import STATUS_DESC_INVALID_REQUEST, STATUS_TYPE_ERROR, RES_C_KEY_DATA
from app.core.exceptions import InvalidRequestException, NoDataFoundException
from app.validators.validate_common_service import validate_customer


def validate_marketing_for_production(marketing_id: str, token_data: TokenData):
    try:
        marketing = get_marketing_obj_by_id(marketing_id, token_data)
        if marketing.order_status != MarketingOrderStatus.CONFIRMED.value:
            raise InvalidRequestException(
                status.HTTP_400_BAD_REQUEST,
                STATUS_TYPE_ERROR,
                f"{STATUS_DESC_INVALID_REQUEST} "
                f"marketing_status '{marketing.order_status}' is not allowed for update production"
            )
    except NoDataFoundException as exp:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} marketing_id '{marketing_id}' is not found"
        ) from exp



def validate_delivery_for_production(production_id: str, token_data: TokenData):
    try:
        from app.service.production.production import get_all_production
        query_param = {ProductionKeyEnum.PRODUCTION_ID.value: production_id}
        delivery_response: dict = get_all_deliveries(query_param, token_data)
    except NoDataFoundException:
        return
    delivery_list = delivery_response.get(RES_C_KEY_DATA, [])
    if delivery_list:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} "
            f"Update not allowed for production ID {production_id} as it is currently "
            f"referenced in delivery records"
        )


def validate_create_production_request(create_production_req: CreateProductionRequest,
                                    token_data: TokenData):
    marketing_id: str = create_production_req.marketing_id
    customer_id: str =create_production_req.customer_id
    validate_marketing_for_production(marketing_id, token_data)
    validate_customer(customer_id, token_data)

def validate_update_production_request(production: Production,
                                    update_production_req: UpdateProductionRequest,
                                    token_data: TokenData):
    marketing_id: str = update_production_req.marketing_id if update_production_req.marketing_id else production.marketing_id
    customer_id: str = update_production_req.customer_id if update_production_req.customer_id else production.customer_id
    production_id: str = production.production_id
    validate_marketing_for_production(marketing_id, token_data)
    validate_customer_for_production(customer_id, token_data)
    validate_delivery_for_production(production_id, token_data)

