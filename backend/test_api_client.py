from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch
import uuid

from sdk import ECommerceClient


class ECommerceClientTest(SimpleTestCase):
    def test_get_products_fetches_data(self):
        test_token = uuid.uuid4().hex
        client = ECommerceClient("http://example.com", token=test_token)
        with patch.object(client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"results": []}
            mock_get.return_value = mock_response

            data = client.get_products()

            mock_get.assert_called_once_with(
                "http://example.com/api/v1/products/", params=None
            )
            self.assertEqual(data, {"results": []})

    def test_token_header_set_on_init(self):
        test_token = uuid.uuid4().hex
        client = ECommerceClient("http://example.com", token=test_token)
        self.assertEqual(
            client.session.headers["Authorization"], f"Bearer {test_token}"
        )
