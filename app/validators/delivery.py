from starlette import status

from app.constants.delivery import DeliveryStatus
from app.common.models import TokenData
from app.models.delivery import Delivery
from app.schemas.delivery import CreateDeliveryRequest, UpdateDeliveryRequest
from app.utils.app_constant import STATUS_DESC_INVALID_REQUEST, STATUS_TYPE_ERROR
from app.core.exceptions import InvalidRequestException
from app.validators.validate_common_service import validate_production, validate_customer


def validate_create_delivery_request(create_delivery_req: CreateDeliveryRequest,
                                    token_data: TokenData):
    production_id: str = create_delivery_req.production_id
    customer_id: str = create_delivery_req.customer_id
    validate_production(production_id, token_data)
    validate_customer(customer_id, token_data)

def validate_update_delivery_request(delivery: Delivery,
                                    update_delivery_req: UpdateDeliveryRequest,
                                    token_data: TokenData):
    delivery_status: DeliveryStatus = update_delivery_req.delivery_status
    db_delivery_status: DeliveryStatus = delivery.delivery_status
    if delivery_status is None:
        return
    valid_transitions = get_valid_transaction()
    allowed_next_statuses = valid_transitions.get(db_delivery_status, [])
    if delivery_status not in allowed_next_statuses:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} "
            f"delivery_status '{delivery_status}' is not allowed for update from current status "
            f"'{db_delivery_status}'"
        )

def get_valid_transaction() -> dict[DeliveryStatus, list[DeliveryStatus]]:
    valid_transitions = {
        DeliveryStatus.IN_TRANSIT: [DeliveryStatus.DELIVERED, DeliveryStatus.REJECTED],
    }
    return valid_transitions