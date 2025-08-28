from odoo import api, fields, _, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    shopify_product_id = fields.Char()
    shopify_store_id = fields.Char()

    # @api.onchange('name')
    # def name_change(self):
    #     import pdb; pdb.set_trace()


# for variants
class ProductProduct(models.Model):
    _inherit = "product.product"

    shopify_product_variant_id = fields.Char()
    shopify_store_id = fields.Char()



    