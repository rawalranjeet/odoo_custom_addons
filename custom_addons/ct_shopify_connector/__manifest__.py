{
    'name':'Shopify Connector',
    'category': 'Sales',
    'summary': 'Shopify',
    'description':"""Shopify""",
    'author': 'Ranjeet Rawal',
    'website': 'https://www.codetrade.io',
    'version': '18.0.1.0',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/shopify_customers_wizard_view.xml',
        'wizards/shopify_products_wizard_view.xml',
        'views/shopify_store_views.xml',
        'views/shopify_webhooks_views.xml',
        'views/product_template_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets':{
        'web.assets_frontend':[
            
        ],
    },
    'application':True,
    'installable':True,
}