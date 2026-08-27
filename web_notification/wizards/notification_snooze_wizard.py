from datetime import timedelta

from odoo import fields, models


class WebNotificationSnoozeWizard(models.TransientModel):
    _name = "web.notification.snooze.wizard"
    _description = "Snooze Notification Wizard"

    notification_id = fields.Many2one(
        "web.notification",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    snooze_until = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self) + timedelta(days=1),
    )

    def action_confirm(self):
        self.ensure_one()
        # Delegate to the secure model method: it re-checks ownership, pending
        # state and future date before writing.
        self.notification_id.action_snooze(self.snooze_until)
        return {"type": "ir.actions.act_window_close"}
