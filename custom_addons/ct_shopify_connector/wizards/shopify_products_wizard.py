from odoo import _,api, models, fields
from odoo.exceptions import UserError
import requests
import base64
import logging

_logger = logging.getLogger("__name__")


class ShopifyProductsWizard(models.TransientModel):
    _name = "shopify.products.wizard"

    shopify_store_id = fields.Many2one("shopify.store", required=True)
    import_with_image = fields.Boolean()

    def action_get_products(self):
        if self.shopify_store_id.state != 'connected':
            raise UserError("Selected Store is not Connected, Please connect the Store First")
        
        url = f'https://{self.shopify_store_id.shopify_store_name}.myshopify.com/admin/api/2025-07/products.json'
        
        headers = {
            'Content-Type':'application/json',
            'X-Shopify-Access-Token': self.shopify_store_id.shopify_access_token
        }

        try:
            response = requests.get(url, headers=headers)
            # import pdb; pdb.set_trace()

            if response.status_code == 200:

                shopify_products = response.json().get('products')
                total_product_fetched = 0

                for product in shopify_products:
                    product_template = self.env['product.template'].search([('shopify_product_id','=',product.get('id'))])
                    shopify_product_variants = product.get('variants')
                    total_product_fetched+=1
                    

                    if not product_template:
                        image_url = False
                        image_base64 = False

                        if self.import_with_image:

                            if product.get('image'):
                                image_url = product.get('image').get('src')

                            if image_url:
                                    response = requests.get(image_url)
                                    
                                    if response.status_code == 200:
                                        image_base64 = base64.b64encode(response.content)

                        vals = {
                            'shopify_product_id': product.get('id'),
                            'shopify_store_id': self.shopify_store_id.id,
                            'name': product.get('title'),
                            'description': product.get('body_html'),
                            'image_1920': image_base64,
                        }

                        
                        product_template = self.env['product.template'].create(vals)
                        
                    # converting currency from shopify to odoo
                    # product_template.list_price = self.shopify_store_id.currency_id._convert(

                    #     from_amount= float(shopify_product_variants[0].get('price')),
                    #     to_currency=product_template.currency_id,
                    #     company=self.env.company,
                    #     date=fields.Date.today()
                    # )
                    product_template.list_price = 0

                    options = product.get('options')
                    
                    # creating attribute and their values
                    for option in options:
                        
                        product_attribute = self.env['product.attribute'].search([('shopify_product_option_id','=', option.get('id'))])
                        

                        if not product_attribute:
                            vals = {
                                'shopify_product_option_id': option.get('id'),
                                'shopify_store_id': self.shopify_store_id.id,
                                'name': option.get('name'),
                            }

                            product_attribute = self.env['product.attribute'].create(vals)
                            
                        product_attribute_value_ids = []
                        for variant in shopify_product_variants:
                            
                            product_attribute_value = self.env['product.attribute.value'].search([('shopify_product_variant_id','=',variant.get('id'))])
                            # import pdb; pdb.set_trace()
                            if not product_attribute_value:
                                product_attribute_value = self.env['product.attribute.value'].create({
                                    'name' : variant.get('title'),
                                    'attribute_id': product_attribute.id,
                                    'shopify_product_variant_id': variant.get('id'),
                                    'shopify_store_id': self.shopify_store_id.id,
                                })

                                product_attribute_value.default_extra_price = self.shopify_store_id.currency_id._convert(

                                    from_amount= float(variant.get('price')),
                                    to_currency=product_template.currency_id,
                                    company=self.env.company,
                                    date=fields.Date.today()
                                )
                            
                            product_attribute_value_ids.extend(product_attribute_value.ids)
                        
                        product_template_attribute_line = self.env['product.template.attribute.line'].search([('shopify_product_option_id','=', option.get('id'))])

                        if not product_template_attribute_line:
                            product_template_attribute_line = self.env['product.template.attribute.line'].create({
                                'attribute_id':product_attribute.id,
                                'value_ids':product_attribute_value_ids,
                                'shopify_product_option_id': option.get('id'),
                                'product_tmpl_id': product_template.id, 
                                 
                                    })
                        
                        # product_template.write({
                        #     'attribute_line_ids': [
                        #         (0,0, {'attribute_id':product_attribute.id, 'value_ids':product_attribute_value_ids})
                        #     ]
                        # })
                        
                        for product_template_attribute_line_id in product_template_attribute_line:
                            product_template.write({
                                'attribute_line_ids': [
                                    (4 ,product_template_attribute_line_id.id)
                                ]
                            })

                        for i, id in enumerate(product_attribute_value_ids):
                            # import pdb; pdb.set_trace()
                            # product_template.product_variant_ids[i].lst_price = shopify_product_variants[i].get('price')
                            # product_template.product_variant_ids[i].shopify_product_variant_price = shopify_product_variants[i].get('price')
                            product_template.product_variant_ids[i].shopify_product_variant_id = shopify_product_variants[i].get('id')
                            
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Product Success'),
                        'message': _(f'Product Fetched, {total_product_fetched} in total'),
                        'type': 'success',
                        'sticky': False,
                    },
                }

            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Connection Failed'),
                        'message': response.text,
                        'type': 'danger',
                        'sticky': False,
                    },
                }
        except Exception as e:
            raise UserError(_(f"Connection error: {str(e)}"))
