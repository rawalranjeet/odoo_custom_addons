from odoo import _,api, models, fields
from odoo.exceptions import UserError, ValidationError
import requests
import base64
import logging
import pprint

_logger = logging.getLogger("__name__")

class MagentoOperationWizard(models.TransientModel):
    _name = "magento.operation.wizard"
    _description = "Magento Operation Wizard"

    magento_instance_id = fields.Many2one("magento.instance", required=True)
    operation_type = fields.Selection([('import','Import'),('export','Export')], default = 'import', required=True)
    operation_sub_type = fields.Selection([
        ('products', 'Products'),
        ('customers', 'Customers'),
        ('orders', 'Orders'),
        ], default = 'products', required=True)

    # export field
    export_all = fields.Boolean("Export all", help= f'Export all the products/customers/orders which are not in the Magento')
    product_template_id = fields.Many2one("product.template")
    partner_id = fields.Many2one("res.partner")
    order_id = fields.Many2one("sale.order")



    def action_confirm(self):

        
        
        if self.operation_type == 'import':
            if self.operation_sub_type == 'products':
                return self.import_product_from_magento()
            
            elif self.operation_sub_type == 'orders':
                return self.import_orders_from_magento()
            
            elif self.operation_sub_type == 'customers':
                return self.import_customers_from_magento()
        
        else: #export
            if self.operation_sub_type == 'products':
                return self.export_product_to_magento()
            
            elif self.operation_sub_type == 'orders':
                return self.export_orders_to_magento()
            
            elif self.operation_sub_type == 'customers':
                return self.export_customers_to_magento()


    def magento_make_request(self,endpoint, params, payload=None, method='GET'):
        
        url = f'{self.magento_instance_id.magento_store_base_url}/rest/V1{endpoint}'

        headers = {'Authorization': f'Bearer {self.magento_instance_id.magento_access_token}', 'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, params= params,json = payload, verify=False, headers=headers, timeout=10)
            else: # POST
                response = requests.post(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
        
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            _logger.exception(e.response.json())
            raise UserError(f"Magento API Error: {e.response.json().get('message')}")

        except Exception as e:
            _logger.exception(e.response.json())
            raise UserError(f"Magento API Error: {(e.response.json().get('message', 'Unknown Magento API error')).replace('%1', e.response.json().get('parameters', [''])[0])}")
            # raise UserError(f"An error occurred: {e}")
        
        
        return response.json()
    


    # IMPORT <-------------
    def import_product_from_magento(self):

        params = {
                "searchCriteria":"name"
            }
        
        response = self.magento_make_request('/products', params)
        
        magento_items = response.get('items')
        new_product_added = 0

        for item in magento_items[:20]:
            product_template = self.env['product.template'].search([('magento_sku_id', '=', item.get('sku')), ('magento_instance_id','=', self.magento_instance_id.id)])

            if not product_template:
                new_product_added += 1
                product_template = product_template.create({
                    'magento_instance_id': self.magento_instance_id.id,
                    'magento_sku_id': item.get('sku'),
                    'name': item.get('name'),
                    'list_price': item.get('price'),
                    'is_storable': True,
                    'type': 'consu',
                    'default_code': item.get('sku'),
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(f'{response.get('total_count')} Products Fetched'),
                'message': _(f'New Product Added: {new_product_added}'),
                'type': 'success',
                'sticky': False,
            },
        }
        
    def import_orders_from_magento(self):
        params = {
                "searchCriteria":""
            }
        
        response = self.magento_make_request('/orders', params)
        
        magento_orders = response.get('items')
        new_order_added = 0

        for order in magento_orders:
            sale_order = self.env['sale.order'].search([('magento_order_id', '=', order.get('entity_id')), ('magento_instance_id','=', self.magento_instance_id.id)])
            partner = self.env['res.partner'].search([('magento_customer_id', '=', order.get('customer_id')), ('magento_instance_id','=', self.magento_instance_id.id)])

            if not partner:
                continue; 
            
            if not sale_order:
                new_order_added += 1
                sale_order = sale_order.create({
                    'partner_id': partner.id,
                    'magento_order_id': order.get('entity_id'),
                    'magento_instance_id': self.magento_instance_id.id,
                })

            import pdb; pdb.set_trace()
            
            items = order.get('items')

            for item in items:

                product_template = self.env['product.template'].search([('magento_sku_id', '=', item.get('sku')), ('magento_instance_id','=', self.magento_instance_id.id)])

                if product_template:
                    product_product = self.env['product.product'].search([('product_tmpl_id','=', product_template.id)])

                    

        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(f'{response.get('total_count')} Orders Fetched'),
                'message': _(f'New Order Added: {new_order_added}'),
                'type': 'success',
                'sticky': False,
            },
        }

    def import_customers_from_magento(self):

        params = {
                "searchCriteria":"name"
            }
        
        response = self.magento_make_request('/customers/search', params)

        magento_customers = response.get('items')
        new_customer_added = 0

        for customer in magento_customers:
            res_partner = self.env['res.partner'].search([('magento_customer_id', '=', customer.get('id')), ('magento_instance_id','=', self.magento_instance_id.id)])

            if not res_partner:
                new_customer_added += 1
                res_partner = res_partner.create({
                    'magento_instance_id': self.magento_instance_id.id,
                    'magento_customer_id': customer.get('id'),
                    'name': f"{customer.get('firstname')} {customer.get('middlename')} {customer.get('lastname')}",
                    'dob': customer.get('dob'),
                    'email': customer.get('email'),
                    'gender': 'male' if customer.get('gender') == 1 else 'female' if customer.get('gender') == 2 else 'other',
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(f'{response.get('total_count')} Customers Fetched'),
                'message': _(f'New Customer Added: {new_customer_added}'),
                'type': 'success',
                'sticky': False,
            },
        }
        
    
    # EXPORT ------------->
    def export_product_to_magento(self):
        
        if self.export_all:
            product_templates = self.env['product.template'].search([('magento_sku_id','=',False)])

            if product_templates:
                params = ''
                total_product_exported = 0

                for product_template in product_templates:
                    if not product_template.default_code or not product_template.is_storable:
                        continue; 
                    
                    total_product_exported += 1
                    payload = {
                        "product": {
                            "sku": product_template.default_code,
                            "name": product_template.name,
                            "price": product_template.list_price,
                            "status": 1,
                            "type_id": "simple",
                            "attribute_set_id": 4,
                            "weight": 1,
                            "custom_attributes": [
                                { "attribute_code": "description", "value": product_template.description }
                            ]
                        }
                    }

                    response = self.magento_make_request('/products', params, payload, 'POST')
                    

                    if response: 
                        product_template.magento_sku_id = response.get('sku')
                        product_template.magento_instance_id = self.magento_instance_id.id

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _(f'Products Export Success'),
                        'message': _(f'Total : {total_product_exported}'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
                    
            else:

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Product Export Failed'),
                        'message': "No product found to export",
                        'type': 'danger',
                        'sticky': False,
                    },
                }

        else:
            if not self.product_template_id.default_code or not self.product_template_id.is_storable:
                raise UserError("Selected Product has no Reference or is not storable")


            params = ''

            payload = {
                "product": {
                    "sku": self.product_template_id.default_code,
                    "name": self.product_template_id.name,
                    "price": self.product_template_id.list_price,
                    "status": 1,
                    "type_id": "simple",
                    "attribute_set_id": 4,
                    "weight": 1,
                    "custom_attributes": [
                        { "attribute_code": "description", "value": self.product_template_id.description }
                    ]
                }
            }

            response = self.magento_make_request('/products',params, payload, 'POST')

            if response: 
                self.product_template_id.magento_sku_id = response.get('sku')
                self.product_template_id.magento_instance_id = self.magento_instance_id.id
            
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _(f'Products Export Success'),
                        'message': _(f'Total : {1}'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
        

    def export_orders_to_magento(self):
        pass


    def export_customers_to_magento(self):

        if self.export_all:
            res_partners = self.env['product.template'].search([('magento_customer_id','=',False)])

            if res_partners:
                params = ''
                total_customer_exported = 0

                for partner in res_partners: 

                    if not partner.dob or partner.gender:
                        continue;
                    
                    total_customer_exported += 1

                    full_name = partner.name

                    parts = full_name.strip().split()

                    first_name = parts[0] if len(parts) > 0 else ""
                    middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
                    last_name = parts[-1] if len(parts) > 1 else ""

                    if not first_name or not last_name:
                        continue;

                    payload = {
                        "customer": {
                            "email": partner.email,
                            "firstname": first_name,
                            "middlename": middle_name,
                            "lastname": last_name,
                            "gender": 1 if partner.gender == 'male' else 2 if partner.gender == 'female' else 3,
                            "dob" : partner.dob.strftime("%Y-%m-%d")
                        }
                    }

                    response = self.magento_make_request('/customers', params, payload, 'POST')
                    

                    if response: 
                        partner.magento_customer_id = response.get('id')
                        partner.magento_instance_id = self.magento_instance_id.id

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _(f'Customer Export Success'),
                        'message': _(f'Total : {total_customer_exported}'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
                    
            else:

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Customer Export Failed'),
                        'message': "No customer found to export",
                        'type': 'danger',
                        'sticky': False,
                    },
                }

        else:

            params = ''

            if not self.partner_id.dob or not self.partner_id.gender:
                raise UserError("Selected Customer has no Dob or Gender defined")

            full_name = self.partner_id.name

            parts = full_name.strip().split()

            first_name = parts[0] if len(parts) > 0 else ""
            middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
            last_name = parts[-1] if len(parts) > 1 else ""

            payload = {
                "customer": {
                    "email": self.partner_id.email,
                    "firstname": first_name,
                    "middlename": middle_name,
                    "lastname": last_name,
                    "gender": 1 if self.partner_id.gender == 'male' else 2 if self.partner_id.gender == 'female' else 3,
                    "dob" : self.partner_id.dob.strftime("%Y-%m-%d")
                }
            }

            response = self.magento_make_request('/customers',params, payload, 'POST')

            if response: 
                self.partner_id.magento_customer_id = response.get('id')
                self.partner_id.magento_instance_id = self.magento_instance_id.id
            
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _(f'Customer Export Success'),
                        'message': _(f'Total : {1}'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
        



