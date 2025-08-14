{
    "name": "Property Management",
    "version": "1.0",
    "summary": "Propery Management",
    "category": "Sales",
    "depends": ["sale_management", "product"],
    "data": [
        "security/ir.model.access.csv",
        "views/property_views.xml",
        "views/room_views.xml",
        "views/component_views.xml",
        "views/sale_order_views.xml",
    ],
    "assets": {},
    "installable": True,
    "application": True,
}