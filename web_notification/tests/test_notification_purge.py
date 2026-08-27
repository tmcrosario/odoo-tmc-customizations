from datetime import timedelta

from odoo import fields
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestNotificationPurge(common.TransactionCase):
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
        cls.user = cls.env.ref("base.user_admin")
        cls.partner = cls.env["res.partner"].create({"name": "P"})
        cls.Notif = cls.env["web.notification"].with_user(cls.user)

    def _schedule(self, event_key):
        return self.Notif._schedule_notification(
            res_model="res.partner",
            res_id=self.partner.id,
            user_id=self.user.id,
            event_key=event_key,
            notification_kind="assignment",
            name="s",
        )

    def _age(self, notif, days):
        # Purge anchors on done_at; flush the pending ORM write first, then age it.
        self.env.flush_all()
        old = fields.Datetime.now() - timedelta(days=days)
        self.env.cr.execute(
            "UPDATE web_notification SET done_at = %s WHERE id = %s",
            (old, notif.id),
        )
        notif.invalidate_recordset()

    def test_purges_old_resolved(self):
        notif = self._schedule("old_done")
        notif.action_mark_seen()
        self.assertEqual(notif.state, "done")
        self._age(notif, 400)
        purged = self.Notif._cron_purge_resolved()
        self.assertEqual(purged, 1)
        self.assertFalse(notif.exists())

    def test_keeps_recent_resolved(self):
        notif = self._schedule("recent_done")
        notif.action_mark_seen()
        self.Notif._cron_purge_resolved()
        self.assertTrue(notif.exists())

    def test_never_purges_pending(self):
        notif = self._schedule("old_pending")
        self._age(notif, 400)
        self.Notif._cron_purge_resolved()
        self.assertTrue(notif.exists())

    def test_retention_zero_disables_purge(self):
        notif = self._schedule("old_done2")
        notif.action_mark_seen()
        self._age(notif, 400)
        self.env["ir.config_parameter"].sudo().set_param(
            "web_notification.retention_days", "0"
        )
        purged = self.Notif._cron_purge_resolved()
        self.assertEqual(purged, 0)
        self.assertTrue(notif.exists())
