{
    "name": "Connector Phone CloudCTI Event Manager",
    "category": "web",
    "summary": "This module integrates odoo with Phone Connector CloudCTI.",
    "version": "12.0.1.0.0",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "depends": ["base_phone_cdr", "inputmask_widget"],
    "data": [
             "views/template.xml",
             "views/res_company.xml",
             "views/res_users_view.xml",
             "views/res_partner_views.xml",
            ],
    "qweb": ["static/src/xml/widget.xml"],
    "license": "AGPL-3",
}
