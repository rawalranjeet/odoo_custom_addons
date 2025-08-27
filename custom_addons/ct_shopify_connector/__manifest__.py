{
    'name':'Shopify Connector',
    'category': 'Sales',
    'summary': 'Shopify',
    'description':"""Shopify""",
    'author': 'Ranjeet Rawal',
    'website': 'https://www.codetrade.io',
    'version': '18.0.1.0',
    'depends': [],
    'data': [
        'security/ir.model.access.csv',
        'views/shopify_store_views.xml',
        'views/shopify_webhooks_views.xml',
        'views/shopify_products_views.xml',
    ],
    'assets':{
        'web.assets_frontend':[
            
        ],
    },
    'application':True,
    'installable':True,
}