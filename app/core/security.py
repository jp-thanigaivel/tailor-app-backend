import bcrypt
from datetime import datetime, timedelta

# Fix for passlib compatibility with bcrypt 4.x
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type('About', (object,), {'__version__': bcrypt.__version__})

from typing import Optional, Any, Dict, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import status

from app.core.config import get_app_secret
from app.core.exceptions import AuthorizeException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    secret_config = get_app_secret().auth_config
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=secret_config.access_token_expire_minutes)
    
    # Existing logic uses 'expiry' as timestamp in payload
    to_encode.update({"exp": expire, "expiry": expire.timestamp()})
    return jwt.encode(to_encode, secret_config.access_secret_key, algorithm=secret_config.algorithm)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    secret_config = get_app_secret().auth_config
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=secret_config.refresh_token_expire_minutes)
    
    to_encode.update({"exp": expire, "expiry": expire.timestamp()})
    return jwt.encode(to_encode, secret_config.refresh_secret_key, algorithm=secret_config.algorithm)

def decode_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    secret_config = get_app_secret().auth_config
    secret_key = secret_config.refresh_secret_key if is_refresh else secret_config.access_secret_key
    try:
        payload = jwt.decode(token, secret_key, algorithms=[secret_config.algorithm])
        return payload
    except JWTError as e:
        raise AuthorizeException(
            error_code=status.HTTP_401_UNAUTHORIZED,
            error_type="ERROR",
            error_desc=f"Invalid token: {str(e)}"
        )
