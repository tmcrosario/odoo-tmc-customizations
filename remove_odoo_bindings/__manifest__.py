# Based on 'disable_odoo_online' module by Therp BV
# Copyright (C) 2013 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Remove odoo.com Bindings",
    "version": "14.0.1.0.0",
    "author": "Therp BV, GRAP, Odoo Community Association (OCA), TMC Rosario",
    "license": "AGPL-3",
    "category": "base",
    "data": ["data/ir_ui_menu.xml"],
    "qweb": [
        "static/src/xml/base.xml",
    ],
    "installable": True,
}  # yapf: disable
