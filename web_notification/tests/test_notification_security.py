from odoo.exceptions import AccessError, UserError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestNotificationSecurity(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = cls.env["tmc.system"].create({"name": "Test App"})
        cls.kind = cls.env.ref("web_notification.notification_kind_assignment")
        cls.env["web.notification.origin"].create(
            {
                "model_id": cls.env["ir.model"]._get_id("res.partner"),
                "system_id": cls.app.id,
            }
        )
        # Plain internal users; every internal user is a recipient.
        cls.user_a = cls.env["res.users"].create(
            {"name": "User A", "login": "wn_user_a"}
        )
        cls.user_b = cls.env["res.users"].create(
            {"name": "User B", "login": "wn_user_b"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Origin"})
        cls.Notif = cls.env["web.notification"]
        cls.notif_a = cls.Notif._schedule_notification(
            res_model="res.partner",
            res_id=cls.partner.id,
            user_id=cls.user_a.id,
            event_key="a",
            notification_kind="assignment",
            name="For A",
        )
        cls.notif_b = cls.Notif._schedule_notification(
            res_model="res.partner",
            res_id=cls.partner.id,
            user_id=cls.user_b.id,
            event_key="b",
            notification_kind="assignment",
            name="For B",
        )

    def test_plain_internal_user_has_scoped_inbox(self):
        # A user with only base.group_user (no special group) sees their own.
        visible = self.Notif.with_user(self.user_a).search([])
        self.assertIn(self.notif_a, visible)
        self.assertNotIn(self.notif_b, visible)

    def test_counter_is_own_scope(self):
        count = self.Notif.with_user(self.user_a).notification_unseen_count()
        self.assertEqual(count, 1)

    def test_user_cannot_write_protected_field(self):
        with self.assertRaises(AccessError):
            self.notif_a.with_user(self.user_a).write({"state": "done"})

    def test_user_cannot_create(self):
        with self.assertRaises(AccessError):
            self.Notif.with_user(self.user_a).create(
                {
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                    "user_id": self.user_a.id,
                    "event_key": "x",
                    "kind_id": self.kind.id,
                    "name": "x",
                }
            )

    def test_user_cannot_unlink(self):
        with self.assertRaises(AccessError):
            self.notif_a.with_user(self.user_a).unlink()

    def test_user_cannot_act_on_others_notification(self):
        with self.assertRaises(AccessError):
            self.notif_b.with_user(self.user_a).action_mark_seen()

    def test_admin_is_also_scoped_to_own(self):
        # No oversight role: even the built-in admin only sees their own.
        admin = self.env.ref("base.user_admin")
        visible = self.Notif.with_user(admin).search([])
        self.assertNotIn(self.notif_a, visible)
        self.assertNotIn(self.notif_b, visible)

    def test_producer_methods_are_not_public(self):
        # Producer API must stay '_'-prefixed so it is not RPC-dispatchable.
        self.assertFalse(hasattr(self.Notif, "schedule_notification"))
        self.assertFalse(hasattr(self.Notif, "resolve_pending"))
        self.assertTrue(hasattr(self.Notif, "_schedule_notification"))
        self.assertTrue(hasattr(self.Notif, "_resolve_pending"))

    def test_non_internal_recipient_is_skipped(self):
        portal = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Portal",
                    "login": "wn_portal",
                    "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
                }
            )
        )
        result = self.Notif._schedule_notification(
            res_model="res.partner",
            res_id=self.partner.id,
            user_id=portal.id,
            event_key="portal",
            notification_kind="assignment",
            name="Portal",
        )
        self.assertFalse(result)

    def test_open_origin_returns_action(self):
        action = self.notif_a.with_user(self.user_a).action_open_origin()
        self.assertEqual(action["res_model"], "res.partner")
        self.assertEqual(action["res_id"], self.partner.id)

    def test_open_origin_deleted_is_generic_error(self):
        partner = self.env["res.partner"].create({"name": "Temp"})
        notif = self.Notif._schedule_notification(
            res_model="res.partner",
            res_id=partner.id,
            user_id=self.user_a.id,
            event_key="tmp",
            notification_kind="assignment",
            name="Temp",
        )
        partner.unlink()
        with self.assertRaises(UserError):
            notif.with_user(self.user_a).action_open_origin()

    def test_restricted_origin_does_not_leak(self):
        # Unreadable origin → reference stays empty and opening is refused.
        self.env["web.notification.origin"].create(
            {
                "model_id": self.env["ir.model"]._get_id("ir.config_parameter"),
                "system_id": self.app.id,
            }
        )
        param = self.env["ir.config_parameter"].create(
            {"key": "wn.test.secret", "value": "secret"}
        )
        notif = self.Notif._schedule_notification(
            res_model="ir.config_parameter",
            res_id=param.id,
            user_id=self.user_a.id,
            event_key="cfg",
            notification_kind="assignment",
            name="Cfg",
        )
        self.assertFalse(notif.with_user(self.user_a).origin)
        with self.assertRaises(UserError):
            notif.with_user(self.user_a).action_open_origin()
