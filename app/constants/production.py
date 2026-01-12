from enum import Enum


class ProductionModelKeyEnum(str, Enum):
    BATCH_NUMBER = 'batch_number'
    PRODUCTION_ID = 'production_id'

class ProductionKeyEnum(str, Enum):
    PRODUCTION_ID = 'productionId'
