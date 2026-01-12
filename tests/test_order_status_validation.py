import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.modules.order.service import OrderService
from app.modules.order.schemas import UpdateOrderStatusRequest
from app.modules.order.models import OrderStatus, OrderItemStatus
from app.core.dependencies import TenantContext
from app.core.exceptions import InvalidRequestException

class TestOrderStatusValidation(unittest.TestCase):
    def setUp(self):
        self.context = TenantContext(user_id="test_user", org_id="test_org", business_unit_id="test_bu", roles=["user"])

    @patch('app.modules.order.service.order_repo.get')
    @patch('app.modules.order.service.order_item_repo.get_all')
    @patch('app.modules.order.service.order_repo.update')
    @patch('app.modules.order.service.order_audit_repo.create')
    @patch('app.modules.order.service.OrderService.get_order_by_id')
    def test_update_order_status_to_stitching_success(self, mock_get_by_id, mock_audit, mock_update, mock_get_items, mock_get_order):
        # Mocking Order
        mock_order = MagicMock()
        mock_order.order_status = OrderStatus.RECEIVED
        mock_get_order.return_value = mock_order
        
        # Mocking Items in CUTTING status (STITCHING status should not validate item status)
        mock_item = MagicMock()
        mock_item.order_item_status = OrderItemStatus.CUTTING
        mock_get_items.return_value = [mock_item]

        status_in = UpdateOrderStatusRequest(orderStatus=OrderStatus.STITCHING)
        OrderService.update_order_status(self.context, "ORD001", status_in)

        mock_update.assert_called_once()
        update_data = mock_update.call_args[0][2]
        self.assertEqual(update_data["orderStatus"], OrderStatus.STITCHING)

    @patch('app.modules.order.service.order_repo.get')
    @patch('app.modules.order.service.order_item_repo.get_all')
    def test_update_order_status_to_ready_failure(self, mock_get_items, mock_get_order):
        # Mocking Order
        mock_order = MagicMock()
        mock_order.order_status = OrderStatus.STITCHING
        mock_get_order.return_value = mock_order
        
        # Mocking Items in CUTTING status (READY needs all items to be READY)
        mock_item = MagicMock()
        mock_item.order_item_status = OrderItemStatus.CUTTING
        mock_item.item_id = "ITEM001"
        mock_get_items.return_value = [mock_item]

        status_in = UpdateOrderStatusRequest(orderStatus=OrderStatus.READY)
        
        with self.assertRaises(InvalidRequestException) as cm:
            OrderService.update_order_status(self.context, "ORD001", status_in)
        
        self.assertIn("All items must be READY", str(cm.exception.error_desc))

if __name__ == '__main__':
    unittest.main()
