from starlette import status

from app.constants.marketing import MarketingOrderStatus, MarketingKeyEnum
from app.common.models import TokenData
from app.models.marketing import Marketing
from app.schemas.marketing import UpdateMarketingRequest, CreateMarketingRequest
from app.utils.app_constant import STATUS_TYPE_ERROR, STATUS_DESC_INVALID_REQUEST, RES_C_KEY_DATA
from app.core.exceptions import InvalidRequestException, NoDataFoundException
from app.validators.validate_common_service import validate_customer


def validate_create_marketing_request(create_marketing_req: CreateMarketingRequest,
                                    token_data: TokenData):
    customer_id: str = create_marketing_req.customer_id
    validate_customer(customer_id, token_data)


def validate_update_marking_request(marketing: Marketing,
                                    update_marketing_req: UpdateMarketingRequest,
                                    token_data: TokenData):
    customer_id: str = update_marketing_req.customer_id if update_marketing_req.customer_id else marketing.customer_id
    validate_customer(customer_id, token_data)

    marketing_status: MarketingOrderStatus = update_marketing_req.order_status
    db_marketing_status: MarketingOrderStatus = marketing.order_status
    if marketing_status is None:
        return
    valid_transitions = get_valid_transaction()
    allowed_next_statuses = valid_transitions.get(db_marketing_status, [])
    if marketing_status not in allowed_next_statuses:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} "
            f"marketing_status '{marketing_status}' is not allowed for update from current status "
            f"'{db_marketing_status}'"
        )

def pre_validation_for_delete(marketing_id: str,token_data: TokenData):
    try:
        from app.service.production.production import get_all_production
        query_param = {MarketingKeyEnum.MARKETING_ID.value: marketing_id}
        production_response: dict = get_all_production(query_param, token_data)
    except NoDataFoundException:
        return
    production_list = production_response.get(RES_C_KEY_DATA, [])
    if production_list:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} "
            f"Deletion not allowed for marketing ID {marketing_id} as it is currently "
            f"referenced in production records"
        )

def get_valid_transaction() -> dict[MarketingOrderStatus, list[MarketingOrderStatus]]:
    valid_transitions = {
        MarketingOrderStatus.PENDING: [MarketingOrderStatus.CONFIRMED],
        MarketingOrderStatus.CONFIRMED: [MarketingOrderStatus.PENDING, MarketingOrderStatus.DELIVERED],
        MarketingOrderStatus.DELIVERED: [],  # No further transitions allowed
    }
    return valid_transitions