from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestNotificationLifecycle(common.TransactionCase):
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
        # Act as an active admin so owner-guarded actions run.
        cls.user = cls.env.ref("base.user_admin")
        cls.partner = cls.env["res.partner"].create({"name": "Origin Partner"})
        cls.Notif = cls.env["web.notification"].with_user(cls.user)

    def _schedule(self, **overrides):
        vals = {
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "user_id": self.user.id,
            "event_key": "evt-1",
            "notification_kind": "assignment",
            "name": "Please review",
        }
        vals.update(overrides)
        return self.Notif._schedule_notification(**vals)

    def _today(self):
        return fields.Date.context_today(self.Notif)

    def _active_domain(self):
        today = self._today()
        return [
            ("state", "=", "pending"),
            "|",
            ("snooze_until", "=", False),
            ("snooze_until", "<=", today),
        ]

    def _snoozed_domain(self):
        return [("state", "=", "pending"), ("snooze_until", ">", self._today())]

    def test_schedule_creates_pending(self):
        notif = self._schedule()
        self.assertEqual(notif.state, "pending")
        self.assertEqual(notif.user_id, self.user)

    def test_schedule_rejects_unlisted_origin(self):
        with self.assertRaises(ValueError):
            self._schedule(res_model="res.company", res_id=self.env.company.id)

    def test_deduplication(self):
        first = self._schedule()
        second = self._schedule()
        self.assertEqual(first, second)
        self.assertEqual(
            self.Notif.search_count(
                [("res_id", "=", self.partner.id), ("event_key", "=", "evt-1")]
            ),
            1,
        )

    def test_new_occurrence_after_done(self):
        first = self._schedule()
        first.action_mark_seen()
        second = self._schedule()
        self.assertNotEqual(first, second)
        self.assertEqual(second.state, "pending")

    def test_mark_seen_stamps_done(self):
        notif = self._schedule()
        notif.action_mark_seen()
        self.assertEqual(notif.state, "done")
        self.assertTrue(notif.done_at)

    def test_snooze_keeps_deadline_and_pending(self):
        deadline = self._today()
        notif = self._schedule(date_deadline=deadline)
        future = self._today() + timedelta(days=3)
        notif.action_snooze(future)
        self.assertEqual(notif.state, "pending")
        self.assertEqual(notif.snooze_until, future)
        self.assertEqual(notif.date_deadline, deadline)

    def test_snooze_rejects_today(self):
        notif = self._schedule()
        with self.assertRaises(UserError):
            notif.action_snooze(self._today())

    def test_snooze_accepts_iso_string(self):
        notif = self._schedule()
        future = self._today() + timedelta(days=3)
        notif.action_snooze(future.isoformat())
        self.assertEqual(notif.snooze_until, future)

    def test_snooze_rejects_non_pending(self):
        notif = self._schedule()
        notif.action_mark_seen()
        with self.assertRaises(UserError):
            notif.action_snooze(self._today() + timedelta(days=1))

    def test_active_excludes_future_snooze(self):
        notif = self._schedule()
        notif.action_snooze(self._today() + timedelta(days=2))
        self.assertNotIn(notif, self.Notif.search(self._active_domain()))

    def test_snoozed_inbox_includes_future(self):
        notif = self._schedule()
        notif.action_snooze(self._today() + timedelta(days=2))
        self.assertIn(notif, self.Notif.search(self._snoozed_domain()))

    def test_reactivate_snoozed(self):
        notif = self._schedule()
        notif.action_snooze(self._today() + timedelta(days=3))
        notif.action_reactivate()
        self.assertFalse(notif.snooze_until)
        self.assertEqual(notif.state, "pending")
        self.assertIn(notif, self.Notif.search(self._active_domain()))

    def test_reactivate_seen(self):
        notif = self._schedule()
        notif.action_mark_seen()
        self.assertEqual(notif.state, "done")
        notif.action_reactivate()
        self.assertEqual(notif.state, "pending")
        self.assertFalse(notif.done_at)

    @mute_logger("odoo.sql_db")
    def test_reactivate_seen_collision_raises(self):
        first = self._schedule()
        first.action_mark_seen()
        second = self._schedule()
        self.assertNotEqual(first, second)
        with self.assertRaises(UserError):
            first.action_reactivate()

    def test_resolve_pending_stamps_done(self):
        notif = self._schedule()
        resolved = self.Notif._resolve_pending(
            res_model="res.partner", res_id=self.partner.id
        )
        self.assertEqual(resolved, 1)
        self.assertEqual(notif.state, "done")
        self.assertTrue(notif.done_at)

    def test_constraint_collision_keeps_transaction_usable(self):
        self._schedule()
        # Duplicate hits the unique index; savepoint must leave the cursor usable.
        self._schedule()
        self.assertTrue(self.env["res.partner"].search([], limit=1))
