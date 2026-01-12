from app.db.base_repository import CRUDBase
from app.modules.customer.models import Customer

class CustomerRepository(CRUDBase[Customer]):
    def __init__(self):
        super().__init__(model=Customer, collection_name="customer")

customer_repo = CustomerRepository()
