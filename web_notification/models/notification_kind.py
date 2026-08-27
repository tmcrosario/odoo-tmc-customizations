from odoo import fields, models


class WebNotificationKind(models.Model):
    _name = "web.notification.kind"
    _description = "Notification Kind"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        index=True,
        help="Stable technical identity used by producers; not translated.",
    )
    # Empty = global; set = specific to that system.
    system_id = fields.Many2one(
        "tmc.system",
        string="System",
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)

    _code_uniq = models.Constraint(
        "unique(code)",
        "The notification kind code must be unique.",
    )
