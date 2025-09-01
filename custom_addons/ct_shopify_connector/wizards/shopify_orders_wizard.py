from odoo import _,api, models, fields
from odoo.exceptions import UserError
import requests
import base64
import logging

_logger = logging.getLogger("__name__")


class ShopifyProductsWizard(models.TransientModel):
    _name = "shopify.orders.wizard"

    shopify_store_id = fields.Many2one("shopify.store", required=True)

    def action_get_orders(self):
        if self.shopify_store_id.state != 'connected':
            raise UserError("Selected Store is not Connected, Please connect the Store First")
        
        url = f'https://{self.shopify_store_id.shopify_store_name}.myshopify.com/admin/api/2025-07/orders.json'
        
        headers = {
            'Content-Type':'application/json',
            'X-Shopify-Access-Token': self.shopify_store_id.shopify_access_token
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:

                shopify_orders = response.json().get('orders')
                total_orders_fetched = 0

                for order in shopify_orders:
                    total_orders_fetched+=1

                    sale_order = self.env['sale.order'].search([('shopify_order_id','=',order.get('id'))])
                    res_partner = self.env['res.partner'].search([('shopify_customer_id','=', order.get('customer').get('id') if order.get('customer') else 'NOTFOUND')])
                    if not res_partner: continue;
                    shopify_line_items = order.get('line_items')


                    # import pdb; pdb.set_trace()

                    if not sale_order and res_partner:
                        sale_order = sale_order.create({
                            'shopify_order_id': order.get('id'),
                            'partner_id': res_partner.id
                        })

                    
                    for shopify_line_item in shopify_line_items:
                        sale_order_line = self.env['sale.order.line'].search([('shopify_order_line_item_id','=',shopify_line_item.get('id'))])
                        product_template = self.env['product.template'].search([('shopify_product_id', '=', shopify_line_item.get('product_id'))])
                        product_product = self.env['product.product'].search([('shopify_product_variant_id','=', shopify_line_item.get('variant_id'))])
                        sale_order_option = self.env['sale.order.option'].search([('shopify_order_line_item_id','=',shopify_line_item.get('id'))])
                        

                        # if not sale_order_line:

                        #     sale_order_line = sale_order_line.create({
                        #             'name': f'shopify_item_line {shopify_line_item.get('id')}',
                        #             'shopify_order_line_item_id': shopify_line_item.get('id'),
                        #             'shopify_store_id' : self.shopify_store_id.id,
                        #             'product_template_id':product_template.id,
                        #             'order_id': sale_order.id,
                        #             'product_uom_qty': shopify_line_item.get('quantity'),
                        #         })
                        
                        # import pdb; pdb.set_trace()                        

                        if not sale_order_option and product_product:

                            sale_order_option = sale_order_option.create({
                                    'name': f'shopify_item_line {shopify_line_item.get('id')}',
                                    'shopify_order_line_item_id': shopify_line_item.get('id'),
                                    'shopify_store_id' : self.shopify_store_id.id,
                                    'product_id':product_product.id,
                                    'order_id': sale_order.id,
                                    'quantity': shopify_line_item.get('quantity'),
                                })

                        sale_order.write({
                            # 'order_line': [(4,sale_order_line.id)],
                            'sale_order_option_ids': [(4,sale_order_option.id)]
                        })

                        for sale_order_option_id in sale_order.sale_order_option_ids:
                            # import pdb; pdb.set_trace()
                            if not sale_order_option_id.is_present:
                                sale_order_option_id.button_add_to_order()

                        print()


                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Order Success'),
                        'message': _(f'Orders Fetched, {total_orders_fetched} in total'),
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
