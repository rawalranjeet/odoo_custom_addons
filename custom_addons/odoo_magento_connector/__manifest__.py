# -*- coding: utf-8 -*-
{
    'name': "Odoo Magento2 Connector",
    'summary': "Integrate and synchronize your Odoo platform with Magento 2.",
    'description': """
Odoo Magento2 Connector
=======================
This module allows for the seamless integration between Odoo and Magento 2,
enabling two-way synchronization of crucial data such as products,
customers, sales orders, and inventory levels.
    """,
    'author': "Magenest",
    'website': "",
    'category': 'Productivity/Connector',
    'version': '18.0.1.0',
    'depends': [
       'base', 'product', 'sale', 'sale_management', 'website'
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'views/magento_instance_views.xml',
        'views/product_template_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'wizards/magento_operation_wizard_views.xml',
        'views/website_menu.xml',
    ],
    
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
