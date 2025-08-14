from odoo import fields, models, api
from odoo.exceptions import ValidationError


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'

#     @api.onchange('order_line')
#     def product_add_validation(self):
#         # import pdb; pdb.set_trace()

#         # for order in self.partner_id.sale_order_ids:
#         #     product_
#         pass

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
        
    @api.onchange('product_template_id')
    def product_add_validation(self):

        

        if self.product_template_id:
            # import pdb ; pdb.set_trace()

            product = self.product_template_id

            # check product in current sale order
            for order_line in self.order_id.order_line:
                # import pdb ; pdb.set_trace()

                if order_line != self and product in order_line.product_template_id:
                    
                    raise ValidationError("You have already added that product")
                

            # check product in all customer related sale order
            for order in self.order_id.partner_id.sale_order_ids:
               
                # discard the current sale order
                if order != self.order_id._origin:   

                    for order_line in order.order_line:
                        
                        if  order_line != self._origin and product in order_line.product_template_id:
                            
                            raise ValidationError(f"Product \"{product.name}\" Already Exists in {order.name}")
                        
            












    # @api.onchange('price_unit')
    # def change_domain(self):
    #     return {'domain': {'product_template_id': [('id','=',self.product_template_id.id)]}}
                        
                    

