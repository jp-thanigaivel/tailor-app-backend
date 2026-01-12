from starlette import status

from app.constants.customer import CustomerKeyEnum
from app.common.models import TokenData
from app.utils.app_constant import STATUS_TYPE_ERROR, STATUS_DESC_INVALID_REQUEST, RES_C_KEY_DATA
from app.core.exceptions import InvalidRequestException, NoDataFoundException


def pre_validation_for_delete(customer_id: str,token_data: TokenData):
    try:
        from app.service.production.production import get_all_production
        query_param = {CustomerKeyEnum.CUSTOMER_ID.value: customer_id}
        production_response: dict = get_all_production(query_param, token_data)
    except NoDataFoundException:
        return
    production_list = production_response.get(RES_C_KEY_DATA, [])
    if production_list:
        raise InvalidRequestException(
            status.HTTP_400_BAD_REQUEST,
            STATUS_TYPE_ERROR,
            f"{STATUS_DESC_INVALID_REQUEST} "
            f"Deletion not allowed for customer ID {customer_id} as it is currently "
            f"referenced in production records"
        )