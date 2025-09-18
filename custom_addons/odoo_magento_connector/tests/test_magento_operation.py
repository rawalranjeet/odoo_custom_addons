from odoo.tests.common import TransactionCase
from unittest.mock import patch


class TestMagentoOperation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestMagentoOperation, cls).setUpClass()
        cls.Wizard = cls.env['magento.operation.wizard']
        cls.instance = cls.env['magento.instance'].create({
            'name': 'Test Instance',
            'magento_store_base_url': 'http://magento.test',
            'magento_access_token': 'test_token',
            "magento_username": "admin",
            "magento_password": "admin123"
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test_customer@example.com',
            'dob': '2001-01-01',
            'gender': 'male',
        })

        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Product',
            'default_code':  'TEST-PRODUCT',
            'is_storable': True,
            'type': 'consu',
            'list_price': 89,
        })


    

    # IMPORT <-------------
    @patch("requests.get")
    def test_import_products_from_magento(self, mock_get):

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = { "items": [
            {
                "id": 1,
                "sku": "24-MB01",
                "name": "Joust Duffle Bag",
                "price": 34,
                "type_id": "simple",
            },
            {
                "id": 2,
                "sku": "26-MB02",
                "name": "Joust Duffle Bag Blue",
                "price": 57,
                "type_id": "simple",
            },

        ], "total_count": 2 }



        wizard = self.Wizard.create({
            'magento_instance_id': self.instance.id,
            'operation_type': 'import',
            'operation_sub_type': 'products',
        })

        
        result = wizard.action_confirm()


        # checking the product added or not
        product1 = self.env['product.template'].search([('default_code', '=', '24-MB01'), ('magento_instance_id','=', self.instance.id)])
        self.assertTrue(product1)

        product2 = self.env['product.template'].search([('default_code', '=', '26-MB02'), ('magento_instance_id','=', self.instance.id)])
        self.assertTrue(product2)

        
    @patch("requests.get")
    def test_import_customers_from_magento(self, mock_get):

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = { "items": [
            {
                "id": 1,
                "dob": "1973-12-15",
                "email": "roni_cost@example.com",
                "firstname": "Veronica",
                "lastname": "Costello",
                "gender": 2,
            },
            {
                "id": 123,
                "dob": "2001-12-15",
                "email": "test_user@gmail.com",
                "firstname": "Testing",
                "middlename": "User",
                "lastname": "Magento",
                "gender": 1,
                "addresses": [
                    {
                        "id": 1,
                        "customer_id": 123,
                        "region": {
                            "region_code": "MI",
                            "region": "Michigan",
                            "region_id": 33
                        },
                        "region_id": 33,
                        "country_id": "US",
                        "street": [
                            "6146 Honey Bluff Parkway"
                        ],
                        "telephone": "(555) 229-3326",
                        "postcode": "49628-7978",
                        "city": "Calder",
                        "firstname": "Testing",
                        "middlename": "User",
                        "lastname": "Magento",
                    }
                ],
            },

        ], "total_count": 2}



        wizard = self.Wizard.create({
            'magento_instance_id': self.instance.id,
            'operation_type': 'import',
            'operation_sub_type': 'customers',
        })


        result = wizard.action_confirm()

        # checking the customers added or not
        customer1 = self.env['res.partner'].search([('email', '=', 'roni_cost@example.com')])
        self.assertTrue(customer1)

        customer2 = self.env['res.partner'].search([('email', '=', 'test_user@gmail.com')])
        self.assertTrue(customer2)

    @patch("requests.get")
    def test_import_orders_from_magento(self, mock_get):

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "items": [{
                "entity_id": 42,
                "customer_email": "jane.doe@example.com",
                "items": [{
                    "order_id": 42,
                    "sku": "SKU-ORDER-PROD",
                    "qty_ordered": 2,
                    "base_price": 55,
                    "tax_percent": 10,
                }]
            }, {
                "entity_id": 43,
                "customer_email": "john.doe@example.com",
                "items": [{
                    "order_id": 43,
                    "sku": "SKU-ORDER-PROD-2",
                    "qty_ordered": 1,
                    "base_price": 75,
                    "tax_percent": 15,
                }, {
                    "order_id": 43,
                    "sku": "SKU-ORDER-PROD",
                    "qty_ordered": 3,
                    "base_price": 50,
                    "tax_percent": 10,
                }]
            },
                {
                "entity_id": 44,
                "customer_email": "no_user@gmail.com",
                "items": [{
                    "order_id": 44,
                    "sku": "SKU-ORDER-PROD-3",
                    "qty_ordered": 10,
                    "base_price": 100,
                    "tax_percent": 100,
                },]
            }
            ],
            "total_count": 3,
        }

        # Pre-create the customer and product that the order refers to (except order number 44)
        self.env['res.partner'].create({
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'magento_instance_id': self.instance.id,
            'magento_customer_id' : 1000,
        })

        self.env['res.partner'].create({
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'magento_instance_id': self.instance.id,
            'magento_customer_id' : 1001,
        })

        self.env['product.template'].create({
            'name': 'Ordered Product',
            'magento_sku_id': 'SKU-ORDER-PROD',
            'magento_instance_id': self.instance.id,
            'default_code': 'SKU-ORDER-PROD',
            'is_storable': True,
            'type': 'consu',
            'list_price': 55,
        })

        self.env['product.template'].create({
            'name': 'Another Ordered Product',
            'magento_sku_id': 'SKU-ORDER-PROD-2',
            'magento_instance_id': self.instance.id,
            'default_code': 'SKU-ORDER-PROD-2',
            'is_storable': True,
            'type': 'consu',
            'list_price': 75,
        })

        wizard = self.Wizard.create({
            'magento_instance_id': self.instance.id,
            'operation_type': 'import',
            'operation_sub_type': 'orders',
        })

        result = wizard.action_confirm()

        # Check that the API was called
        mock_get.assert_called_once()
        
        # Check that the sale order was created correctly
        sale_order = self.env['sale.order'].search([('magento_order_id', '=', '42')])
        self.assertTrue(sale_order, "Sale order should have been created.")
        self.assertEqual(sale_order.magento_instance_id, self.instance)
        self.assertEqual(sale_order.partner_id.email, 'jane.doe@example.com')

        # Check that the sale order line was created correctly
        self.assertEqual(len(sale_order.order_line), 1)
        order_line = sale_order.order_line[0]
        self.assertEqual(order_line.product_uom_qty, 2)
        self.assertEqual(order_line.price_unit, 55)
        self.assertEqual(order_line.magento_order_id, '42')
        self.assertEqual(order_line.product_id.product_tmpl_id.magento_sku_id, 'SKU-ORDER-PROD')

        # Check that the tax was created and applied
        self.assertEqual(len(order_line.tax_id), 1)
        self.assertEqual(order_line.tax_id.amount, 10)

        # Check that the second sale order was created correctly
        sale_order_2 = self.env['sale.order'].search([('magento_order_id', '=', '43')])
        self.assertTrue(sale_order_2, "Second sale order should have been created.")
        self.assertEqual(sale_order_2.partner_id.email, 'john.doe@example.com')
        self.assertEqual(len(sale_order_2.order_line), 2)

        # Check the lines of the second order
        line1 = sale_order_2.order_line[0]
        self.assertEqual(line1.product_uom_qty, 1)
        self.assertEqual(line1.price_unit, 75)
        self.assertEqual(len(line1.tax_id), 1)
        self.assertEqual(line1.tax_id.amount, 15)

        line2 = sale_order_2.order_line[1]
        self.assertEqual(line2.product_uom_qty, 3)
        self.assertEqual(line2.price_unit, 50)
        self.assertEqual(len(line2.tax_id), 1)
        self.assertEqual(line2.tax_id.amount, 10)

        # Check that the third sale order was created or not (expected to be not created because of no customer and products in db)
        sale_order_3 = self.env['sale.order'].search([('magento_order_id', '=', '44')])
        self.assertFalse(sale_order_3, "Third sale order should not have been created.")


    # EXPORT ------------->
    @patch("requests.post")
    def test_export_product_to_magento(self, mock_post):
        mock_post.return_value.status_code = 200

        mock_post.return_value.json.return_value = {
            "id": 2001,
            "sku": "TEST-PRODUCT-01",
            "name": "Test Product 01",
        }


        # Create and run the wizard for single product export
        wizard = self.Wizard.create({
            'magento_instance_id': self.instance.id,
            'operation_type': 'export',
            'operation_sub_type': 'products',
            'export_all': False,
            'product_template_id': self.product_template.id,
        })


        result = wizard.action_confirm()

        # Check that the API was called once
        mock_post.assert_called_once()

        
        # Check the product was updated with Magento details
        self.assertEqual(self.product_template.magento_sku_id, 'TEST-PRODUCT-01')
        self.assertEqual(self.product_template.magento_instance_id, self.instance)


    @patch("requests.post")
    def test_export_customer_to_magento(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "id": 1001,
        }


        # Create and run the wizard for single customer export
        wizard = self.Wizard.create({
            'magento_instance_id': self.instance.id,
            'operation_type': 'export',
            'operation_sub_type': 'customers',
            'export_all': False,
            'partner_id': self.partner.id,
        })

        result = wizard.action_confirm()

        # Check that the API has called once
        mock_post.assert_called_once()

        # Check the customer has updated with Magento details
        self.assertEqual(self.partner.magento_customer_id, "1001")
        self.assertEqual(self.partner.magento_instance_id, self.instance)


    @patch("odoo.addons.odoo_magento_connector.wizards.magento_operation_wizard.MagentoOperationWizard.magento_make_request")
    def test_export_order_to_magento(self, request):
        


        def fake_request(endpoint, params, payload, method):
            if endpoint == "/guest-carts" and method == "POST":
                return "cart_123"
            elif endpoint.endswith("/items") and method == "POST":
                return {"item_id": 1}
            elif endpoint.endswith("/shipping-information"):
                return {"success": True}
            elif endpoint.endswith("/selected-payment-method"):
                return {"success": True}
            elif endpoint.endswith("/order"):
                return "order_456"
            return None

        request.side_effect = fake_request
        
        self.product_template.write({
            'magento_sku_id': 'TEST-PRODUCT',
            'magento_instance_id': self.instance.id,
        })


        # Create an order in Odoo to be exported
        product_product = self.env['product.product'].search([('product_tmpl_id','=', self.product_template.id)], limit = 1)

        order_to_export = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product_product.id,
                'product_uom_qty': 5,
                'price_unit': 89,
            })]
        })

            
        # Create and run the wizard for single order export
        wizard = self.Wizard.create({
            'magento_instance_id': self.instance.id,
            'operation_type': 'export',
            'operation_sub_type': 'orders',
            'export_all': False,
            'order_id': order_to_export.id,
        })

        result = wizard.action_confirm()

        # for call in request.call_args_list:
        #     pass
        
        
        # Check that the sale order was updated correctly
        self.assertEqual(order_to_export.magento_order_id, "order_456", "Order is not updated with magento_order_id")
        self.assertEqual(order_to_export.magento_instance_id, self.instance, "Order is not updated with magento_instance_id")
        
    

   


    @classmethod
    def tearDownClass(cls):
    # Define this for cleanup operations, such as releasing resources
        super(TestMagentoOperation, cls).tearDownClass()
        cls.instance.unlink()




# args, kwargs = mock_get.call_args
 # # Helper Methods
    # def check_api_request(self, url, endpoint, params = None, payload = None, method = 'GET' ):
    #     if url == f'{self.instance.magento_store_base_url}/rest/V1{endpoint}':
    #         pass;
    #     else:
    #         return False

    #     if method == 'POST' or method == 'PUT':
            

    #     return False