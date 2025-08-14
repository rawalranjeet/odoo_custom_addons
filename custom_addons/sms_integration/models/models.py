from odoo import fields, api, models
from odoo.exceptions import UserError


class CustomSMSIntegration(models.Model):
    _name = "customsms.sms"
    _description = "Custom SMS"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    

    state = fields.Selection(selection=[('draft','Draft'),('delivered','Delivered'),('failed','Failed')], default = "draft")
    contact = fields.Many2one('res.partner', required=True)
    number = fields.Char(required=True , string="To")
    message = fields.Text(required=True)


    def send_sms(self):

        # self.write({
        #     'state':'delivered'
        # })

        # self.message_post(
        #     body='Test'
        # )

        # import pdb; pdb.set_trace()
        
        from twilio.rest import Client

        account_sid = 'AC3256cd601b7e2fb9ceba86ddecfd080b'
        auth_token = '2faeecde4a7d943411d1e89744e4504b'
        client = Client(account_sid, auth_token)

        try:

            msg = client.messages.create(
                from_='+17622382361',
                body=self.message,
                to= self.number
                )
            self.write({
                'state':'delivered'
            })

            self.message_post(body=msg)

        except Exception as e:
            self.state = 'failed'

            self.message_post(body= e.msg)
            # raise UserError("Invalid Details")

        
    def button_draft(self):
        self.write({
            'state':'draft'
        })

    


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_number = fields.Integer()