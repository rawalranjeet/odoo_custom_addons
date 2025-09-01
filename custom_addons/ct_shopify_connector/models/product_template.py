from odoo import api, fields, _, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    shopify_product_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")

    # @api.onchange('name')
    # def name_change(self):
    #     import pdb; pdb.set_trace()

class ProductProduct(models.Model):
    _inherit = "product.product"

    # @api.onchange('name')
    # def name_change(self):
    #     import pdb; pdb.set_trace()

    shopify_product_variant_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")

    # @api.model_create_multi
    # def create(self, vals_list):
    #     products = super().create(vals_list)
    #     import pdb; pdb.set_trace()
    #     return products

# # for variants
class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    shopify_product_option_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")

class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    shopify_product_variant_id = fields.Char()
    shopify_store_id = fields.Many2one("shopify.store")

class ProductTemplateAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    shopify_product_option_id = fields.Char()





    