from odoo import http, SUPERUSER_ID, api
from odoo.http import request, Response
from odoo.exceptions import UserError, ValidationError
import json

MAGENTO_TO_ODOO_PRODUCT_TYPE = {
    'simple': 'consu',
    'configurable' : 'consu',
    'bundle': 'combo',
    'grouped': 'combo',
    'virtual': 'service',
    'downloadable': 'service'
}



class ProductController(http.Controller):

    # Product Operation:::
    @http.route('/magento_product_create', type='http', auth='public', csrf=False, methods=['POST'])
    def magento_product_create(self, **kw):

        try:
            raw_body = request.httprequest.data

            data = json.loads(raw_body.decode('utf-8'))

            magento_sku_id = data.get("sku")


            product_template = request.env['product.template'].sudo().search([('default_code', '=', magento_sku_id), ('magento_sku_id','=', False)], limit=1)
            magento_instance_id = request.env['magento.instance'].sudo().search([], limit=1)

            vals = {
                'name': data.get('name'),
                'default_code': data.get('sku'),
                'magento_sku_id': data.get('sku'),
                'list_price': data.get('price'),
                'standard_price': data.get('cost'),
                'weight' : data.get('weight'),
                'is_published': True if data.get('status') == '1' else False,
                'type': MAGENTO_TO_ODOO_PRODUCT_TYPE[data.get('type_id')],
                'magento_instance_id': magento_instance_id.id if magento_instance_id else False,
                'sync_to_magento' : True,
                'taxes_id': False,
                'supplier_taxes_id': False
            }

            if vals['type'] == 'consu':
                vals['is_storable'] = True

            if not product_template:
                product_template.with_context(from_magento_operation = True).sudo().create(vals)

            else:
                product_template.with_context(from_magento_operation = True).sudo().update(vals)


            return Response(json.dumps({"status": "ok"}), status=200, content_type="application/json")
        
        except UserError as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=409, content_type="application/json")

        except Exception as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=500, content_type="application/json")


    @http.route('/magento_product_update', type='http', auth='public', csrf=False, methods=['PUT'])
    def magento_product_update(self, **kw):
        env = api.Environment(request.cr, SUPERUSER_ID, request.session.context or {})

        try:
            raw_body = request.httprequest.data
            
            import pdb; pdb.set_trace()
            
            data = json.loads(raw_body.decode('utf-8'))
            
            magento_sku_id = data.get("sku")
            

            product_template = env['product.template'].sudo().search([('magento_sku_id', '=', magento_sku_id)], limit=1)
            if product_template:

                product_template.sudo().with_context(from_magento_operation = True).write({
                    'name': data.get('name'),
                    'default_code': data.get('sku'),
                    'list_price': data.get('price'),
                    'standard_price': data.get('cost'),
                    'weight' : data.get('weight'),
                    'is_published': True if data.get('status') == 1 else False,
                    'sync_to_magento' : True
                }) 


            return Response(json.dumps({"status": "ok"}), status=200, content_type="application/json")
        
        except UserError as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=409, content_type="application/json")

        except Exception as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=500, content_type="application/json")


    @http.route('/magento_product_delete', type='http', auth='public', csrf=False, methods=['DELETE'])
    def magento_product_delete(self, **kw):

        try:
            raw_body = request.httprequest.data

            data = json.loads(raw_body.decode('utf-8'))

            magento_sku_id = data.get("sku")

            product_template = request.env['product.template'].sudo().search([('magento_sku_id', '=', magento_sku_id)], limit=1)
           
            if product_template:
                product_template.with_context(from_magento_operation = True).sudo().unlink()

                
            return Response(json.dumps({"status": "ok"}), status=200, content_type="application/json")
        
        except UserError as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=409, content_type="application/json")

        except Exception as e:
            request.env.cr.rollback()
            return Response(json.dumps({"status": "error", "message": str(e)}), status=500, content_type="application/json")


    # Customer Operation:::
    @http.route('/magento_customer_create', type='http', auth='public', csrf=False, methods=['POST'])
    def magento_customer_create(self, **kw):
        
        try:
            raw_body = request.httprequest.data

            data = json.loads(raw_body.decode('utf-8'))

            res_partner = request.env['res.partner'].search([
                '|',
                    ('email', '=', data.get('email')),
                    ('magento_customer_id', '=', data.get('entity_id')),
                ], limit=1)
            
            magento_instance_id = request.env['magento.instance'].sudo().search([], limit=1)
            
            full_name = data.get('firstname') + " "
            if data.get('middlename'):
                full_name += (data.get('middlename') + " ")
            full_name += data.get('lastname')


            vals = {
                'name' : full_name,
                'email' : data.get('email'),
                'magento_customer_id': data.get('entity_id'),
                'magento_instance_id': magento_instance_id.id if magento_instance_id else False,
                'sync_to_magento' : True,
                'dob': data.get('dob') if data.get('dob') != '' or None else False,
                'gender': 'male' if data.get('gender') == 1 else 'female' if data.get('gender') == 2 else 'other',
            }
            
            if not res_partner:
                res_partner = res_partner.with_context(from_magento_operation = True).sudo().create(vals)
            else:
                res_partner.with_context(from_magento_operation = True).sudo().update(vals)

            

            
            return Response(json.dumps({"status": "ok"}), status=200, content_type="application/json")
        
        except UserError as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=409, content_type="application/json")

        except Exception as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=500, content_type="application/json")
        
        
    @http.route('/magento_customer_update', type='http', auth='public', csrf=False, methods=['PUT'])
    def magento_customer_update(self, **kw):
        
        try:
            raw_body = request.httprequest.data

            data = json.loads(raw_body.decode('utf-8'))

            res_partner = request.env['res.partner'].sudo().search([
                '|',
                    ('email', '=', data.get('email')),
                    ('magento_customer_id', '=', data.get('entity_id')),
                ], limit=1)
            
            magento_instance_id = request.env['magento.instance'].sudo().search([], limit=1)
            
            full_name = data.get('firstname') + " "
            if data.get('middlename'):
                full_name += (data.get('middlename') + " ")
            full_name += data.get('lastname')


            vals = {
                'name' : full_name,
                'email' : data.get('email'),
                'magento_customer_id': data.get('entity_id'),
                'magento_instance_id': magento_instance_id.id if magento_instance_id else False,
                'sync_to_magento' : True,
                'dob': data.get('dob') if data.get('dob') != None else False,
                'gender': 'male' if data.get('gender') == 1 else 'female' if data.get('gender') == 2 else 'other',
            }
            


            if not res_partner:
                res_partner = res_partner.with_context(from_magento_operation = True).sudo().create(vals)
            else:
                res_partner.with_context(from_magento_operation = True).sudo().update(vals)

            
            addresses = data.get('addresses')
            for address in addresses:
                
                child_partner = request.env['res.partner'].sudo().search([('parent_id','=', res_partner.id),('magento_address_id','=',address.get('id'))])

                country = request.env['res.country'].sudo().search([('code', '=', address.get('country_id'))])

                if address.get('region').get('region') != None and country:
                    if address.get('region_id') == 0:
                        state = request.env['res.country.state'].sudo().search([('name','=', address.get('region').get('region')), ('country_id','=',country.id)])
                    else:
                        state = request.env['res.country.state'].sudo().search([('code','=', address.get('region').get('region_code')), ('country_id','=',country.id)])
                else:
                    state = False

                full_name = address.get('firstname') + " "

                if address.get('middlename'):
                    full_name += (address.get('middlename') + " ")

                full_name += address.get('lastname')
                

                child_vals =  {
                    "name" : full_name,
                    'magento_address_id': address.get('id'),
                    "magento_instance_id": magento_instance_id.id,
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
                    child_partner.with_context(from_magento_operation = True).sudo().create(child_vals)
                else:
                    child_partner.with_context(from_magento_operation = True).sudo().write(child_vals)
           



            return Response(json.dumps({"status": "ok"}), status=200, content_type="application/json")
        
        except UserError as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=409, content_type="application/json")

        except Exception as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=500, content_type="application/json")
        

    @http.route('/magento_customer_delete', type='http', auth='public', csrf=False, methods=['DELETE'])
    def magento_customer_delete(self, **kw):
       

        try:
            raw_body = request.httprequest.data

            data = json.loads(raw_body.decode('utf-8'))

            res_partner = request.env['res.partner'].sudo().search([
                ('magento_customer_id', '=', data.get('entity_id')),
                ], limit=1)
            
            if res_partner:
                res_partner.with_context(from_magento_operation=True).sudo().unlink()
           

            return Response(json.dumps({"status": "ok"}), status=200, content_type="application/json")
        
        except UserError as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=409, content_type="application/json")

        except Exception as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=500, content_type="application/json")


    # Order::::::::
    @http.route('/magento_order', type='http', auth='public', csrf=False, methods=['POST'])
    def magento_order(self, **kw):
        try:
            raw_body = request.httprequest.data
            
            data = json.loads(raw_body.decode('utf-8'))

            magento_instance_id = request.env['magento.instance'].sudo().search([], limit=1)
            partner = request.env['res.partner'].sudo().search([('magento_customer_id','=', data.get('customer_id'))])

            if partner and magento_instance_id:
                sale_order = request.env['sale.order'].with_context(from_magento_operation = True).sudo().create({
                    'partner_id': partner.id,
                    'magento_instance_id': magento_instance_id.id if magento_instance_id else False,
                    'magento_order_id' : data.get('entity_id'),
                    "sync_to_magento": True,
                    "magento_cart_id" : data.get('quote_id')
                })

                for item in data.get('items'):
                
                    product_template = request.env['product.template'].sudo().search([('magento_sku_id', '=', item.get('sku')), ('magento_instance_id','=', magento_instance_id.id)])
                    product_product = request.env['product.product']

                    if product_template:
                        product_product = product_product.sudo().search([('product_tmpl_id','=', product_template.id)])
                    

                    if product_product:

                        # check if the sale_order_line already exists
                        sale_order_line = request.env['sale.order.line'].sudo().search([('magento_order_id', '=', data.get('entity_id')), ('magento_instance_id','=', magento_instance_id.id), ('order_id','=',sale_order.id),('product_id','=',product_product.id)])


                        if not sale_order_line:
                            account_tax = False
                            
                            if item.get('tax_percent') != 0:
                                account_tax = request.env['account.tax'].sudo().search([('amount','=',item.get('tax_percent'))], limit=1)
                                if not account_tax:
                                    account_tax = account_tax.create({
                                        'name': f"{item.get('tax_percent')}%",
                                        'amount': item.get('tax_percent'),
                                    })
                            

                            sale_order_line = request.env['sale.order.line'].sudo().create({
                                'magento_order_id':  data.get('entity_id'),
                                'magento_instance_id': magento_instance_id.id if magento_instance_id else False,
                                'name': f'magento_item_line {data.get('entity_id')}',
                                'product_id':product_product.id,
                                'order_id': sale_order.id,
                                'product_uom_qty': item.get('qty_ordered'),
                                'price_unit': item.get('price'),
                                'tax_id': [(4, account_tax.id)] if account_tax else False,
                            }) 

            return Response(json.dumps({"status": "ok"}), status=200, content_type="application/json")
        
        except UserError as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=409, content_type="application/json")

        except Exception as e:
            return Response(json.dumps({"status": "error", "message": str(e)}), status=500, content_type="application/json")