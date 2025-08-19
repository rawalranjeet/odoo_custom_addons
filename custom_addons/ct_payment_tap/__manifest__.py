{
    'name':'Payment Provider: Tap',
    'category': 'Accounting/Payment Providers',
    'summary': 'Connects Tap payment gateway to Odoo for reliable and convenient payment transactions.',
    'description':"""Tap payment gateway integration for Odoo, offering smooth and secure online payment solutions.""",
    'author': 'Ranjeet Rawal',
    'website': 'https://www.codetrade.io',
    'version': '18.0.1.0',
    'depends': ['payment','account','website'],
    'data': [
       'views/payment_provider_views.xml',
       'views/payment_tap_template.xml',
       'data/payment_method_data.xml',
       'data/payment_provider_data.xml',
    ],
    'assets':{
        'web.assets_frontend':[
            'ct_payment_tap/static/src/js/payment_form.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}