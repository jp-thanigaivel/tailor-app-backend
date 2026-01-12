from datetime import datetime

from pydantic import Field, HttpUrl
from typing_extensions import Optional

from app.constants.delivery import PlacingMode, DeliveryStatus, QualityCheck
from app.common.models import CreateEntity, Quantity


class Delivery(CreateEntity):
    id: str = Field(default=None, alias="id")
    delivery_id: str = Field(..., alias="deliveryId")
    production_id: str = Field(..., alias="productionId")
    marketing_id: str = Field(..., alias="marketingId")
    site_location: str = Field(..., alias='siteLocation')
    customer_id: str = Field(..., alias="customerId")
    batch_number: str = Field(..., alias="batchNumber")
    delivery_status: DeliveryStatus = Field(default=DeliveryStatus.IN_TRANSIT, alias="deliveryStatus")
    slump_value: Optional[float] = Field(None, alias="slumpValue")
    mode_of_unloading: Optional[PlacingMode] = Field(None, alias="modeOfUnloading")
    unloading_start_time: Optional[datetime] = Field(None, alias="unloadingStartTime")
    unloading_end_time: Optional[datetime] = Field(None, alias="unloadingEndTime")
    unloading_qty: Optional[Quantity] = Field(None, alias="unloadingQty")
    cube_casting: Optional[bool] = Field(None, alias="cubeCasting")
    site_photos: Optional[list[HttpUrl]] = Field(None, alias="sitePhotos")
    qc_approval: Optional[QualityCheck] = Field(None, alias="qcApproval")
    gps_coordinates: Optional[str] = Field(None, alias="gpsCoordinates")
    truck_capacity: Optional[float] = Field(None, alias="truckCapacity")
    operator_id: Optional[str] = Field(None, alias="operatorId")

    class Config:
        populate_by_name = True
        use_enum_values = True