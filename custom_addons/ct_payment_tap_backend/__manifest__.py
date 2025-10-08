# -*- coding: utf-8 -*-
{
    'name':'Backend Payment: Tap',
    'version': '18.0.1.0.1',
    'category': 'Accounting/Payment Providers',
    'summary': 'Extends Tap payment integration to allow backend payments on customer invoices.',
    'description': """This module extends the *Payment Provider: Tap* integration by enabling backend payments for customer invoices.  
    With this addon, Odoo users can register and process customer invoice payments through Tap directly from the backend.""",
    'author': 'CodeTrade India Pvt Ltd',
    'company': 'CodeTrade India Pvt Ltd',
    'maintainer': 'CodeTrade India Pvt Ltd',
    'website': 'https://www.codetrade.io',
    'depends': ['ct_payment_tap', 'contacts'],
    'data': [
       'views/account_payment_register.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}