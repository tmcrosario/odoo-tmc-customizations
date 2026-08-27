from datetime import timedelta

from odoo import fields
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestNotificationBadge(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = cls.env["tmc.system"].create({"name": "Test App"})
        cls.env["web.notification.origin"].create(
            {
                "model_id": cls.env["ir.model"]._get_id("res.partner"),
                "system_id": cls.app.id,
            }
        )
        # Plain internal user — no notification group exists.
        cls.user = cls.env["res.users"].create(
            {"name": "Badge User", "login": "wn_badge_user"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "P"})
        cls.Notif = cls.env["web.notification"]

    def _schedule(self, event_key, **kwargs):
        return self.Notif._schedule_notification(
            res_model="res.partner",
            res_id=self.partner.id,
            user_id=self.user.id,
            event_key=event_key,
            notification_kind="assignment",
            name="s",
            **kwargs,
        )

    def _count(self):
        return self.Notif.with_user(self.user).notification_unseen_count()

    def test_counts_pending(self):
        self._schedule("e1")
        self.assertEqual(self._count(), 1)

    def test_excludes_future_snoozed(self):
        notif = self._schedule("e2")
        future = fields.Date.context_today(self.Notif) + timedelta(days=5)
        notif.with_user(self.user).action_snooze(future)
        self.assertEqual(self._count(), 0)

    def test_counts_matured_snooze(self):
        notif = self._schedule("e4")
        # Past-dated snooze is active again; set directly (action_snooze rejects past).
        past = fields.Date.context_today(self.Notif) - timedelta(days=1)
        notif.sudo().write({"snooze_until": past})
        self.assertEqual(self._count(), 1)

    def test_excludes_done(self):
        notif = self._schedule("e3")
        notif.with_user(self.user).action_mark_seen()
        self.assertEqual(self._count(), 0)

    def test_action_xmlid_targets_model(self):
        action = self.env.ref("web_notification.action_web_notification_active")
        self.assertEqual(action.res_model, "web.notification")
