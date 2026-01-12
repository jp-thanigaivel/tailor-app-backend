import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.modules.order.service import OrderService
from app.modules.order.schemas import CreateOrderRequest
from app.modules.order.models import OrderType, OrderStatus
from app.core.dependencies import TenantContext
from app.core.exceptions import NoDataFoundException

class TestOrderServiceCustomerValidation(unittest.TestCase):
    def setUp(self):
        self.context = TenantContext(user_id="test_user", org_id="test_org", business_unit_id="test_bu", roles=["user"])

    @patch('app.modules.order.service.CustomerService.get_customer_by_id')
    @patch('app.modules.order.service.DBUtils.get_formatted_sequence')
    @patch('app.modules.order.service.order_repo.create')
    @patch('app.modules.order.service.order_audit_repo.create')
    def test_create_order_valid_customer(self, mock_audit_create, mock_order_create, mock_seq, mock_get_customer):
        # Mocking Customer
        mock_customer = MagicMock()
        mock_customer.customer_id = "CUST001"
        mock_customer.phone_number = MagicMock()
        mock_customer.phone_number.model_dump.return_value = {
            "countryCode": 91,
            "phoneNumber": "9876543210"
        }
        mock_customer.customer_address = MagicMock()
        mock_customer.customer_address.model_dump.return_value = {
            "addressLine1": "Line 1",
            "city": "City",
            "district": "District",
            "state": "State",
            "country": "India",
            "postalCode": 123456
        }
        mock_get_customer.return_value = mock_customer
        
        mock_seq.return_value = "ORD001"

        obj_in = CreateOrderRequest(
            customerId="CUST001",
            orderType=OrderType.INDIVIDUAL,
            orderStatus=OrderStatus.DRAFT,
            orderNotes="Test Order"
        )

        response = OrderService.create_order(self.context, obj_in)

        # Assertions
        self.assertEqual(response.order_id, "ORD001")
        self.assertEqual(response.customer_id, "CUST001")
        self.assertEqual(response.customer_phone_number.phone_number, "9876543210")
        self.assertEqual(response.customer_address.address_line1, "Line 1")
        mock_get_customer.assert_called_once_with(self.context, "CUST001")
        mock_order_create.assert_called_once()
        
        # Verify the data sent to repo
        order_data_sent = mock_order_create.call_args[0][1]
        self.assertEqual(order_data_sent["customerAddress"]["addressLine1"], "Line 1")

    @patch('app.modules.order.service.CustomerService.get_customer_by_id')
    def test_create_order_invalid_customer(self, mock_get_customer):
        mock_get_customer.side_effect = NoDataFoundException(404, "WARN", "Customer not found")

        obj_in = CreateOrderRequest(
            customerId="INVALID",
            orderType=OrderType.INDIVIDUAL,
            orderStatus=OrderStatus.DRAFT
        )

        with self.assertRaises(NoDataFoundException):
            OrderService.create_order(self.context, obj_in)

if __name__ == '__main__':
    unittest.main()
