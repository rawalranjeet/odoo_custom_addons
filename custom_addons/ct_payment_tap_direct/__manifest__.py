# -*- coding: utf-8 -*-
{
    'name':'Direct Payment: Tap',
    'version': '18.0.1.0.2',
    'category': 'Accounting/Payment Providers',
    'summary': 'Extends Tap payment integration to allow backend payments on customer invoices.',
    'description': """This module extends the *Payment Provider: Tap* integration by enabling backend payments for customer invoices.  
    With this addon, Odoo users can register and process customer invoice payments through Tap directly from the backend.""",
    'author': 'CodeTrade India Pvt Ltd',
    'company': 'CodeTrade India Pvt Ltd',
    'maintainer': 'CodeTrade India Pvt Ltd',
    'website': 'https://www.codetrade.io',
    'depends': ['ct_payment_tap'],
    'data': [
        'views/payment_tap_template.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'assets':{
        'web.assets_frontend':[
            'ct_payment_tap_direct/static/src/js/payment_form.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}