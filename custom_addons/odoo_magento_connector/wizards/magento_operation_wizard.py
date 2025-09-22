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


    def magento_make_request(self, endpoint, params, payload=None, method='GET'):
        
        url = f'{self.magento_instance_id.magento_store_base_url}/rest/V1{endpoint}'

        headers = {'Authorization': f'Bearer {self.magento_instance_id.magento_access_token}', 'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, params= params,json = payload, verify=False, headers=headers, timeout=10)
            elif method == 'POST': 
                response = requests.post(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
            elif method == 'PUT':
                response = requests.put(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
        
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            _logger.exception(e.response.json())
            raise UserError(f"Magento API Error: {e.response.json().get('message')}")
        
        except requests.exceptions.RequestException as e:
        # Any network/connection/timeout/DNS errors
            _logger.exception(e)
            raise UserError(f"Magento Connection Error: It may be due to store url you provided is either invalid or the server is down")

        except Exception as e:
            _logger.exception(e)
            # raise UserError(f"Magento API Error: {(e.response.json().get('message', 'Unknown Magento API error')).replace('%1', e.response.json().get('parameters', [''])[0])}")
            raise UserError(f"An error occurred: {e}")
        
        
    


    # IMPORT <-------------
    def import_product_from_magento(self):

        # search for only the simple prodcuts
        params = {
                "searchCriteria[filter_groups][0][filters][0][field]":"type_id",
                "searchCriteria[filter_groups][0][filters][0][value]": "simple",
                "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq"
            }
        
        response = self.magento_make_request('/products', params)
        
        
        magento_items = response.get('items')
        new_product_added = 0

        for item in magento_items:
            product_template = self.env['product.template'].search([
                '|',
                    ('default_code', '=', item.get('sku')),
                    ('magento_sku_id', '=', item.get('sku')),
                ('magento_instance_id','=', self.magento_instance_id.id)
                ])
            

            if not product_template:
                new_product_added += 1
                product_template = product_template.create({
                    'name': item.get('name'),
                    'list_price': item.get('price'),
                    'is_storable': True,
                    'type': 'consu',
                    'default_code': item.get('sku'),
                    'magento_instance_id': self.magento_instance_id.id,
                    'magento_sku_id': item.get('sku'),
                    'sync_to_magento': True,
                    'from_magento_operation': True,
                })
            else:

                product_template.write({
                    'magento_instance_id': self.magento_instance_id.id,
                    'magento_sku_id': item.get('sku'),
                    'from_magento_operation': True,
                    'sync_to_magento': True,
                    'from_magento_operation': True,
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
            partner = self.env['res.partner'].search([('email', '=', order.get('customer_email')), ('magento_instance_id','=', self.magento_instance_id.id)])
            
            # import pdb; pdb.set_trace()

            if not partner:
                continue; 
            
            if not sale_order:
                new_order_added += 1
                sale_order = sale_order.create({
                    'partner_id': partner.id,
                    'magento_order_id': order.get('entity_id'),
                    'magento_instance_id': self.magento_instance_id.id,
                })

            
            
            items = order.get('items')

            for item in items:
                # import pdb; pdb.set_trace()

                product_template = self.env['product.template'].search([('magento_sku_id', '=', item.get('sku')), ('magento_instance_id','=', self.magento_instance_id.id)])
                product_product = self.env['product.product']

                if product_template:
                    product_product = product_product.search([('product_tmpl_id','=', product_template.id)])
                

                if product_product:

                    # check if the sale_order_line already exists
                    sale_order_line = self.env['sale.order.line'].search([('magento_order_id', '=', item.get('order_id')), ('magento_instance_id','=', self.magento_instance_id.id), ('order_id','=',sale_order.id),('product_id','=',product_product.id)])


                    if not sale_order_line:
                        account_tax = self.env['account.tax'].search([('amount','=',item.get('tax_percent'))], limit=1)
                        if not account_tax:
                            account_tax = account_tax.create({
                                'name': f"{item.get('tax_percent')}%",
                                'amount': item.get('tax_percent'),
                            })

                        sale_order_line = self.env['sale.order.line'].create({
                            'magento_order_id':  item.get('order_id'),
                            'magento_instance_id': self.magento_instance_id.id,
                            'name': f'magento_item_line {item.get('order_id')}',
                            'product_id':product_product.id,
                            'order_id': sale_order.id,
                            'product_uom_qty': item.get('qty_ordered'),
                            'price_unit': item.get('base_price'),
                            'tax_id': False,
                        }) 

                        sale_order_line.write({
                            'tax_id': [(4, account_tax.id)]
                        })

        
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
            res_partner = self.env['res.partner'].search([
                '|',
                    ('email', '=', customer.get('email')),
                    ('magento_customer_id', '=', customer.get('id')),
                ], limit=1)
            
            vals  = {
                'magento_instance_id': self.magento_instance_id.id,
                'magento_customer_id': customer.get('id'),
                'dob': customer.get('dob'),
                'gender': 'male' if customer.get('gender') == 1 else 'female' if customer.get('gender') == 2 else 'other',
                'sync_to_magento' : True,
            }

            addresses = customer.get('addresses')

            full_name = customer.get('firstname') + " "

            if customer.get('middlename'):
                full_name += (customer.get('middlename') + " ")

            full_name += customer.get('lastname')

            vals.update({
                'name': full_name,
                'email': customer.get('email'),
                'from_magento_operation': True,
            })

            if not res_partner:
                new_customer_added += 1
                res_partner = res_partner.create(vals)

            else:

                res_partner.write(vals)

            # adding addresses to the partner
            for address in addresses:
                
                child_partner = self.env['res.partner'].search([('parent_id','=', res_partner.id),('magento_address_id','=',address.get('id'))])

                country = self.env['res.country'].search([('code', '=', address.get('country_id'))])

                if address.get('region').get('region') != None and country:
                    if address.get('region_id') == 0:
                        state = self.env['res.country.state'].search([('name','=', address.get('region').get('region')), ('country_id','=',country.id)])
                    else:
                        state = self.env['res.country.state'].search([('code','=', address.get('region').get('region_code')), ('country_id','=',country.id)])
                else:
                    state = False

                full_name = address.get('firstname') + " "

                if address.get('middlename'):
                    full_name += (address.get('middlename') + " ")

                full_name += address.get('lastname')
                

                child_vals =  {
                    "name" : full_name,
                    'magento_address_id': address.get('id'),
                    "magento_instance_id": self.magento_instance_id.id,
                    'phone': address.get('telephone'),
                    'parent_id': res_partner.id,
                    'street': address.get('street')[0],
                    'street2': address.get('street')[1] if len(address.get('street'))>1 else '',
                    'zip': address.get('postcode'),
                    'country_id': country.id if country else False,
                    'city': address.get('city'),
                    'state_id': state.id if state else False,
                    'sync_to_magento': True,
                    'type': 'delivery' if address.get('default_shipping') else 'invoice' if address.get('default_billing') else 'other',
                    'from_magento_operation': True,
                }


                if not child_partner:
                    child_partner.create(child_vals)
                else:
                    child_partner.write(child_vals)
                
            
        
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
            product_templates = self.env['product.template'].search([
                ('magento_sku_id','=',False),
                ('default_code', '!=', False),
                ])
            
            

            if product_templates:
                params = ''
                total_product_exported = 0

                for product_template in product_templates:
                    
                    url_key = f"{"-".join(product_template.name.lower().split()).replace("'", "")}-{product_template.id}"

                    
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
                                { "attribute_code": "description", "value": product_template.description },
                                { "attribute_code": "url_key", "value": url_key },
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
            if not self.product_template_id.default_code:
                raise UserError("Selected Product has no Reference")


            params = ''

            url_key = f"{"-".join(self.product_template_id.name.lower().split()).replace("'", "")}-{self.product_template_id.id}"

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
                        { "attribute_code": "description", "value": self.product_template_id.description },
                        { "attribute_code": "url_key", "value": url_key },
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
        
        if self.export_all:
            orders = self.env['sale.order'].search([('magento_order_id','=',False), ('magento_instance_id','!=', self.magento_instance_id.id)])

            if orders:
                total_order_exported = 0
                for order in orders:
                    order_line = order.order_line
                    if not order_line:
                        continue;

                    partner = order.partner_id


                    first_name, middle_name, last_name = self.get_magento_name(partner.name)

                    if not first_name or not last_name:
                        continue;
                    
                    if not partner.phone or not partner.street or not partner.city or not partner.state_id or not partner.zip or not partner.country_code:
                        continue;
                        
                    import pdb; pdb.set_trace()
                    # Create a cart
                    params = ''
                    # cart_response = self.magento_make_request('/guest-carts', params,None , 'POST')
                    cart_response = self.magento_make_request(f'/customers/{partner.magento_customer_id}/carts', params,None , 'POST')
                    magento_cart_id = cart_response
                    

                    # Add items to cart
                    total_product_added = 0
                    for item in order_line:
                        if not item.product_template_id.magento_sku_id:
                            continue;
                        total_product_added+=1
                        item_payload = {
                            "cartItem": {
                                "sku": item.product_template_id.magento_sku_id,
                                "qty": item.product_uom_qty,
                                "quote_id": magento_cart_id,
                            }
                        }

                        self.magento_make_request(f'/carts/{magento_cart_id}/items', params, item_payload, 'POST')
                        # self.magento_make_request(f'/guest-carts/{magento_cart_id}/items', params, item_payload, 'POST')

                    if total_product_added == 0:
                        continue;
                    
                    shipping_address = {}
                    billing_address = {}

                    
                    
                    # shipping details
                    shipping_payload = {
                        "addressInformation": {
                            "shipping_address": {
                                "firstname": first_name,
                                "middlename": middle_name,
                                "lastname": last_name,
                                "street": [partner.street, partner.street2],
                                "city": partner.city,
                                "region": partner.state_id.code,
                                "postcode": partner.zip,
                                "country_id": partner.country_code,
                                "telephone": partner.phone,
                                "email": partner.email,
                            },
                            "billing_address": {
                                "firstname": first_name,
                                "middlename": middle_name,
                                "lastname": last_name,
                                "street": [partner.street, partner.street2],
                                "city": partner.city,
                                "region": partner.state_id.code,
                                "postcode": partner.zip,
                                "country_id": partner.country_code,
                                "telephone": partner.phone,
                                "email": partner.email,
                            },
                            "shipping_method_code": "flatrate",
                            "shipping_carrier_code": "flatrate"
                        }
                    }

                   

                    # response = self.magento_make_request(f'/guest-carts/{magento_cart_id}/shipping-information', params, shipping_payload, 'POST')
                    response = self.magento_make_request(f'/carts/{magento_cart_id}/shipping-information', params, shipping_payload, 'POST')

                    # payment methods
                    payment_payload = {
                        "method": {
                            "method": "checkmo"   # Payment method code
                        }
                    }

                    # response = self.magento_make_request(f'/guest-carts/{magento_cart_id}/selected-payment-method', params, payment_payload, 'PUT')
                    response = self.magento_make_request(f'/carts/{magento_cart_id}/selected-payment-method', params, payment_payload, 'PUT')
                    

                    # create an order
                    magento_order_id = self.magento_make_request(f'/carts/{magento_cart_id}/order', params, None, 'PUT')
                    # magento_order_id = self.magento_make_request(f'/guest-carts/{magento_cart_id}/order', params, None, 'PUT')

                    order.write({
                        'magento_order_id': magento_order_id,
                        'magento_instance_id': self.magento_instance_id,
                    })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _(f'Orders Export Success'),
                        'message': _(f'Total : {total_order_exported}'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
                    

            else:

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Order Export Failed'),
                        'message': "No order found to export",
                        'type': 'danger',
                        'sticky': False,
                    },
                }

            
        else:
            order_line = self.order_id.order_line
            if not order_line:
                raise UserError("Selected Order has no products added")

            partner = self.order_id.partner_id

            if not partner.magento_customer_id:
                raise UserError("Selected Order's customer is not linked to any magento customer")
            
            # Create a cart
            params = ''
            import pdb; pdb.set_trace()
            # cart_response = self.magento_make_request('/guest-carts', params,None , 'POST')
            cart_response = self.magento_make_request(f'/customers/{partner.magento_customer_id}/carts', params,None , 'POST')
            magento_cart_id = cart_response

            # Add items to cart
            for item in order_line:
                item_payload = {
                    "cartItem": {
                        "sku": item.product_template_id.magento_sku_id,
                        "qty": item.product_uom_qty,
                        "quote_id": magento_cart_id,
                    }
                }

                # self.magento_make_request(f'/guest-carts/{magento_cart_id}/items', params, item_payload, 'POST')
                self.magento_make_request(f'/carts/{magento_cart_id}/items', params, item_payload, 'POST')

            # shipping details\
            partner = self.order_id.partner_id

            first_name, middle_name, last_name = self.get_magento_name(partner.name)

            if not first_name or not last_name:
                raise UserError("customer name is incomplete")
        

            shipping_payload = {
                "addressInformation": {
                    "shipping_address": {
                        "firstname": first_name,
                        "middlename": middle_name,
                        "lastname": last_name,
                        "street": [partner.street, partner.street2],
                        "city": partner.city,
                        "region": partner.state_id.code,
                        "postcode": partner.zip,
                        "country_id": partner.country_code,
                        "telephone": partner.phone,
                        "email": partner.email,
                    },
                    "billing_address": {
                        "firstname": first_name,
                        "middlename": middle_name,
                        "lastname": last_name,
                        "street": [partner.street, partner.street2],
                        "city": partner.city,
                        "region": partner.state_id.code,
                        "postcode": partner.zip,
                        "country_id": partner.country_code,
                        "telephone": partner.phone,
                        "email": partner.email,
                    },
                    "shipping_method_code": "flatrate",
                    "shipping_carrier_code": "flatrate"
                }
            }

            response = self.magento_make_request(f'/carts/{magento_cart_id}/shipping-information', params, shipping_payload, 'POST')

            # payment methods
            payment_payload = {
                "method": {
                    "method": "checkmo"   # Payment method code
                }
            }

            response = self.magento_make_request(f'/carts/{magento_cart_id}/selected-payment-method', params, payment_payload, 'PUT')
            

            # create an order
            magento_order_id = self.magento_make_request(f'/carts/{magento_cart_id}/order', params, None, 'PUT')

            self.order_id.write({
                'magento_order_id': magento_order_id,
                'magento_instance_id': self.magento_instance_id,
            })


    def export_customers_to_magento(self):

        if self.export_all:
            res_partners = self.env['res.partner'].search([
                ('magento_customer_id','=',False), 
                ('magento_address_id','=',False), 
                ('email', '!=', False),
                ('dob', '!=', False),
                ('gender', '!=', False),
                ])
            
            

            if res_partners:
                params = ''
                total_customer_exported = 0

                for partner in res_partners: 
                    # search for customer in magento using email
                    params = {
                        "searchCriteria[filter_groups][0][filters][0][field]":"email",
                        "searchCriteria[filter_groups][0][filters][0][value]": partner.email,
                        "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq"
                    }
                    customer = self.magento_make_request('/customers/search', params)
                    
                    if customer.get('items'):
                        continue;
                    

                    total_customer_exported += 1

                    first_name, middle_name, last_name = self.get_magento_name(partner.name)

                    if not first_name or not last_name:
                        continue;

                    addresses = []

                    for child_partner in partner.child_ids:

                        child_first_name, child_middle_name, child_last_name = self.get_magento_name(child_partner.name)

                        if not child_first_name or not child_last_name or not child_partner.phone or not child_partner.street or not child_partner.city or not child_partner.zip or not child_partner.country_id:
                            continue;

                        address = {
                                "firstname": child_first_name,
                                "middlename": child_middle_name,
                                "lastname": child_last_name,
                                "street": [child_partner.street, child_partner.street2],
                                "city": child_partner.city,
                                "postcode": child_partner.zip,
                                "telephone": child_partner.phone,
                                "country_id": child_partner.country_code,
                                "region": {
                                    "region_code": child_partner.state_id.code,
                                    "region": child_partner.state_id.name,
                                } if child_partner.state_id else {},
                                "default_shipping": True if child_partner.type == 'delivery' else False,
                                "default_billing": True if child_partner.type == 'invoice' else False,
                            }
                        
                        addresses.append(address)

                    payload = {
                        "customer": {
                            "email": partner.email,
                            "firstname": first_name,
                            "middlename": middle_name,
                            "lastname": last_name,
                            "gender": 1 if partner.gender == 'male' else 2 if partner.gender == 'female' else 3,
                            "dob" : partner.dob.strftime("%Y-%m-%d") if partner.dob else None,
                            "addresses": addresses,
                        }
                    }

                    

                    response = self.magento_make_request('/customers', params, payload, 'POST')
                    

                    partner.write({
                        'magento_customer_id': response.get('id'),
                        'magento_instance_id': self.magento_instance_id.id,
                        'sync_to_magento': True,
                        'from_magento_operation': True,
                    })

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

            first_name, middle_name, last_name = self.get_magento_name(self.partner_id.name)

            if not first_name or not last_name:
                raise UserError("Customer name is incomplete")
            
            addresses = []

            for child_partner in self.partner_id.child_ids:

                child_first_name, child_middle_name, child_last_name = self.get_magento_name(child_partner.name)

                if not child_first_name or not child_last_name or not child_partner.phone or not child_partner.street or not child_partner.city or not child_partner.zip or not child_partner.country_id:
                    continue;

                address = {
                        "firstname": child_first_name,
                        "middlename": child_middle_name,
                        "lastname": child_last_name,
                        "street": [child_partner.street, child_partner.street2],
                        "city": child_partner.city,
                        "postcode": child_partner.zip,
                        "telephone": child_partner.phone,
                        "country_id": child_partner.country_code,
                        "region": {
                            "region_code": child_partner.state_id.code,
                            "region": child_partner.state_id.name,
                        } if child_partner.state_id else {},
                        "default_shipping": True if child_partner.type == 'delivery' else False,
                        "default_billing": True if child_partner.type == 'invoice' else False,
                    }
                
                addresses.append(address)

            payload = {
                "customer": {
                    "email": self.partner_id.email,
                    "firstname": first_name,
                    "middlename": middle_name,
                    "lastname": last_name,
                    "gender": 1 if self.partner_id.gender == 'male' else 2 if self.partner_id.gender == 'female' else 3,
                    "dob" : self.partner_id.dob.strftime("%Y-%m-%d") if self.partner_id.dob else None,
                    "addresses": addresses,
                }
            }

            response = self.magento_make_request('/customers',params, payload, 'POST')

            if response: 
                self.partner_id.write({
                    'magento_customer_id': response.get('id'),
                    'magento_instance_id': self.magento_instance_id.id,
                    'sync_to_magento': True,
                    'from_magento_operation': True,
                })

            
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
        



    # Helper function
    def get_magento_name(self, name):

        parts = name.strip().split()

        first_name = parts[0] if len(parts) > 0 else ""
        middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
        last_name = parts[-1] if len(parts) > 1 else ""

        return first_name, middle_name, last_name