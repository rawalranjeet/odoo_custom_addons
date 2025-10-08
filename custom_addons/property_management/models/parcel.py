from odoo import api, fields, models


class Municipality(models.Model):
    _name = 'property.municipality'
    _description = 'Municipality'

    name = fields.Char(string='Name', required=True)


class FemaFloodType(models.Model):
    _name = 'property.fema.flood.type'
    _description = 'FEMA Flood Type'

    name = fields.Char(string='Name', required=True)

class PropertyParcel(models.Model):
    _name = 'property.parcel'
    _description = 'Property Parcel'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=False)
    address_id = fields.Many2one('res.partner', string='Address')
    municipality_id = fields.Many2one('property.municipality', string='Municipality')
    owner_id = fields.Many2one('res.partner', string='Owner')
    # latitude = fields.Float(string='Latitude', compute='_compute_coordinates', store=False, readonly=True)
    # longitude = fields.Float(string='Longitude', compute='_compute_coordinates', store=False, readonly=True)
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    centroid_coordinates = fields.Integer(string='Centroid Coordinates')
    size = fields.Float(string='Size')
    size_type = fields.Selection(
        [('acres', 'Acres'), ('sqft', 'Square Feet')],
        string='Size Type',
        default='acres'
    )
    zoning_type = fields.Selection(
        [('residential', 'Residential'), ('commercial', 'Commercial'), ('industrial', 'Industrial')],
        string='Zoning Type'
    )
    last_sale_date = fields.Date(string='Last Sale Date')
    fema_flood_zone = fields.Boolean(string='FEMA Flood Zone')
    fema_flood_type_id = fields.Many2one('property.fema.flood.type', string='FEMA Flood Zone Type')
    total_parcel_value = fields.Monetary(string='Total Parcel Value', currency_field='currency_id')
    land_value = fields.Monetary(string='Land Value', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company')
    notes = fields.Html(string='Notes')


    # @api.depends('owner_id.partner_latitude', 'owner_id.partner_longitude')
    # def _compute_coordinates(self):
    #     for record in self:
    #         record.latitude = record.owner_id.partner_latitude or 0.0
    #         record.longitude = record.owner_id.partner_longitude or 0.0

    # def _compute_parcel_id(self):
    #     for record in self:
    #         record.parcel_id = record.id

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name
