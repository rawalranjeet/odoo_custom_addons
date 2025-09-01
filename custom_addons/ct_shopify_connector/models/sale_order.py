from odoo import api, _, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    shopify_order_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    shopify_order_line_item_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")

class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"

    shopify_order_line_item_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")


