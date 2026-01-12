import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_token
from app.core.dependencies import TenantContext
from app.core.exceptions import AuthorizeException, get_standard_response

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        # public endpoints
        public_paths = [
            "/user/signin", 
            "/user/signup", 
            "/user/otp", 
            "/user/otp/verify", 
            "/user/token/refresh",
            "/docs", 
            "/openapi.json"
        ]

        if any(path in request.url.path for path in public_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=get_standard_response(status.HTTP_401_UNAUTHORIZED, "ERROR", "Authentication required")
            )

        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
            
            # Extract tenant information
            org_id = payload.get("org_id")
            business_unit_id = payload.get("businessUnitId") or payload.get("business_unit_id")
            user_id = payload.get("user_id")
            roles = payload.get("user_roles", [])

            # owner_id derivation logic (simplified for now)
            # If the user is a standard 'user', they can only see their own data
            # This can be refined based on ROLES configuration
            owner_id = user_id if "user" in roles and "admin" not in roles else None

            request.state.tenant_context = TenantContext(
                org_id=org_id,
                business_unit_id=business_unit_id or "default", # Fallback if not in token yet
                user_id=user_id,
                roles=roles,
                owner_id=owner_id
            )
            
        except AuthorizeException as e:
            return JSONResponse(
                status_code=e.status_code,
                content=get_standard_response(e.status_code, e.error_type, e.error_desc, e.error_code)
            )
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=get_standard_response(status.HTTP_401_UNAUTHORIZED, "ERROR", "Invalid or expired token")
            )

        return await call_next(request)
