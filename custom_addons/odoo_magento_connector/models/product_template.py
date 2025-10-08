from odoo import api, fields, _, models
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    magento_instance_id = fields.Many2one("magento.instance")
    magento_sku_id = fields.Char()
    magento_tax_class_id = fields.Integer()

    sync_to_magento = fields.Boolean()


    def write(self, vals):

        
        res = super(ProductTemplate, self).write(vals)
    
        if self.env.context.get('from_magento_operation'):
            return res
        
        
        for product_template in self:
            
            
            if product_template.magento_sku_id and product_template.magento_instance_id:
                result = product_template.magento_instance_id.magento_update_product(product_template, vals)
                if not result:
                    raise UserError("Failed to update product in Magento")
                
            elif product_template.sync_to_magento and product_template.magento_instance_id and not product_template.magento_sku_id:
                result = product_template.magento_instance_id.magento_create_product(product_template)

                if not result:
                    raise UserError("Failed to create product in Magento")

                product_template.with_context(from_magento_operation = True).write({
                    'magento_sku_id': result.get('sku'),
                })
                

        return res
    
    @api.model_create_multi
    def create(self, vals_list):

        products = super().create(vals_list)

        if not self.env.context.get('from_magento_operation'):

            for product in products:
                if product.sync_to_magento:
                    result = product.magento_instance_id.magento_create_product(product)

                    product.with_context(from_magento_operation = True).write({
                        'magento_sku_id': result.get('sku'),
                    })

        return products 



    def unlink(self):

        if self.env.context.get('from_magento_operation'):
            return super().unlink()

        magento_sku_ids = []
        magento_instance_id = False

        for product in self:
            if product.magento_sku_id and product.magento_instance_id:
                magento_sku_ids.append(product.magento_sku_id)
                magento_instance_id = product.magento_instance_id

        res = super().unlink()

        
        if magento_sku_ids:
            result = magento_instance_id.magento_delete_products(magento_sku_ids)

            if result is False:
                raise UserError("Failed to delete product in Magento")

        return res

        # for product in self:
        #     if product.magento_sku_id and product.magento_instance_id:
        #         result = product.magento_instance_id.magento_delete_product(product)

        #         if result is False:
        #             raise UserError("Failed to delete product in Magento")

        # return super().unlink()

        
