# -*- coding: utf-8 -*-
{
    'name': 'ct_import_products',
    'summary': 'ct_import_products',
    'description': """Import Products""",
    'category': 'Sales/Sales',
    'author': 'CodeTrade India Pvt Ltd',
    'website': 'https://www.codetrade.io',
    'version': '18.0.0.1',
    'depends': ['product','account','uom'],
    'data': [
        'data/uom_data.xml',
        'security/ir.model.access.csv',
        'views/product_view.xml',
    ],
}
