from odoo import models, fields, api
from odoo.http import request

class ComponentsType(models.Model):
    _name = 'property.component.type'
    _description = 'Components Type'
    _rec_name = 'name'

    name = fields.Char(required=True)