from enum import Enum


class ConcreteGrade(str, Enum):
    M10 = "M10"
    M15 = "M15"
    M20 = "M20"
    M25 = "M25"
    M30 = "M30"

class PlacingMode(str, Enum):
    PUMP = "PUMP"
    DIRECT_POUR = "DIRECT POUR"
    CRANE = "CRANE"

class PlacingType(str, Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"

class MarketingOrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DELIVERED = "DELIVERED"

class MarketingModelKeyEnum(str, Enum):
    MARKETING_ID = 'marketing_id'
    ENQUIRY_DATE = 'enquiry_date'
    ORDER_STATUS = 'order_status'

class MarketingKeyEnum(str, Enum):
    MARKETING_ID = 'marketingId'
    ORDER_STATUS = 'orderStatus'