{
    'name':'SMS Integration',
    'summary': 'SMS Integration',
    'description':"""Send and Receive SMS""",
    'category': 'SMS',
    'author': 'Ranjeet Rawal',
    'website': 'https://www.codetrade.io',
    'version': '18.0.0.1',
    'depends': ['base','mail','contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/sms_view.xml',
    ],
    'assets':{
        'web.assets_frontend':[

        ],
        'web.assets_backend':[
           
        ]
    },
    "installable": True,
    "application": True,
}