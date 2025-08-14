from odoo import models, fields, api

class Components(models.Model):
    _name = 'component.component'
    _description = 'Components'

    name = fields.Char(required=True)
    

    def action_add_to_property_room(self):
        room_line_id = self.env.context.get('default_room_line_id')
        room_line = self.env['property.room.line'].browse(room_line_id)
        property_id = room_line.property_id.id
        room_id = room_line.room_id.id

        if room_id and property_id:
            # Create or link in property component line
            self.env['room.component.line'].create({
                'property_id': property_id,
                'room_line_id': room_id,
                'component_id': self.id
            })

            # Optional: recompute or log
            property_rec = self.env['property.property'].browse(property_id)
            property_rec._compute_total_components()
        
        return {'type': 'ir.actions.act_window_close'}