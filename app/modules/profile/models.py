from typing import Optional, List
from pydantic import Field
from app.common.models import BaseMongoModel

class Profile(BaseMongoModel):
    profile_id: str = Field(..., alias='profileId')
    customer_id: str = Field(..., alias='customerId')
    profile_name: str = Field(..., min_length=1, alias='profileName')
    relation: Optional[str] = Field(default=None)
    measurements: List[dict] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        use_enum_values = True
