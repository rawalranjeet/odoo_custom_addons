from odoo.tests.common import TransactionCase
from unittest.mock import patch


class TestMagentoInstance(TransactionCase):
    @classmethod
    def setUpClass(cls):

        super(TestMagentoInstance, cls).setUpClass()

        cls.instance = cls.env['magento.instance'].create({
            'name': 'Test1',
            'magento_store_base_url': 'http://test.com',
            'magento_username': 'admin',
            'magento_password': 'admin123',
        })

    def test_field_values(self):
      # Test the values of fields
        self.assertEqual(self.instance.name, 'Test1',
                        "Name field value is incorrect")
        self.assertEqual(self.instance.magento_store_base_url, 'http://test.com',
                        "magento_store_base_url field value is incorrect")
        self.assertEqual(self.instance.magento_username, 'admin',
                        "magento_username field value is incorrect")
        self.assertEqual(self.instance.magento_password, 'admin123',
                        "magento_password field value is incorrect")
        

    # token generate method
    @patch("odoo.addons.odoo_magento_connector.models.magento_instance.requests.post")
    def test_action_generate_access_token_success(self, mock_post):

        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "token123"

        import pdb; pdb.set_trace()
        result = self.instance.action_generate_access_token()
        
        self.assertEqual(self.instance.magento_access_token, 'token123', 'Access token not matching')
        
      

    # for success case
    @patch("odoo.addons.odoo_magento_connector.models.magento_instance.requests.get")
    def test_action_test_connection_success(self, mock_get):

        mock_get.return_value.status_code = 200
        
        # Test the action_test_connection method
        result = self.instance.action_test_connection()

        self.assertEqual(result['type'], 'ir.actions.client', "Type of action is incorrect")
        self.assertEqual(result['tag'], 'display_notification', "Tag of notification is incorrect")
        self.assertEqual(result['params']['type'], 'success', "Type of notification is incorrect")

    
    # for failed case
    @patch("odoo.addons.odoo_magento_connector.models.magento_instance.requests.get")
    def test_action_test_connection_failed(self, mock_get):

        mock_get.return_value.status_code = 400
        
        # Test the action_test_connection method
        result = self.instance.action_test_connection()

        self.assertEqual(result['type'], 'ir.actions.client', "Type of action is incorrect")
        self.assertEqual(result['tag'], 'display_notification', "Tag of notification is incorrect")
        self.assertEqual(result['params']['type'], 'danger', "Type of notification is incorrect")
        
        
    @classmethod
    def tearDownClass(cls):
    # Define this for cleanup operations, such as releasing resources
        super(TestMagentoInstance, cls).tearDownClass()