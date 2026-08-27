from odoo import fields, models


class WebNotificationOrigin(models.Model):
    _name = "web.notification.origin"
    _description = "Allowed Notification Origin Model"
    _rec_name = "res_model"

    model_id = fields.Many2one(
        "ir.model",
        string="Origin Model",
        required=True,
        ondelete="cascade",
    )
    res_model = fields.Char(
        related="model_id.model",
        string="Model Name",
        store=True,
        index=True,
    )
    system_id = fields.Many2one(
        "tmc.system",
        string="System",
        required=True,
        ondelete="cascade",
    )

    _model_uniq = models.Constraint(
        "unique(model_id)",
        "This origin model is already registered.",
    )

    def write(self, vals):
        res = super().write(vals)
        if "system_id" in vals:
            # Notifications store system_id; retrigger its recompute when an origin moves.
            self.env["web.notification"].sudo().search(
                [("res_model", "in", self.mapped("res_model"))]
            ).modified(["res_model"])
        return res
