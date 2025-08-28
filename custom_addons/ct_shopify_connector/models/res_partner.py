from odoo import api, _, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    shopify_customer_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")


   
    

    