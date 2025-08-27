from odoo import api, fields, _, models


class ShopifyProducts(models.Model):
    _name = "shopify.products"
    _description = "Shopify Products"

    name = fields.Char("Name")
    price = fields.Char("Price")
    description = fields.Html("Description")