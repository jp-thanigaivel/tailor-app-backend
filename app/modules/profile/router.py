from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_tenant_context, TenantContext
from app.modules.profile.service import ProfileService
from app.modules.profile.schemas import CreateProfileRequest, UpdateProfileRequest, ProfileResponse, MeasurementBase
from app.core.exceptions import get_standard_response
from starlette import status
from typing import Optional

router = APIRouter(tags=["Profile"])

@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_profile(
    obj_in: CreateProfileRequest, 
    context: TenantContext = Depends(get_tenant_context)
):
    data = ProfileService.create_profile(context, obj_in)
    return {
        "status": get_standard_response(status.HTTP_201_CREATED, "SUCCESS", "Profile created successfully")["status"],
        "data": data
    }

@router.get("/profiles")
async def get_profiles(
    customer_id: Optional[str] = Query(None, alias="customerId"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    context: TenantContext = Depends(get_tenant_context)
):
    data = ProfileService.get_all_profiles(context, customer_id=customer_id, skip=skip, limit=limit)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.get("/profile/{profile_id}")
async def get_profile(
    profile_id: str,
    context: TenantContext = Depends(get_tenant_context)
):
    data = ProfileService.get_profile_by_id(context, profile_id)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }

@router.patch("/profile/{profile_id}")
async def update_profile(
    profile_id: str,
    obj_in: UpdateProfileRequest,
    context: TenantContext = Depends(get_tenant_context)
):
    data = ProfileService.update_profile(context, profile_id, obj_in)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Profile updated successfully")["status"],
        "data": data
    }

@router.delete("/profile/{profile_id}")
async def delete_profile(
    profile_id: str,
    context: TenantContext = Depends(get_tenant_context)
):
    ProfileService.delete_profile(context, profile_id)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Profile deleted successfully")["status"],
        "data": ""
    }

@router.post("/{profile_id}/measurements", response_model=None)
async def add_measurement(
    profile_id: str,
    measurement: MeasurementBase,
    context: TenantContext = Depends(get_tenant_context)
):
    data = ProfileService.add_measurement(context, profile_id, measurement)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Measurement added successfully")["status"],
        "data": data
    }

@router.put("/{profile_id}/measurements/{measurement_name}", response_model=None)
async def update_measurement(
    profile_id: str,
    measurement_name: str,
    measurement: MeasurementBase,
    context: TenantContext = Depends(get_tenant_context)
):
    data = ProfileService.update_measurement(context, profile_id, measurement_name, measurement)
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Measurement updated successfully")["status"],
        "data": data
    }

@router.get("/profiles/measurements/config", response_model=None)
async def get_measurement_config(
    context: TenantContext = Depends(get_tenant_context)
):
    data = ProfileService.get_measurement_config()
    return {
        "status": get_standard_response(status.HTTP_200_OK, "SUCCESS", "Success")["status"],
        "data": data
    }
