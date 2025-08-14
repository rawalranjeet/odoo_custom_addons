from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    property_id = fields.Many2one('property.property', string="Property", domain="[('partner_id', '=', partner_id)]")
    component_order_line_ids = fields.One2many('component.order.line', 'sale_order_id', string="Component Order Lines")


class ComponentOrderLine(models.Model):
    _name = 'component.order.line'
    _description = 'Component Order Line'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order",)
    component_id = fields.Many2one('component.component', string="Component", domain="[('id', 'in', available_component_ids)]")
    service_id = fields.Many2one('product.product', string="Service",)
    primer_product_id = fields.Many2one('product.product', string="Primer Product")
    paint_product_id = fields.Many2one('product.product', string="Paint Product")
    paint_layers = fields.Integer(string="No. of Layers", default=1)
    available_component_ids = fields.Many2many('component.component', compute='_compute_available_components', string='Available Components')

    @api.depends('sale_order_id.property_id')
    def _compute_available_components(self):
        for line in self:
            components = self.env['component.component']
            if line.sale_order_id and line.sale_order_id.property_id:
                property_id = line.sale_order_id.property_id

                # Get all component_ids from nested structure
                room_lines = property_id.property_room_line_ids
                component_lines = room_lines.mapped('component_line_ids')
                components = component_lines.mapped('component_id')

            line.available_component_ids = components
