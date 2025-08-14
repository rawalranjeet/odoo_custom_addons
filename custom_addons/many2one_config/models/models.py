from odoo import fields, models, api
from odoo.addons.web.controllers.session import Session
from odoo import http
from odoo.http import request


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
   
    edit_many2one = fields.Boolean(
        string="Disable Create/Edit Many2one",
        config_parameter='many2one_config.enable_edit_many2one',
        help="Check this to enable a Create and edit of many2one fields"
        )
    
    @api.model
    def get_model(self):
        # import pdb; pdb.set_trace()

        return self


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        
        session_info = super().session_info()

        session_info.update({
            'disable_edit_many2one': self.env['ir.config_parameter'].sudo().get_param('many2one_config.enable_edit_many2one'),
         })
        
        return session_info
        

