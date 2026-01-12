from datetime import datetime

from pydantic import Field, HttpUrl
from typing_extensions import Optional

from app.constants.delivery import DeliveryStatus, QualityCheck, PlacingMode
from app.common.models import Quantity
from app.common.models import CreateSchema


class CreateDeliveryRequest(CreateSchema):
    production_id: str = Field(..., alias="productionId")
    marketing_id: str = Field(..., alias="marketingId")
    customer_id: str = Field(..., alias="customerId")
    batch_number: str = Field(..., alias="batchNumber")
    slump_value: Optional[float] = Field(None, alias="slumpValue")
    mode_of_unloading: Optional[PlacingMode] = Field(None, alias="modeOfUnloading")
    unloading_start_time: Optional[datetime] = Field(None, alias="unloadingStartTime")
    unloading_end_time: Optional[datetime] = Field(None, alias="unloadingEndTime")
    unloading_qty: Optional[Quantity] = Field(None, alias="unloadingQty")
    cube_casting: Optional[bool] = Field(None, alias="cubeCasting")
    site_photos: Optional[list[HttpUrl]] = Field(None, alias="sitePhotos")
    site_location: str = Field(..., alias='siteLocation')
    delivery_status: Optional[DeliveryStatus] = Field(None, alias="deliveryStatus")
    qc_approval: Optional[QualityCheck] = Field(None, alias="qcApproval")
    gps_coordinates: Optional[str] = Field(None, alias="gpsCoordinates")
    truck_capacity: Optional[float] = Field(None, alias="truckCapacity")
    operator_id: Optional[str] = Field(None, alias="operatorId")


class CreateDeliveryResponse(CreateSchema):
    delivery_id: str = Field(..., alias="deliveryId")
    production_id: str = Field(..., alias="productionId")
    marketing_id: str = Field(..., alias="marketingId")

class GetDeliveryResponse(CreateSchema):
    delivery_id: str = Field(..., alias="deliveryId")
    customer_id: str = Field(..., alias="customerId")
    production_id: str = Field(..., alias="productionId")
    marketing_id: str = Field(..., alias="marketingId")
    batch_number: str = Field(..., alias="batchNumber")
    delivery_status: DeliveryStatus = Field(default=DeliveryStatus.IN_TRANSIT, alias="deliveryStatus")
    slump_value: Optional[float] = Field(None, alias="slumpValue")
    mode_of_unloading: Optional[PlacingMode] = Field(None, alias="modeOfUnloading")
    unloading_start_time: Optional[datetime] = Field(None, alias="unloadingStartTime")
    unloading_end_time: Optional[datetime] = Field(None, alias="unloadingEndTime")
    unloading_qty: Optional[Quantity] = Field(None, alias="unloadingQty")
    cube_casting: Optional[bool] = Field(None, alias="cubeCasting")
    site_photos: Optional[list[HttpUrl]] = Field(None, alias="sitePhotos")
    site_location: str = Field(..., alias='siteLocation')
    qc_approval: Optional[QualityCheck] = Field(None, alias="qcApproval")
    gps_coordinates: Optional[str] = Field(None, alias="gpsCoordinates")
    truck_capacity: Optional[float] = Field(None, alias="truckCapacity")
    operator_id: Optional[str] = Field(None, alias="operatorId")

class UpdateDeliveryRequest(CreateSchema):
    delivery_id: str = Field(..., alias="deliveryId")
    customer_id: str = Field(None, alias="customerId")
    slump_value: Optional[float] = Field(None, alias="slumpValue")
    mode_of_unloading: Optional[PlacingMode] = Field(None, alias="modeOfUnloading")
    unloading_start_time: Optional[datetime] = Field(None, alias="unloadingStartTime")
    unloading_end_time: Optional[datetime] = Field(None, alias="unloadingEndTime")
    unloading_qty: Optional[Quantity] = Field(None, alias="unloadingQty")
    cube_casting: Optional[bool] = Field(None, alias="cubeCasting")
    site_photos: Optional[list[HttpUrl]] = Field(None, alias="sitePhotos")
    delivery_status: Optional[DeliveryStatus] = Field(None, alias="deliveryStatus")
    qc_approval: Optional[QualityCheck] = Field(None, alias="qcApproval")
    gps_coordinates: Optional[str] = Field(None, alias="gpsCoordinates")
    truck_capacity: Optional[float] = Field(None, alias="truckCapacity")
    operator_id: Optional[str] = Field(None, alias="operatorId")

class UpdateDeliveryResponse(CreateSchema):
    delivery_id: str = Field(..., alias="deliveryId")