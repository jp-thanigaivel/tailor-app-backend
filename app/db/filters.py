from typing import Dict, Any, Optional
from app.core.dependencies import TenantContext

def build_tenant_filter(context: TenantContext, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Automatically injects multi-tenancy filters based on the context.
    """
    tenant_filter = {
        "orgId": context.org_id,
        "businessUnitId": context.business_unit_id
    }
    
    # If a role dictates owner isolation, add owner_id to the filter
    if context.owner_id:
        tenant_filter["ownerId"] = context.owner_id

    if query:
        # If the query already has an $and, append to it
        if "$and" in query:
            query["$and"].append(tenant_filter)
            return query
        else:
            return {"$and": [tenant_filter, query]}
    
    return tenant_filter
