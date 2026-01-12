from app.db.base_repository import CRUDBase
from app.modules.order.models import Order, OrderItem, PaymentDetail, OrderAudit
from app.utils.app_constant import COLL_TODO_ORDER, COLL_TODO_ORDER_ITEM, COLL_TODO_PAYMENT, COLL_TODO_ORDER_AUDIT

class OrderRepository(CRUDBase[Order]):
    pass

class OrderItemRepository(CRUDBase[OrderItem]):
    pass

class PaymentRepository(CRUDBase[PaymentDetail]):
    pass

class OrderAuditRepository(CRUDBase[OrderAudit]):
    pass

order_repo = OrderRepository(Order, COLL_TODO_ORDER)
order_item_repo = OrderItemRepository(OrderItem, COLL_TODO_ORDER_ITEM)
payment_repo = PaymentRepository(PaymentDetail, COLL_TODO_PAYMENT)
order_audit_repo = OrderAuditRepository(OrderAudit, COLL_TODO_ORDER_AUDIT)
