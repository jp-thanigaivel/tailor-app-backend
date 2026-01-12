from typing import List, Optional
from fastapi import Request, Depends, status
from pydantic import BaseModel
from app.core.exceptions import AuthorizeException

class TenantContext(BaseModel):
    org_id: str
    business_unit_id: str
    user_id: str
    roles: List[str]
    owner_id: Optional[str] = None

def get_tenant_context(request: Request) -> TenantContext:
    if not hasattr(request.state, "tenant_context"):
        raise AuthorizeException(
            error_code=status.HTTP_401_UNAUTHORIZED,
            error_type="ERROR",
            error_desc="Tenant context not found"
        )
    return request.state.tenant_context

def get_db(request: Request):
    return request.app.state.db_client
