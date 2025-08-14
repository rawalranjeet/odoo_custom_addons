from odoo import models, fields, api

class ComponentService(models.Model):
    _name = 'property.component.service'
    _description = 'Component Services'

    name = fields.Char(required=True)
    component_id = fields.Many2one('property.component')
    service_id = fields.Many2one('product.product', string="Service")
    primer_product_id = fields.Many2one('product.product', string="Primer Product")
    paint_product_id = fields.Many2one('product.product', string="Paint Product")
    paint_layers = fields.Integer(string="No. of Layers")