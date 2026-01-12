from enum import Enum


class PlacingMode(str, Enum):
    PUMP = "PUMP"
    DIRECT_POUR = "DIRECT POUR"
    CRANE = "CRANE"

class DeliveryStatus(str, Enum):
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"

class QualityCheck(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class DeliveryModelKeyEnum(str, Enum):
    DELIVERY_ID = 'delivery_id'

class DeliveryKeyEnum(str, Enum):
    DELIVERY_ID = 'deliveryId'