from odoo import models, fields, api
from odoo.http import request


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    property_id = fields.Many2one('property.property', string="Property", domain="[('partner_id', '=', partner_id)]")
    component_order_line_ids = fields.One2many('property.component.order.line', 'sale_order_id', string="Component Order Lines")
    survey_response_line_ids = fields.One2many('survey.user_input.line','sale_order_id',string="Survey Answers", compute="_compute_survey_response_lines", readonly=False)
    preparation_line_ids = fields.One2many('property.component.component','sale_order_id',string="Preparation Tab", compute="_compute_preparation_lines")
    attachment_ids = fields.One2many(
        'sale.order.attachment',
        'sale_order_id',
        compute="_compute_sale_order_attachment_line_ids",
        string="Attachments"
    )
    job_summary = fields.Char(string="Job Summary")

    def _compute_sale_order_attachment_line_ids(self):
        for order in self:
            room_lines = self.env['property.room.line'].search([
                ('property_id', '=', order.property_id.id),
            ]).filtered(lambda r: r.attachment_ids)

            order.attachment_ids.unlink()
            for room_line in room_lines:
                line = self.env['sale.order.attachment'].create({
                    'sale_order_id': order.id,
                    'room_name':  room_line.room_id.name or 'Room Attachment',
                    'prep_name':  '',
                    'attachment_type': 'room',
                    'attachment_ids': [(6, 0, room_line.attachment_ids.ids)]
                })
                order.attachment_ids = [(4, line.id)]

            room_lines = self.env['property.room.line'].search([
                ('property_id', '=', order.property_id.id),
            ])
            for room_line in room_lines:
                component_room_lines = self.env['property.room.component.line'].search([
                    ('room_line_id', '=', room_line.id),
                ])
                for component_room_line in component_room_lines:
                    component_preparation_lines = self.env['property.com.preparation.line'].search([
                        ('component_line_id', '=', component_room_line.id),
                        ('room_line_id', '=', room_line.id),
                    ]).filtered(lambda r: r.attachment_ids)

                    for component_preparation_line in component_preparation_lines:
                        line = self.env['sale.order.attachment'].create({
                            'sale_order_id': order.id,
                            'room_name': room_line.room_id.name,
                            'prep_name': component_preparation_line.name,
                            'attachment_type': 'prep',
                            'attachment_ids': [(6, 0, component_preparation_line.attachment_ids.ids)]
                        })
                        # Append new attachment to order
                        order.attachment_ids = [(4, line.id)]

    @api.depends('property_id')
    def _compute_preparation_lines(self):
        for order in self:
            components = self.env['property.component.component']
            if order.property_id:
                property_id = order.property_id

                # Get all component_ids from nested structure
                room_lines = property_id.property_room_line_ids
                component_lines = room_lines.mapped('component_line_ids')
                component_ids = component_lines.mapped('component_id')
                components_with_preparation = component_ids.filtered(lambda c: c.preparation_ids)

                if components_with_preparation:
                    components = components_with_preparation
            order.preparation_line_ids = components


    def _compute_survey_response_lines(self):
        for order in self:
            if order.id:
                order.survey_response_line_ids = self.env['survey.user_input.line'].search([
                    ('sale_order_id', '=', order.id)],
                    order='create_date ASC'
                )
            else:
                order.survey_response_line_ids = False

    def add_component_services(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.component.service',
            'view_mode': 'list,form',
            'domain' : [('order_id', '=', self.id)],
            'context' : {'default_order_id' : self.id},
            'target': 'current'
        }

    def action_open_survey(self):
        if self.sale_order_template_id:
            if self.sale_order_template_id.survey_id:
                survey_rec = self.sale_order_template_id.survey_id
                request.session['current_sale_order_id'] = self.id
                survey_start_url = survey_rec.get_start_url()
                if survey_start_url:
                    return {
                            'type': 'ir.actions.act_url',
                            'target': 'new',
                            'url': survey_start_url,
                    }
                # return survey_rec.action_test_survey()
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Not Found!',
                        'message': f"No survey record found.",
                        'type': 'success',
                    }
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Not Found!',
                    'message': f"No template found.",
                    'type': 'success',
                }
            }
        

    def action_manage_property(self):
        if self.property_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'property.property',
                'view_mode': 'kanban',
                'domain' : [('id', '=', self.property_id.id)],
                'context': {
                    'order_id' : self.id
                },
                'target': 'new'
            }
        else:
            self.ensure_one()
            property_vals = {
                'partner_id': self.partner_id.id,
                'name': f"{self.partner_id.name}",
            }
            new_property = self.env['property.property'].create(property_vals)
            self.property_id = new_property.id

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'property.property',
                'view_mode': 'kanban',
                'domain': [('id', '=', new_property.id)],
                'target': 'new'
            }

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    survey_id = fields.Many2one('survey.survey', string="Survey")


class ComponentOrderLine(models.Model):
    _name = 'property.component.order.line'
    _description = 'Component Order Line'

    name = fields.Char(string="Name")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order",)
    component_id = fields.Many2one('property.component.component', string="Component", domain="[('id', 'in', available_component_ids)]")
    service_id = fields.Many2one('product.template', string="Service",)
    primer_product_id = fields.Many2one('product.product', string="Primer Product",  domain="[('categ_id.category_type', '=', 'primer')]")
    paint_product_id = fields.Many2one('product.template', string="Paint Product", domain="[('categ_id.category_type', '=', 'paint')]")
    paint_layers = fields.Integer(string="No. of Layers", default=1)
    available_component_ids = fields.Many2many('property.component.component', compute='_compute_available_components', string='Available Components')
    rooms = fields.Many2one('property.room.room', string="Rooms")
    sheen_id = fields.Many2one('product.attribute.value',string="Sheen",domain="[('attribute_id.name', '=', 'Sheen'),('pav_attribute_line_ids.product_tmpl_id', '=', paint_product_id)]")
    color_id = fields.Many2one('product.attribute.value',string="Color",domain="[('attribute_id.name', '=', 'Color'),('pav_attribute_line_ids.product_tmpl_id', '=', paint_product_id)]")
    coats = fields.Selection([
        ('guaranteed', 'Guaranteed Coverage'),
        ('1', '1'),
        ('2', '2')
    ], string='Coats', default='guaranteed')
    primer_coats = fields.Selection([
        ('spot', 'Spot'),
        ('full', 'Full')
    ], string='Primer Coats')
    note = fields.Char(string='Note', required=False)
    int_note = fields.Char(string='Int.Note', required=False)
    display_type = fields.Selection([('line_section', "Section")], default=False)
    sequence = fields.Integer(string="Sequence")

    @api.depends('sale_order_id.property_id')
    def _compute_available_components(self):
        for line in self:
            components = self.env['property.component.component']
            if line.sale_order_id and line.sale_order_id.property_id:
                property_id = line.sale_order_id.property_id

                # Get all component_ids from nested structure
                room_lines = property_id.property_room_line_ids
                component_lines = room_lines.mapped('component_line_ids')
                components = component_lines.mapped('component_id')

            line.available_component_ids = components

class SaleOrderAttachment(models.Model):
    _name = 'sale.order.attachment'
    _description = 'Sale Order Attachment'

    room_name =  fields.Char(string='Room',required=False)
    prep_name = fields.Char(string='Preparation',required=False)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order", ondelete='cascade')
    attachment_type = fields.Selection([('room', 'Room'), ('prep', 'Prep'), ], string="Type", readonly=True)
    attachment_ids = fields.Many2many("ir.attachment",string="Attachments")