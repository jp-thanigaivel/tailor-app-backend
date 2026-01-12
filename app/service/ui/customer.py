import logging

from starlette import status

from app.constants.customer import CustomerBizTypeEnum
from app.constants.delivery import DeliveryStatus, QualityCheck
from app.constants.marketing import ConcreteGrade, PlacingMode, PlacingType
from app.dependencies.database.mongodb.database import MongoDBClient
from app.utils.app_constant import STATUS_TYPE_WARN, STATUS_DESC_NO_DATA
from app.core.exceptions import NoDataFoundException

logger = logging.getLogger(__name__)

db_client = MongoDBClient().get_client()


def get_drop_down_list(dropdown_name: str) -> list[str]:
    match dropdown_name:
        case "CustomerBizType":
            return [item.value for item in CustomerBizTypeEnum]
        case "ConcreteGrade":
            return [item.value for item in ConcreteGrade]
        case "PlacingMode":
            return [item.value for item in PlacingMode]
        case "PlacingType":
            return [item.value for item in PlacingType]
        case "DeliveryStatus":
            return [item.value for item in DeliveryStatus]
        case "QualityCheck":
            return [item.value for item in QualityCheck]
        case _:
            raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " dropdown_name: " + str(dropdown_name))