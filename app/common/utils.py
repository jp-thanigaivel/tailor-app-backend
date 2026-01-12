from app.core.dependencies import TenantContext
from app.utils.common_functions import DateUtils
from app.utils.app_constant import (
    RESOURCE_BODY_CREATED_ON,
    RESOURCE_BODY_UPDATED_ON,
    RESOURCE_BODY_CREATED_BY,
    RESOURCE_BODY_UPDATED_BY,
    RESOURCE_BODY_ORG_ID,
    RESOURCE_BODY_OWNER_ID,
    RESOURCE_BODY_BUSINESS_UNIT_ID
)

class MetadataUtils:
    @staticmethod
    def prepare_create_metadata(data: dict, user_id: str, context: TenantContext = None):
        """Sets creation and update metadata."""
        current_time = DateUtils.get_system_datetime_string()
        
        data[RESOURCE_BODY_CREATED_ON] = current_time
        data[RESOURCE_BODY_UPDATED_ON] = current_time
        data[RESOURCE_BODY_CREATED_BY] = user_id
        data[RESOURCE_BODY_UPDATED_BY] = user_id
        
        if context:
            data[RESOURCE_BODY_ORG_ID] = context.org_id
            data[RESOURCE_BODY_BUSINESS_UNIT_ID] = context.business_unit_id
            data[RESOURCE_BODY_OWNER_ID] = context.owner_id
            
        return data

    @staticmethod
    def prepare_update_metadata(data: dict, user_id: str):
        """Sets update metadata only."""
        data[RESOURCE_BODY_UPDATED_ON] = DateUtils.get_system_datetime_string()
        data[RESOURCE_BODY_UPDATED_BY] = user_id
        return data
