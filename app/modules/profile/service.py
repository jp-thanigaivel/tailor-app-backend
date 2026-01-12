import logging
from typing import List, Optional
from fastapi import status
from datetime import datetime
from app.modules.profile.repository import profile_repo
from app.modules.customer.repository import customer_repo
from app.modules.profile.schemas import CreateProfileRequest, UpdateProfileRequest, ProfileResponse, MeasurementBase, MeasurementConfig
from app.core.dependencies import TenantContext
from app.core.exceptions import EntityAlreadyExistException, NoDataFoundException
from app.utils.common_functions import DBUtils
from app.utils.app_constant import COLL_TODO_SEQ_PROFILE_ID, SEQ_TODO_PROFILE_ID, PREFIX_SEQ_TODO_PROFILE_ID
from app.common.utils import MetadataUtils

logger = logging.getLogger(__name__)

class ProfileService:
    @staticmethod
    def create_profile(context: TenantContext, obj_in: CreateProfileRequest):
        logger.info(f"Creating profile for customer: {obj_in.customer_id}")
        
        # Validate Customer Existence - assuming we should validate against customer repo
        customer = customer_repo.get(context, {"customerId": obj_in.customer_id})
        if not customer:
             raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc=f"Customer with id {obj_in.customer_id} does not exist"
            )

        # Check for duplicates (customerId, profileName, relation)
        query = {
            "customerId": obj_in.customer_id,
            "profileName": obj_in.profile_name,
        }
        if obj_in.relation:
             query["relation"] = obj_in.relation
             
        existing = profile_repo.get(context, query)
        if existing:
            raise EntityAlreadyExistException(
                error_code=status.HTTP_400_BAD_REQUEST,
                error_type="ERROR",
                error_desc=f"Profile with name {obj_in.profile_name} and relation {obj_in.relation} already exists for this customer"
            )

        # Generate Profile ID
        profile_id = DBUtils.get_formatted_sequence(
            COLL_TODO_SEQ_PROFILE_ID, 
            SEQ_TODO_PROFILE_ID,
            PREFIX_SEQ_TODO_PROFILE_ID
        )
        
        # Prepare data for DB
        data = obj_in.model_dump(by_alias=True)
        data["profileId"] = profile_id
        
        # Add metadata
        MetadataUtils.prepare_create_metadata(data, context.user_id, context)
        
        profile_repo.create(context, data)
        return ProfileResponse(**data)

    @staticmethod
    def get_all_profiles(context: TenantContext, customer_id: Optional[str] = None, skip: int = 0, limit: int = 100):
        query = {}
        if customer_id:
            query["customerId"] = customer_id
            
        profiles = profile_repo.get_all(context, filter_query=query, skip=skip, limit=limit)
        return [ProfileResponse(**p.model_dump(by_alias=True)) for p in profiles]

    @staticmethod
    def get_profile_by_id(context: TenantContext, profile_id: str):
        profile = profile_repo.get(context, {"profileId": profile_id})
        if not profile:
            raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Profile not found"
            )
        return ProfileResponse(**profile.model_dump(by_alias=True))

    @staticmethod
    def update_profile(context: TenantContext, profile_id: str, obj_in: UpdateProfileRequest):
        existing_profile = profile_repo.get(context, {"profileId": profile_id})
        if not existing_profile:
             raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Profile not found"
            )
        
        # Check uniqueness if name or relation is changing
        if obj_in.profile_name or obj_in.relation:
            query = {
                "customerId": existing_profile.customer_id,
                "profileName": obj_in.profile_name or existing_profile.profile_name,
                "profileId": {"$ne": profile_id} # exclude self
            }
            # relation logic: if obj_in has relation, use it. Else use existing.
            # Handle implicit None vs explicit None? Request model defaults to None.
            # If user wants to unset relation, they might send empty string or we need consistent logic.
            # For now assuming optional update.
            
            new_relation = obj_in.relation if obj_in.relation is not None else existing_profile.relation
            if new_relation:
                query["relation"] = new_relation
            
            # Simple unique check: existing code checked (profileName, relation).
            # If relation is None in DB, query shouldn't look for it?
            # Let's match exact structure of create.
            
            duplicate = profile_repo.get(context, query)
            if duplicate:
                 raise EntityAlreadyExistException(
                    error_code=status.HTTP_400_BAD_REQUEST,
                    error_type="ERROR",
                    error_desc=f"Profile with name {query['profileName']} already exists for this customer"
                )

        data = obj_in.model_dump(exclude_unset=True, by_alias=True)
        MetadataUtils.prepare_update_metadata(data, context.user_id)
        
        updated = profile_repo.update(context, {"profileId": profile_id}, data)
        return ProfileResponse(**updated.model_dump(by_alias=True))

    @staticmethod
    def delete_profile(context: TenantContext, profile_id: str):
        success = profile_repo.delete(context, {"profileId": profile_id})
        if not success:
            raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Profile not found"
            )
        return success

    @staticmethod
    def add_measurement(context: TenantContext, profile_id: str, measurement_in: MeasurementBase):
        profile = profile_repo.get(context, {"profileId": profile_id})
        if not profile:
             raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Profile not found"
            )
        
        # Ensure measurements list exists
        if not hasattr(profile, 'measurements') or profile.measurements is None:
            profile.measurements = []

        # Generate Name if missing
        if not measurement_in.measurement_name:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            measurement_in.measurement_name = f"{measurement_in.measurement_type}_{timestamp}"

        # Check Uniqueness
        for m in profile.measurements:
            if m.get('measurementName') == measurement_in.measurement_name:
                raise EntityAlreadyExistException(
                    error_code=status.HTTP_400_BAD_REQUEST,
                    error_type="ERROR",
                    error_desc=f"Measurement with name {measurement_in.measurement_name} already exists for this profile"
                )

        # Append
        measurement_data = measurement_in.model_dump(by_alias=True)
        profile.measurements.append(measurement_data)
        
        # Update DB
        profile_repo.update(context, {"profileId": profile_id}, {"measurements": profile.measurements})
        
        return ProfileResponse(**profile.model_dump(by_alias=True))

    @staticmethod
    def update_measurement(context: TenantContext, profile_id: str, measurement_name: str, measurement_in: MeasurementBase):
        profile = profile_repo.get(context, {"profileId": profile_id})
        if not profile:
             raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Profile not found"
            )
            
        if not hasattr(profile, 'measurements') or not profile.measurements:
             raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc="Measurement not found"
            )

        # Find matching measurement
        target_index = -1
        for idx, m in enumerate(profile.measurements):
            if m.get('measurementName') == measurement_name:
                target_index = idx
                break
        
        if target_index == -1:
             raise NoDataFoundException(
                error_code=status.HTTP_404_NOT_FOUND,
                error_type="WARN",
                error_desc=f"Measurement with name {measurement_name} not found"
            )
            
        # Update logic
        # If user tries to change name, check uniqueness
        new_name = measurement_in.measurement_name
        if new_name and new_name != measurement_name:
             for idx, m in enumerate(profile.measurements):
                 if idx != target_index and m.get('measurementName') == new_name:
                    raise EntityAlreadyExistException(
                        error_code=status.HTTP_400_BAD_REQUEST,
                        error_type="ERROR",
                        error_desc=f"Measurement with name {new_name} already exists"
                    )
        elif not new_name:
             measurement_in.measurement_name = measurement_name

        measurement_data = measurement_in.model_dump(by_alias=True)
        profile.measurements[target_index] = measurement_data
        
        profile_repo.update(context, {"profileId": profile_id}, {"measurements": profile.measurements})
        
        return ProfileResponse(**profile.model_dump(by_alias=True))

    @staticmethod
    def get_measurement_config():
        return MeasurementConfig.ALLOWED_TYPES
