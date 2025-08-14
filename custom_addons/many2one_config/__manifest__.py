# -*- coding: utf-8 -*-
{
    'name': 'Many2one Config',
    'summary': 'Many2one Config',
    'description': """Enable and Disable Create and Edit for Many2one Fields""",
    'category': 'Configuration',
    'author': 'Ranjeet Rawal',
    'website': 'https://www.codetrade.io',
    'version': '18.0.0.1',
    'depends': ['base','web','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets':{
        'web.assets_frontend':[

        ],
        'web.assets_backend':[
            
            'many2one_config/static/src/js/*.js',
            'many2one_config/static/src/xml/*.xml',
            
        ]
    },
}
