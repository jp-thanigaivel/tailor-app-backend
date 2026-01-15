from enum import Enum


class CreateEntityModelKeyEnum(str, Enum):
    CREATED_ON = 'createdOn'
    UPDATED_ON = 'updatedOn'
    CREATED_BY = 'createdBy'
    UPDATED_BY = 'updatedBy'
    ORG_ID = 'orgId'
    BUSINESS_UNIT_ID = 'businessUnitId'
    OWNER_ID = 'ownerId'
