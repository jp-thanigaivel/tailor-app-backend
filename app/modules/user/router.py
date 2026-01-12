from fastapi import APIRouter, Depends, Query, Header
from app.modules.user.service import UserService
from app.modules.user.schemas import UserCreate, UserLogin, UserResponse
from app.core.exceptions import get_standard_response
from starlette import status

router = APIRouter(tags=["User"])

@router.post("/user/signup", status_code=status.HTTP_201_CREATED)
async def signup(obj_in: UserCreate):
    data = UserService.signup(obj_in)
    return {
        "status": get_standard_response(status.HTTP_201_CREATED, "SUCCESS", "User created successfully")["status"],
        "data": data
    }

@router.post("/user/signin")
async def signin(obj_in: UserLogin):
    data = UserService.signin(obj_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Login successful")["status"],
        "data": data
    }

@router.post("/user/token/refresh")
async def refresh_token(authorization: str = Header(..., alias="Authorization")):
    data = UserService.refresh_token(authorization)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Token refreshed successfully")["status"],
        "data": data
    }
