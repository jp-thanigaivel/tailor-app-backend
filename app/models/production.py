from datetime import datetime

from pydantic import Field, HttpUrl

from app.common.models import CreateEntity


class Production(CreateEntity):
    id: str = Field(default=None, alias="id")
    production_id: str = Field(..., alias="productionId")
    batch_date: datetime = Field(..., alias="batchDate")
    batch_start_date: datetime = Field(..., alias="batchStartDate")
    batch_end_date: datetime = Field(..., alias="batchEndDate")
    batch_number: str = Field(..., alias="batchNumber")
    customer_id: str = Field(..., alias="customerId")
    site_location: str = Field(..., alias="siteLocation")
    recipe_code: str = Field(..., alias="recipeCode")
    recipe_name: str = Field(..., alias="recipeName")
    truck_number: str = Field(..., alias="truckNumber")
    truck_driver: str = Field(..., alias="truckDriver")
    batcher_name: str = Field(..., alias="batcherName")
    plant_serial_number: str = Field(None, alias="plantSerialNumber")
    raw_material_stock: str = Field(None, alias="rawMaterialStock")
    plant_id: str = Field(..., alias="plantId")
    upload_pdf: list[HttpUrl] = Field(None, alias="uploadPDF")
    marketing_id: str = Field(..., alias="marketingId")

    class Config:
        populate_by_name = True
        use_enum_values = True