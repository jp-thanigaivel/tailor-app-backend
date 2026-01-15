import logging
from typing import Dict, Any
from fastapi import status
from app.modules.user.repository import user_repo
from app.modules.user.schemas import UserCreate, UserLogin, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthorizeException, EntityAlreadyExistException, NoDataFoundException
from app.utils.common_functions import DBUtils
from app.utils.app_constant import (
    COLL_TODO_SEQ_USER_ID, 
    SEQ_TODO_USER_ID, 
    PREFIX_SEQ_TODO_USER_ID,
    RESOURCE_BODY_ORG_ID,
    RESOURCE_BODY_BUSINESS_UNIT_ID,
    RESOURCE_BODY_OWNER_ID
)
from app.common.models import UserStatusEnum, RoleEnum
from app.common.utils import MetadataUtils

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def signup(obj_in: UserCreate):
        logger.info(f"Signing up user: {obj_in.phone_number}")
        
        # Check if user exists
        existing = user_repo.collection.find_one({"phoneNumber": obj_in.phone_number})
        if existing:
            raise EntityAlreadyExistException(
                error_code=status.HTTP_400_BAD_REQUEST,
                error_type="ERROR",
                error_desc="User already exists"
            )

        # Generate User ID
        user_id = DBUtils.get_formatted_sequence(
            COLL_TODO_SEQ_USER_ID, 
            SEQ_TODO_USER_ID,
            PREFIX_SEQ_TODO_USER_ID
        )
        
        data = obj_in.model_dump(by_alias=True)
        data["userId"] = user_id
        data["password"] = hash_password(obj_in.password)
        
        # Metadata
        MetadataUtils.prepare_create_metadata(data, user_id)
        
        # Identity fields for multi-tenancy
        data[RESOURCE_BODY_ORG_ID] = data.get(RESOURCE_BODY_ORG_ID) or user_id
        data[RESOURCE_BODY_BUSINESS_UNIT_ID] = data.get(RESOURCE_BODY_BUSINESS_UNIT_ID) or "default"
        data[RESOURCE_BODY_OWNER_ID] = user_id
        
        # Default fields (required by UserResponse)
        data["isActive"] = data.get("isActive") or UserStatusEnum.ACTIVE
        data["userRoles"] = data.get("userRoles") or [RoleEnum.USER]
        
        result = user_repo.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return UserResponse(**data)

    @staticmethod
    def signin(obj_in: UserLogin):
        logger.info(f"Signing in user: {obj_in.phone_number}")
        user_dict = user_repo.collection.find_one({"phoneNumber": obj_in.phone_number})
        if not user_dict:
            raise AuthorizeException(
                error_code=status.HTTP_401_UNAUTHORIZED,
                error_type="ERROR",
                error_desc="Invalid credentials"
            )
        
        if not verify_password(obj_in.password, user_dict["password"]):
            raise AuthorizeException(
                error_code=status.HTTP_401_UNAUTHORIZED,
                error_type="ERROR",
                error_desc="Invalid credentials"
            )

        # Generate tokens
        token_data = {
            "userId": user_dict["userId"],
            "orgId": user_dict["orgId"],
            "businessUnitId": user_dict["businessUnitId"],
            "userRoles": user_dict["userRoles"]
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }

    @staticmethod
    def refresh_token(authorization: str):
        logger.info("Refreshing token")
        try:
            if not authorization or not authorization.startswith("Bearer "):
                 raise AuthorizeException(
                    error_code=status.HTTP_401_UNAUTHORIZED,
                    error_type="ERROR",
                    error_desc="Invalid authorization header"
                )
            
            refresh_token = authorization.split(" ")[1]
            payload = decode_token(refresh_token, is_refresh=True)
            
            # Extract data for new tokens
            token_data = {
                "userId": payload.get("userId") or payload.get("user_id"),
                "orgId": payload.get("orgId") or payload.get("org_id"),
                "businessUnitId": payload.get("businessUnitId") or payload.get("business_unit_id"),
                "userRoles": payload.get("userRoles") or payload.get("user_roles", [])
            }
            
            new_access_token = create_access_token(token_data)
            new_refresh_token = create_refresh_token(token_data)
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer"
            }
        except AuthorizeException as e:
            raise e
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise AuthorizeException(
                error_code=status.HTTP_401_UNAUTHORIZED,
                error_type="ERROR",
                error_desc="Invalid refresh token"
            )
