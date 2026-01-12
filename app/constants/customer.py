from enum import Enum


class CustomerBizTypeEnum(str, Enum):
    INDIVIDUAL = 'INDIVIDUAL'
    ENTERPRISE = 'ENTERPRISE'


class CustomerModelKeyEnum(str, Enum):
    CUSTOMER_ID = 'customer_id'
    CUSTOMER_NAME = 'customer_name'

class CustomerKeyEnum(str, Enum):
    CUSTOMER_ID = 'customerId'
