from psycopg2 import IntegrityError

from odoo.tests import common, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestNotificationSystem(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Test-only names: tmc.system has UNIQUE(name) and real rows may exist.
        cls.sys_gd = cls.env["tmc.system"].create({"name": "WN Test System A"})
        cls.sys_sicon = cls.env["tmc.system"].create({"name": "WN Test System B"})
        cls.env["web.notification.origin"].create(
            {
                "model_id": cls.env["ir.model"]._get_id("res.partner"),
                "system_id": cls.sys_gd.id,
            }
        )
        cls.env["web.notification.origin"].create(
            {
                "model_id": cls.env["ir.model"]._get_id("res.company"),
                "system_id": cls.sys_sicon.id,
            }
        )
        # A kind bound to SICON only; must not be usable by a GD origin.
        cls.kind_sicon = cls.env["web.notification.kind"].create(
            {
                "name": "Concession due",
                "code": "sicon_due",
                "system_id": cls.sys_sicon.id,
            }
        )
        cls.user = cls.env.ref("base.user_admin")
        cls.partner = cls.env["res.partner"].create({"name": "P"})
        cls.Notif = cls.env["web.notification"].with_user(cls.user)

    def _schedule(self, **overrides):
        vals = {
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "user_id": self.user.id,
            "event_key": "evt",
            "notification_kind": "assignment",
            "name": "s",
        }
        vals.update(overrides)
        return self.Notif._schedule_notification(**vals)

    def test_system_derived_from_origin(self):
        notif = self._schedule()
        self.assertEqual(notif.system_id, self.sys_gd)

    def test_origin_reference_resolves_for_readable_record(self):
        notif = self._schedule()
        self.assertEqual(notif.origin, self.partner)

    def test_global_kind_usable_by_any_system(self):
        # "assignment" is a global base kind (no system_id).
        notif = self._schedule()
        self.assertEqual(notif.kind_id.code, "assignment")

    def test_app_specific_kind_rejected_for_other_app(self):
        with self.assertRaises(ValueError):
            self._schedule(event_key="mismatch", notification_kind="sicon_due")

    def test_app_specific_kind_accepted_for_its_app(self):
        notif = self.Notif._schedule_notification(
            res_model="res.company",
            res_id=self.env.company.id,
            user_id=self.user.id,
            event_key="sicon-evt",
            notification_kind="sicon_due",
            name="s",
        )
        self.assertEqual(notif.system_id, self.sys_sicon)
        self.assertEqual(notif.kind_id, self.kind_sicon)

    def test_unknown_kind_code_raises(self):
        with self.assertRaises(ValueError):
            self._schedule(event_key="bad", notification_kind="does_not_exist")

    def test_stored_system_recomputed_when_origin_moves(self):
        notif = self._schedule()
        self.assertEqual(notif.system_id, self.sys_gd)
        origin = self.env["web.notification.origin"].search(
            [("res_model", "=", "res.partner")]
        )
        origin.write({"system_id": self.sys_sicon.id})
        self.assertEqual(notif.system_id, self.sys_sicon)

    def test_unseen_count_filtered_by_system(self):
        self._schedule()
        self.assertEqual(self.Notif.notification_unseen_count(self.sys_gd.id), 1)
        self.assertEqual(self.Notif.notification_unseen_count(self.sys_sicon.id), 0)

    def test_systray_data_maps_current_app_to_system(self):
        self._schedule()
        menu = self.env["ir.ui.menu"].create({"name": "WN GD App"})
        self.sys_gd.app_menu_id = menu.id
        data = self.Notif.notification_systray_data(menu.id)
        self.assertEqual(data["system_id"], self.sys_gd.id)
        self.assertEqual(data["count"], 1)

    def test_systray_hidden_for_unmapped_app(self):
        menu = self.env["ir.ui.menu"].create({"name": "WN Other App"})
        data = self.Notif.notification_systray_data(menu.id)
        self.assertFalse(data["system_id"])

    def test_systray_hidden_when_system_has_no_origin(self):
        menu = self.env["ir.ui.menu"].create({"name": "WN Empty App"})
        self.env["tmc.system"].create(
            {"name": "WN Test System C", "app_menu_id": menu.id}
        )
        data = self.Notif.notification_systray_data(menu.id)
        self.assertFalse(data["system_id"])

    def test_systray_action_is_system_scoped(self):
        action = self.Notif.notification_systray_action(self.sys_sicon.id)
        self.assertIn(("system_id", "=", self.sys_sicon.id), action["domain"])
        # Flat, system-less view with no group-by in a single-system context.
        scoped = self.env.ref("web_notification.web_notification_view_list_scoped")
        self.assertEqual(action["view_id"], scoped.id)
        self.assertNotIn("search_default_group_system", action.get("context", {}))

    def test_systray_action_missing_system_no_crash(self):
        action = self.Notif.notification_systray_action(999999)
        self.assertEqual(action["res_model"], "web.notification")

    @mute_logger("odoo.sql_db")
    def test_app_menu_unique_across_systems(self):
        menu = self.env["ir.ui.menu"].create({"name": "WN Shared App"})
        self.sys_gd.app_menu_id = menu.id
        self.sys_gd.flush_recordset()
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.sys_sicon.app_menu_id = menu.id
            self.sys_sicon.flush_recordset()
