from odoo import http
from odoo.http import request

class PortalPartnerForm(http.Controller):

    @http.route('/my/partner-data', type="http", csrf=False, website=True)
    def partner_data(self,**kw):
        partner_records = request.env['res.partner'].search([])

        return request.render('website_partner_form.partner_data',{
            'partner_records': partner_records
            })


    @http.route('/my/partner-form', type="http", csrf=False, website=True)
    def partner_form(self,**kw):

        return request.render('website_partner_form.partner_form', {
            'partner_form':True
            })
    

    @http.route('/my/partner-form/submit', type="http", csrf=False, website=True)
    def partner_form_submit(self,**kw):

        name = kw.get('name')
        email = kw.get('email')
        phone = kw.get('phone')

        if name:
            
            vals = {
                'name':name,
                'email':email,
                'phone':phone,
            }

            request.env['res.partner'].create(vals)

        return request.redirect('/my/partner-form/thank-you')
    
    
    @http.route('/my/partner-form/thank-you', type="http", csrf=False, website=True)
    def partner_form_thankyou(self,**kw):
        # import pdb; pdb.set_trace()

        
        
        return request.render('website.contactus_thanks')
    
    