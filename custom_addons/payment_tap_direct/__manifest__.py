{
    'name':'Payment Provider: Tap',
    'summary': 'Payment Provider: Tap',
    'description':"""Payment Provider: Tap""",
    'category': 'Payment',
    'author': 'Ranjeet Rawal',
    'website': 'https://www.codetrade.io',
    'version': '18.0.0.1',
    'depends': ['payment','account','website'],
    'data': [
       'views/payment_provider_views.xml',
       'views/payment_tap_template.xml',
       'data/payment_method_data.xml',
       'data/payment_provider_data.xml',
    ],
    'assets':{
        'web.assets_frontend':[
            'payment_tap_direct/static/src/js/payment_form.js',
        ],
        'web.assets_backend':[
           
        ]
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}