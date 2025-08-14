from odoo import models, fields, api

class Property(models.Model):
    _name = 'property.property'
    _description = 'Property'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    sale_order_id = fields.Many2one('sale.order', string="Quotation")
    property_room_line_ids = fields.One2many('property.room.line', 'property_id', string="Rooms")
    total_area = fields.Float(string="Total Area")
    total_components = fields.Integer(string="Total Components")
    room_count = fields.Integer(string="Room Count", compute='_compute_room_count', store=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'property_room_line_ids' in fields_list:
            rooms = self.env['room.room'].search([])
            lines = [(0, 0, {'room_id': room.id, 'quantity': 0}) for room in rooms]
            res.update({'property_room_line_ids': lines})
        return res

    @api.depends('property_room_line_ids.quantity')
    def _compute_room_count(self):
        # import pdb;pdb.set_trace()
        for prop in self:
            prop.room_count = sum(line.quantity for line in prop.property_room_line_ids)

    def _compute_total_components(self):
        for prop in self:
            import pdb;pdb.set_trace()
            total_components = sum(len(line.component_line_ids) for line in prop.property_room_line_ids)
            prop.total_components = total_components
    # @api.depends('property_room_line_ids')
    # def _compute_totals(self):
    #     for prop in self:
    #         prop.total_area = 0
    #         prop.total_components = 0
            # area = 0.0
            # comp_count = 0
            # for room in prop.property_line_ids:
            #     for comp in room.component_ids:
            #         area += (comp.height or 0.0) * (comp.width or 0.0)
            #         comp_count += 1
            # prop.total_area = round(area, 2)
            # prop.total_components = comp_count

    # @api.depends('property_room_line_ids')
    # def _compute_room_count(self):
    #     for prop in self:
    #         prop.room_count = 0
            # prop.room_count = len(prop.property_line_ids)


class PropertyRoomLines(models.Model):
    _name = 'property.room.line'
    _description = 'Property Room Lines'

    property_id = fields.Many2one('property.property', string="Property", readonly=True)
    room_id = fields.Many2one('room.room', string="Room")
    component_line_ids = fields.One2many('room.component.line', 'room_line_id', string="Components")
    quantity = fields.Integer(string="Quantity", default=0)


    def action_add_room(self):
        for rec in self:
            rec.quantity = 1

    def action_increase_room(self):
        for rec in self:
            rec.quantity += 1

    def action_decrease_room(self):
        for rec in self:
            if rec.quantity > 1:
                rec.quantity -= 1
            else:
                rec.quantity = 0
