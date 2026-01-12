from enum import Enum


class CreateEntityModelKeyEnum(str, Enum):
    CREATED_ON = 'created_on'
    UPDATED_ON = 'updated_on'
    CREATED_BY = 'created_by'
    UPDATED_BY = 'updated_by'
    ORG_ID = 'org_id'
    BUSINESS_UNIT_ID = 'business_unit_id'
    OWNER_ID = 'owner_id'
