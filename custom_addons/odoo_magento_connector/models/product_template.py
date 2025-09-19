from odoo import api, fields, _, models
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    magento_instance_id = fields.Many2one("magento.instance")
    magento_sku_id = fields.Char()


    def write(self, vals):
        
        if vals.get('from_import_operation'):
            del vals['from_import_operation']

            return super(ProductTemplate, self).write(vals)
        

        res = super(ProductTemplate, self).write(vals)

        for product_template in self:
            if product_template.magento_sku_id and product_template.magento_instance_id:
                result = product_template.magento_instance_id.magento_update_product(product_template, vals)

                if not result:
                    raise UserError("Failed to update product in Magento")
                

        return res
                

        
