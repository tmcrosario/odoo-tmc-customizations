from odoo import fields, models


class TmcSystem(models.Model):
    _inherit = "tmc.system"

    # Odoo app this system maps to; the systray scopes the bell by it.
    app_menu_id = fields.Many2one(
        "ir.ui.menu",
        string="App Menu",
        domain="[('parent_id', '=', False)]",
    )

    _app_menu_uniq = models.Constraint(
        "unique(app_menu_id)",
        "This app is already mapped to a system.",
    )
