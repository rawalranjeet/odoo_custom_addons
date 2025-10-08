from odoo import models, fields, api
from odoo.http import request

class Property(models.Model):
    _name = 'property.property'
    _description = 'Property'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    sale_order_id = fields.Many2one('sale.order', string="Quotation")
    property_room_line_ids = fields.One2many('property.room.line', 'property_id', string="Rooms")
    total_area = fields.Float(string="Total Area", compute='_compute_totals')
    total_components = fields.Integer(string="Total Components", compute='_compute_totals')
    room_count = fields.Integer(string="Room Count", compute="_compute_room_count")
    height = fields.Integer(string='Height', default=8)
    parcel_id = fields.Many2one('property.parcel' ,string="Parcel")

    @api.depends('property_room_line_ids')
    def _compute_totals(self):
        for prop in self:
            prop.total_area = 0
            prop.total_components = 0

    @api.depends('property_room_line_ids')
    def _compute_room_count(self):
        for prop in self:
            prop.room_count = 0
            # prop.room_count = len(prop.property_line_ids)


    def select_rooms(self):
        request.session['selected_property_id'] = self.id
        return self.env.ref('property_management.action_property_room_kanaban').read()[0]

    def action_increase_height(self):
        for record in self:
            record.height += 1
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.property',
            'view_mode': 'kanban',
            'domain' : [('id', '=', self.id)],
            'context': {
                'order_id': self.env.context.get('order_id')
            },
            'target': 'new'
        }

    def action_decrease_height(self):
        for record in self:
            if record.height > 0:
                record.height -= 1
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.property',
            'view_mode': 'kanban',
            'domain' : [('id', '=', self.id)],
            'context': {
                'order_id': self.env.context.get('order_id')
            },
            'target': 'new'
        }


class PropertyRoomLines(models.Model):
    _name = 'property.room.line'
    _description = 'Property Room Lines'
    _inherit = ['mail.thread']

    property_id = fields.Many2one('property.property', string="Property", readonly=True)
    room_id = fields.Many2one('property.room.room', string="Room")
    quantity = fields.Integer(string='Quantity', default=1)
    notes = fields.Char(string="Notes")
    height = fields.Integer(string='Height', default=8)
    width = fields.Integer(string="Width", default=8)
    length = fields.Integer(string="Length", default=8)
    component_line_ids = fields.One2many('property.room.component.line', 'room_line_id', string="Components")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        compute="_compute_attachment_ids",
        string="Attachments"
    )
    sale_order_id = fields.Many2one('sale.order', string="Sale Order",)

    def _compute_attachment_ids(self):
        for record in self:
            if record.id:
                record.attachment_ids = self.env["ir.attachment"].search([
                    ("res_model", "=", "property.room.line"),
                    ("res_id", "=", record.id)
                ])
            else:
                record.attachment_ids = False