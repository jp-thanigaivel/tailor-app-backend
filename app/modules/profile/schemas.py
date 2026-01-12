from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


class MeasurementConfig:
    ALLOWED_TYPES = {
    'SHIRT': ['CHEST', 'SHOULDER', 'SLEEVE_LENGTH', 'SHIRT_LENGTH', 'NECK', 'CUFF'],
    'PANT': ['WAIST', 'HIP', 'THIGH', 'KNEE', 'BOTTOM', 'LENGTH', 'INSEAM'],
    'KURTA': ['CHEST', 'SHOULDER', 'SLEEVE_LENGTH', 'KURTA_LENGTH', 'NECK'],
    'SUIT': ['CHEST', 'SHOULDER', 'SLEEVE_LENGTH', 'JACKET_LENGTH', 'WAIST', 'HIP'],
    'DRESS': ['CHEST', 'WAIST', 'HIP', 'SHOULDER', 'DRESS_LENGTH', 'SLEEVE_LENGTH']
    }

class MeasurementBase(BaseModel):
    measurement_type: str = Field(..., alias='measurementType')
    measurement_name: Optional[str] = Field(None, alias='measurementName')
    measurement_json: dict = Field(..., alias='measurementJson')

    @field_validator('measurement_type')
    def validate_type(cls, v):
        if v not in MeasurementConfig.ALLOWED_TYPES:
            raise ValueError(f"Invalid measurement type. Allowed types: {', '.join(MeasurementConfig.ALLOWED_TYPES.keys())}")
        return v

    @model_validator(mode='after')
    def validate_measurement_json(self):
        m_type = self.measurement_type
        m_json = self.measurement_json
        
        allowed_keys = set(MeasurementConfig.ALLOWED_TYPES.get(m_type, []))
        provided_keys = set(m_json.keys())
        
        # Check for invalid keys
        invalid_keys = provided_keys - allowed_keys
        if invalid_keys:
            raise ValueError(f"Invalid keys for {m_type}: {', '.join(invalid_keys)}. Allowed keys: {', '.join(allowed_keys)}")
            
        # Check for missing keys
        missing_keys = allowed_keys - provided_keys
        if missing_keys:
             raise ValueError(f"Missing keys for {m_type}: {', '.join(missing_keys)}. Required keys: {', '.join(allowed_keys)}")

        return self

    class Config:
        populate_by_name = True

class ProfileBase(BaseModel):
    customer_id: str = Field(..., alias='customerId')
    profile_name: str = Field(..., min_length=1, alias='profileName')
    relation: Optional[str] = Field(None)

    class Config:
        populate_by_name = True
        use_enum_values = True

class CreateProfileRequest(ProfileBase):
    pass

class UpdateProfileRequest(BaseModel):
    profile_name: Optional[str] = Field(None, min_length=1, alias='profileName')
    relation: Optional[str] = Field(None)

    class Config:
        populate_by_name = True
        use_enum_values = True

class ProfileResponse(ProfileBase):
    profile_id: str = Field(..., alias='profileId')
    id: Optional[str] = Field(None, alias='id')
    measurements: List[MeasurementBase] = Field(default_factory=list)

