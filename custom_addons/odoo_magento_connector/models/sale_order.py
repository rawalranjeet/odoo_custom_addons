from odoo import api, _, fields, models
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    magento_order_id = fields.Char(copy=False)
    magento_instance_id = fields.Many2one("magento.instance", copy=False)
    sync_to_magento = fields.Boolean(copy=False)
    magento_cart_id = fields.Char(copy=False) 

    def write(self, vals):
        if self.env.context.get('from_magento_operation'):
            return super(SaleOrder, self).write(vals)
        
        res = super().write(vals)
        
        for order in self:
            if order.sync_to_magento and order.magento_instance_id and not order.magento_order_id:
                result = order.magento_instance_id.magento_create_order(order)

                if not result:
                    raise UserError("Failed to create Order in Magento")

                order.with_context(from_magento_operation = True).write({
                    'magento_order_id': result.get('magento_order_id'),
                    'magento_cart_id': result.get('magento_cart_id'),
                })
                
            elif order.magento_order_id and order.magento_instance_id:
                if vals.get('state') == 'cancel':
                    result = order.magento_instance_id.magento_cancel_order(order.magento_order_id)
                    if not result:
                        raise UserError("Failed to cancel Order in Magento")
                else:
                    result = order.magento_instance_id.magento_update_order(order)

                if not result:
                    raise UserError("Failed to update Order in Magento")

        return res

    @api.model_create_multi
    def create(self, vals_list):
        

        if self.env.context.get('from_magento_operation'):
            return super().create(vals_list)

        orders = super().create(vals_list)

        for order in orders:
            if order.sync_to_magento and order.magento_instance_id and not order.magento_order_id:
                result = order.magento_instance_id.magento_create_order(order)

                if not result:
                    raise UserError("Failed to create Order in Magento")

                order.with_context(from_magento_operation = True).write({
                    'magento_order_id': result.get('magento_order_id'),
                    'magento_cart_id': result.get('magento_cart_id'),
                })

        return orders
    
    def unlink(self):
        for order in self:
            if order.magento_order_id and order.magento_instance_id:
                raise UserError(_("You cannot delete an order which is already synced with Magento."))
        return super().unlink()
    

    def action_draft(self):
        if self.magento_order_id and self.magento_instance_id:
            raise UserError(_("You cannot reset to draft an order which is already synced with Magento."))
        return super().action_draft()

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    magento_order_id = fields.Char()
    magento_instance_id = fields.Many2one("magento.instance")
    magento_discount = fields.Boolean()
    magento_is_added_line = fields.Boolean()

