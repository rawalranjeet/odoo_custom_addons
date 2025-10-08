from odoo import _,api, models, fields
from odoo.exceptions import UserError, ValidationError
import requests
import base64
import logging
import pprint

_logger = logging.getLogger("__name__")

magento_to_odoo_order_state = {
        'new': 'draft',
        'pending_payment': 'sent',
        'payment_review': 'sent',
        'processing': 'sale',
        'on_hold': 'sale',
        'complete': 'sale',  
        'closed': 'sale',  
        'canceled': 'cancel'
    }

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
                product_template = product_template.with_context(from_magento_operation = True).create({
                    'name': item.get('name'),
                    'list_price': item.get('price'),
                    'is_storable': True,
                    'type': 'consu',
                    'default_code': item.get('sku'),
                    'magento_instance_id': self.magento_instance_id.id,
                    'magento_sku_id': item.get('sku'),
                    'sync_to_magento': True,
                    'magento_tax_class_id': next((attr.get('value') for attr in item.get('custom_attributes', []) if attr.get('attribute_code') == 'tax_class_id'), None) or False,
                    })
            else:

                product_template.with_context(from_magento_operation = True).write({
                    'magento_instance_id': self.magento_instance_id.id,
                    'magento_sku_id': item.get('sku'),
                    'sync_to_magento': True,
                    'magento_tax_class_id': next((attr.get('value') for attr in item.get('custom_attributes', []) if attr.get('attribute_code') == 'tax_class_id'), None) or False,
                    'list_price': item.get('price'),
                    'is_storable': True,
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
            
            if not partner:
                continue; 
            
            if not sale_order:
                new_order_added += 1
                sale_order = sale_order.with_context(from_magento_operation = True).sudo().create({
                    'partner_id': partner.id,
                    'magento_order_id': order.get('entity_id'),
                    'magento_instance_id': self.magento_instance_id.id,
                    'sync_to_magento': True,
                })

            
            sale_order.state = magento_to_odoo_order_state[order.get('state')]
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
                        account_tax = False
                        if item.get('tax_percent') != 0:
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
                            'tax_id': [(4, account_tax.id)] if account_tax else False,
                        }) 

            # DISCOUNT PRICE
            discount_amount = order.get('discount_amount')
            if discount_amount != 0:
                discount_product = self.env['product.product'].search([('default_code','=','MAGENTO_DISCOUNT_PRODUCT')], limit=1)
                if not discount_product: 
                    discount_product = self.env['product.product'].create({
                        'name': 'Magento Discount Product',
                        'sale_ok': False,
                        'purchase_ok': False,
                        'available_in_pos': False,
                        'type': 'service',
                        'lst_price': 0.0,
                        'taxes_id': False,
                        'default_code': 'MAGENTO_DISCOUNT_PRODUCT',
                    })

                discount_line = sale_order.order_line.filtered(lambda l: l.magento_discount)
                if not discount_line: 
                    self.env['sale.order.line'].create({
                        'magento_order_id':  item.get('order_id'),
                        'magento_instance_id': self.magento_instance_id.id,
                        'magento_discount': True,
                        'name': f'Discount',
                        'order_id': sale_order.id,
                        'price_unit': discount_amount,
                        'tax_id': False,
                        'product_id': discount_product.id,
                    })
                else:
                    discount_line.write({
                        'price_unit': discount_amount,
                        })


            billing_address_partner = partner.child_ids.filtered(lambda p: p.type == 'invoice')
            shipping_address_partner = partner.child_ids.filtered(lambda p: p.type == 'delivery')

            if not billing_address_partner and not shipping_address_partner:
                billing_address = order.get('billing_address')
                partner.with_context(from_magento_operation = True).create({
                    "name" : f"{billing_address.get('firstname')} {billing_address.get('lastname')}",
                    "magento_instance_id": self.magento_instance_id.id,
                    'phone': billing_address.get('telephone'),
                    'parent_id': partner.id,
                    'street': billing_address.get('street')[0],
                    'street2': billing_address.get('street')[1] if len(billing_address.get('street'))>1 else '',
                    'zip': billing_address.get('postcode'),
                    'country_id': self.env['res.country'].search([('code', '=', billing_address.get('country_id'))]).id,
                    'city': billing_address.get('city'),
                    'state_id': self.env['res.country.state'].search([('code', '=', billing_address.get('region_code')), ('country_id','=', self.env['res.country'].search([('code', '=', billing_address.get('country_id'))]).id)]).id,
                    'sync_to_magento': True,
                    'type': 'invoice',
                })
                
            # SHIPPING PRICE
            shipping_amount = order.get('shipping_amount')
            carrier_id = self.env['delivery.carrier'].search([('delivery_type', '=', 'fixed'), ('fixed_price','=',shipping_amount) ], limit=1)

            if not carrier_id:
                delivery_product = self.env['product.product'].create({
                    'name': 'Flat Rate',
                    'sale_ok': False,
                    'purchase_ok': False,
                    'available_in_pos': False,
                    'type': 'service',
                    'lst_price': shipping_amount,
                    'taxes_id': False,
                    'default_code': f'Delivery_Flate_Rate_{shipping_amount}',
                })
                carrier_id = self.env['delivery.carrier'].create({
                    'name': f'Flat Rate {shipping_amount}',
                    'delivery_type': 'fixed',
                    'fixed_price': shipping_amount,
                    'product_id': delivery_product.id,
                })
            
            sale_order.set_delivery_line(carrier_id, shipping_amount)



        
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
            })

            if not res_partner:
                new_customer_added += 1
                res_partner = res_partner.with_context(from_magento_operation = True).create(vals)

            else:

                res_partner.with_context(from_magento_operation = True).write(vals)

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
                }


                if not child_partner:
                    child_partner.with_context(from_magento_operation = True).create(child_vals)
                else:
                    child_partner.with_context(from_magento_operation = True).write(child_vals)
                
            
        
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
        if not self.export_all:
            try:
                result = self.magento_instance_id.magento_create_order(self.order_id)
                
                self.order_id.with_context(from_magento_operation = True).write({
                    'magento_order_id': result.get('magento_order_id'),
                    'magento_instance_id': self.magento_instance_id.id,
                    'sync_to_magento': True,
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Order %s successfully exported to Magento.') % self.order_id.name,
                        'type': 'success',
                        'sticky': False,
                    },
                }
            except (UserError, Exception) as e:
                _logger.error("Failed to export order %s: %s", self.order_id.name, e)
                raise

        else:
            orders_to_export = self.env['sale.order'].search([
                ('magento_order_id', '=', False),
            ])

            if not orders_to_export:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('No Orders Found'),
                        'message': "There are no orders for this Magento instance to export.",
                        'type': 'warning',
                        'sticky': False,
                    },
                }
                
            exported_count = 0
            failed_orders = []
            for order in orders_to_export:
                try:
                    result = self.magento_instance_id.magento_create_order(order)
                    order.with_context(from_magento_operation = True).write({
                        'magento_order_id': result.get('magento_order_id'),
                        'magento_instance_id': self.magento_instance_id.id,
                        'sync_to_magento': True,
                    })
                    exported_count += 1
                except Exception as e:
                    _logger.error("Failed to export order %s to Magento: %s", order.name, e)
                    failed_orders.append(f"{order.name}: {e}")
        
            message = _('%s orders exported successfully.') % exported_count
            notif_type = 'success'
            if failed_orders:
                failed_message = '\n'.join(failed_orders)
                message += _('\n\n%s orders failed to export:\n%s') % (len(failed_orders), failed_message)
                notif_type = 'warning' if exported_count > 0 else 'danger'

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Bulk Export Complete'),
                    'message': message,
                    'type': notif_type,
                    'sticky': False,
                },
            }


    def export_customers_to_magento(self):

        if self.export_all:
            res_partners = self.env['res.partner'].search([
                ('magento_customer_id','=',False), 
                ('magento_address_id','=',False), 
                ('email', '!=', False),
                ])
            
            

            if res_partners:
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
                    response = self.magento_instance_id.magento_create_customer(partner)
                    
                    partner.with_context(from_magento_operation = True).write({
                        'magento_customer_id': response.get('id'),
                        'magento_instance_id': self.magento_instance_id.id,
                        'sync_to_magento': True,
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
            params = {
                        "searchCriteria[filter_groups][0][filters][0][field]":"email",
                        "searchCriteria[filter_groups][0][filters][0][value]": self.partner_id.email,
                        "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq"
                    }
            customer = self.magento_make_request('/customers/search', params)
            
            if customer.get('items'):
                raise UserError("Customer with this email already exists in Magento")

            response = self.magento_instance_id.magento_create_customer(self.partner_id)

            if response: 
                self.partner_id.with_context(from_magento_operation = True).write({
                    'magento_customer_id': response.get('id'),
                    'magento_instance_id': self.magento_instance_id.id,
                    'sync_to_magento': True,
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