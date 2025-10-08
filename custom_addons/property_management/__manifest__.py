{
    "name": "Property Management",
    "version": "1.0",
    "summary": "Propery Management",
    "category": "Sales",
    "depends": ["sale_management", "product", "survey", "web_map", "base_geolocalize", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "data/product_category_data.xml",
        "views/property_views.xml",
        "views/room_views.xml",
        "views/component_views.xml",
        "views/sale_order_views.xml",
        "views/survey.xml",
        "views/survey_template.xml",
        "views/preparation_view.xml",
        "views/property_component_service.xml",
        "views/product_category_views.xml",
        "views/component_type_view.xml",
        "views/parcel_views.xml",
        "views/parcel_municipality_views.xml",
        "reports/sale_quotation_reports.xml",
        "wizard/property_room_edit_name_wizard_view.xml",
        "wizard/property_room_edit_notes_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "property_management/static/scss/button.scss",
            "property_management/static/src/js/component_kanban.js",
            "property_management/static/src/xml/kanban_template.xml",
            "property_management/static/src/xml/m2m_field_preview_template.xml",
            "property_management/static/src/js/m2m_field_preview.js",
            "property_management/static/src/js/kanban_attachment.js",

        ],
        "web.assets_frontend":[
            "property_management/static/src/js/custom_survey.js",
        ]
    },
    "installable": True,
    "application": True,
}