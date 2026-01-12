import logging
import traceback
from typing import Any, Optional, Dict, List, Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.utils.app_constant import (
    STATUS_TYPE_ERROR,
    INTERNAL_ERROR_CODE_BAD_REQUEST,
    INTERNAL_ERROR_CODE_SERVER_ERROR,
    INTERNAL_ERROR_CODE_VALIDATION_ERROR
)

logger = logging.getLogger(__name__)

class BaseAppException(Exception):
    def __init__(
        self, 
        error_code: Any, 
        error_type: str, 
        error_desc: str,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> None:
        self.error_code = error_code
        self.error_type = error_type
        self.error_desc = error_desc
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.error_code} {self.error_desc}"

# Specific Exceptions
class InvalidRequestException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str) -> None:
        super().__init__(error_code, error_type, error_desc, status.HTTP_400_BAD_REQUEST)

class NoDataFoundException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str) -> None:
        super().__init__(error_code, error_type, error_desc, status.HTTP_404_NOT_FOUND)

class EntityAlreadyExistException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str) -> None:
        super().__init__(error_code, error_type, error_desc, status.HTTP_400_BAD_REQUEST)

class AuthorizeException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str, status_code: int = status.HTTP_401_UNAUTHORIZED) -> None:
        super().__init__(error_code, error_type, error_desc, status_code)

class DataBaseException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str) -> None:
        super().__init__(error_code, error_type, error_desc, status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str) -> None:
        super().__init__(error_code, error_type, error_desc, status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotImplementedException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str) -> None:
        super().__init__(error_code, error_type, error_desc, status.HTTP_501_NOT_IMPLEMENTED)

class NotAllowedException(BaseAppException):
    def __init__(self, error_code: Any, error_type: str, error_desc: str) -> None:
        super().__init__(error_code, error_type, error_desc, status.HTTP_403_FORBIDDEN)

# Other exceptions from existing codebase
class EntityNotExistException(BaseAppException): pass
class InvalidCredentialsException(BaseAppException): pass
class EntityNotActiveException(BaseAppException): pass
class PaymentException(BaseAppException): pass
class PaymentGatewayException(BaseAppException): pass
class InvalidPaymentTypeException(BaseAppException): pass
class InvalidDocumentStorageTypeException(BaseAppException): pass
class PaymentGatewayError(BaseAppException): pass
class InvalidPaymentException(BaseAppException): pass
class ProcessStepNotFoundException(BaseAppException): pass
class NoConfigFoundException(BaseAppException): pass
class InvalidException(BaseAppException): pass
class OtpGenerationException(BaseAppException): pass
class NotMatchException(BaseAppException): pass
class OTPExpiredException(BaseAppException): pass
class InvalidNotificationChannelException(BaseAppException): pass
class NotificationException(BaseAppException): pass
class DependentServiceException(BaseAppException): pass
class DocumentCreationException(BaseAppException): pass
class InvalidOTelExporterException(BaseAppException): pass
class UnInitializedException(BaseAppException): pass

def get_standard_response(status_code: int, error_type: str, error_desc: str, error_code: Any = None, data: Any = ""):
    return {
        "status": {
            "statusCode": str(error_code or status_code),
            "statusType": error_type,
            "statusDesc": error_desc
        },
        "data": data
    }

async def app_exception_handler(request: Request, exc: BaseAppException):
    logger.error(f"{exc.__class__.__name__}: {exc}")
    content = get_standard_response(exc.status_code, exc.error_type, exc.error_desc, exc.error_code)
    return JSONResponse(status_code=exc.status_code, content=content)

async def validation_exception_handler(request: Request, exc: Union[RequestValidationError, ValidationError]):
    # Extract clean error messages
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg")
        error_details.append(f"[{loc}]: {msg}")
    
    clean_error_desc = " | ".join(error_details)
    logger.error(f"ValidationError: {clean_error_desc}")
    
    content = get_standard_response(
        status_code=status.HTTP_400_BAD_REQUEST, 
        error_type=STATUS_TYPE_ERROR, 
        error_desc=clean_error_desc, 
        error_code=INTERNAL_ERROR_CODE_VALIDATION_ERROR
    )
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)

async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    logger.error(f"Unhandled Exception: {str(exc)}")
    content = get_standard_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
        error_type=STATUS_TYPE_ERROR, 
        error_desc=f"Internal Server Error: {str(exc)}",
        error_code=INTERNAL_ERROR_CODE_SERVER_ERROR
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
