{
    'name':'Equipment Custom Display Name',
    'summary': 'Equipment Custom Display Name',
    'description':"""Custom field to change the display name in quipment display name""",
    'category': 'Maintenance',
    'author': 'Ranjeet Rawal',
    'website': 'https://www.codetrade.io',
    'version': '18.0.0.1',
    'depends': ['base','maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        
    ],
    'assets':{
        'web.assets_frontend':[

        ],
        'web.assets_backend':[
           
        ]
    },
}