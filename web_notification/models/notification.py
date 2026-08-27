from collections import defaultdict
from datetime import timedelta

from psycopg2 import IntegrityError, errorcodes

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class WebNotification(models.Model):
    _name = "web.notification"
    _description = "In-App Notification"
    # Soonest deadline first, undated last, then newest.
    _order = "date_deadline asc, id desc"

    res_model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)
    origin = fields.Reference(
        selection="_selection_origin_models",
        compute="_compute_origin",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Recipient",
        required=True,
        index=True,
        ondelete="cascade",
    )
    event_key = fields.Char(required=True, index=True)
    kind_id = fields.Many2one(
        "web.notification.kind",
        string="Type",
        required=True,
        index=True,
        ondelete="restrict",
    )
    system_id = fields.Many2one(
        "tmc.system",
        string="System",
        compute="_compute_system_id",
        store=True,
        index=True,
    )
    system_color = fields.Integer(related="system_id.color")
    # _rec_name/title; holds the summary line.
    name = fields.Char(string="Summary", required=True)
    note = fields.Text()
    date_deadline = fields.Date()
    snooze_until = fields.Date(index=True)
    done_at = fields.Datetime(readonly=True)
    state = fields.Selection(
        [("pending", "Pending"), ("done", "Done")],
        required=True,
        default="pending",
        index=True,
    )

    def init(self):
        # One pending row per event; partial so a new one is allowed after resolve.
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS web_notification_pending_event_uniq
            ON web_notification (res_model, res_id, user_id, kind_id, event_key)
            WHERE state = 'pending'
            """
        )

    @api.model
    def _allowed_origin_models(self):
        # This IS the allowlist — full read is intentional.
        origins = self.env["web.notification.origin"].search([])  # pylint: disable=no-search-all
        return set(origins.mapped("res_model"))

    @api.model
    def _selection_origin_models(self):
        origins = self.env["web.notification.origin"].search([])  # pylint: disable=no-search-all
        return [(origin.res_model, origin.model_id.name) for origin in origins]

    @api.depends("res_model", "res_id")
    def _compute_origin(self):
        allowed = self._allowed_origin_models()
        by_model = defaultdict(list)
        for notif in self:
            notif.origin = False
            if notif.res_model in allowed and notif.res_id:
                by_model[notif.res_model].append(notif)
        # Batch exists + read-access per model; unreadable origins stay empty.
        for res_model, notifs in by_model.items():
            model = self.env.get(res_model)
            if model is None:
                continue
            records = model.browse(notif.res_id for notif in notifs).exists()
            readable = set(records._filtered_access("read").ids)
            for notif in notifs:
                if notif.res_id in readable:
                    notif.origin = f"{res_model},{notif.res_id}"

    @api.depends("res_model")
    def _compute_system_id(self):
        origins = self.env["web.notification.origin"].search([])  # pylint: disable=no-search-all
        by_model = {origin.res_model: origin.system_id.id for origin in origins}
        for notif in self:
            notif.system_id = by_model.get(notif.res_model, False)

    @api.model
    def _schedule_notification(
        self,
        *,
        res_model,
        res_id,
        user_id,
        event_key,
        notification_kind,
        name,
        note=False,
        date_deadline=False,
    ):
        """Create one pending notification for one logical event and recipient.

        `notification_kind` is a kind CODE (resolved to a web.notification.kind).
        The system is derived from the origin. Idempotent: a repeated logical
        event returns the existing pending notification (partial unique index).
        """
        origin = self.env["web.notification.origin"].search(
            [("res_model", "=", res_model)], limit=1
        )
        if not origin:
            raise ValueError(
                f"Origin model {res_model!r} is not an allowed notification origin."
            )
        if not res_id:
            raise ValueError("A res_id is required to schedule a notification.")
        kind = self.env["web.notification.kind"].search(
            [("code", "=", notification_kind)], limit=1
        )
        if not kind:
            raise ValueError(f"Unknown notification kind {notification_kind!r}.")
        if kind.system_id and kind.system_id != origin.system_id:
            raise ValueError(
                f"Kind {notification_kind!r} does not belong to the origin's system."
            )
        recipient = self.env["res.users"].browse(user_id).exists()
        if not recipient:
            raise ValueError(f"Unknown recipient user id {user_id!r}.")
        # Only active internal users have an inbox/bell; skip others.
        if not recipient.active or recipient.share:
            return self.browse()
        vals = {
            "res_model": res_model,
            "res_id": res_id,
            "user_id": recipient.id,
            "event_key": event_key,
            "kind_id": kind.id,
            "name": name,
            "note": note or False,
            "date_deadline": date_deadline or False,
        }
        try:
            with self.env.cr.savepoint():
                return self.sudo().create(vals)
        except IntegrityError as error:
            if error.pgcode != errorcodes.UNIQUE_VIOLATION:
                raise
            return self.sudo().search(
                [
                    ("res_model", "=", res_model),
                    ("res_id", "=", res_id),
                    ("user_id", "=", recipient.id),
                    ("kind_id", "=", kind.id),
                    ("event_key", "=", event_key),
                    ("state", "=", "pending"),
                ],
                limit=1,
            )

    @api.model
    def _resolve_pending(
        self,
        *,
        res_model,
        res_id,
        notification_kinds=None,
        event_keys=None,
        user_id=None,
    ):
        """Resolve matching pending notifications and stamp done_at.

        `notification_kinds` is a list of kind CODES. Returns the number resolved.
        """
        domain = [
            ("res_model", "=", res_model),
            ("res_id", "=", res_id),
            ("state", "=", "pending"),
        ]
        if notification_kinds:
            kinds = self.env["web.notification.kind"].search(
                [("code", "in", list(notification_kinds))]
            )
            domain.append(("kind_id", "in", kinds.ids))
        if event_keys:
            domain.append(("event_key", "in", list(event_keys)))
        if user_id:
            domain.append(("user_id", "=", user_id))
        pending = self.sudo().search(domain)
        pending.write(
            {"state": "done", "done_at": fields.Datetime.now(), "snooze_until": False}
        )
        return len(pending)

    @api.model
    def _active_domain(self):
        today = fields.Date.context_today(self)
        return [
            ("state", "=", "pending"),
            "|",
            ("snooze_until", "=", False),
            ("snooze_until", "<=", today),
        ]

    @api.model
    def notification_unseen_count(self, system_id=None):
        """Current user's active pending count (record-rule scoped, no sudo);
        optionally per system. Future-snoozed are excluded."""
        domain = self._active_domain()
        if system_id:
            domain.append(("system_id", "=", system_id))
        return self.search_count(domain)

    @api.model
    def notification_systray_data(self, app_menu_id=None):
        """Systray payload: the notification-managing system mapped to the
        current app (if any) and the current user's active count for it."""
        empty = {"system_id": False, "count": 0}
        if not app_menu_id:
            return empty
        system = (
            self.env["tmc.system"]
            .sudo()
            .search([("app_menu_id", "=", app_menu_id)], limit=1)
        )
        if not system or not self._system_has_origins(system):
            return empty
        return {
            "system_id": system.id,
            "count": self.notification_unseen_count(system.id),
        }

    @api.model
    def _system_has_origins(self, system):
        return bool(
            self.env["web.notification.origin"]
            .sudo()
            .search_count([("system_id", "=", system.id)])
        )

    @api.model
    def notification_systray_action(self, system_id):
        """The 'Active' action scoped to one system (bell), using the flat
        system-less view (grouping/system column are redundant in one system)."""
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "web_notification.action_web_notification_active"
        )
        scoped_view = self.env.ref("web_notification.web_notification_view_list_scoped")
        action["domain"] = [("system_id", "=", system_id)] + self._active_domain()
        action["views"] = [(scoped_view.id, "list")]
        action["view_id"] = scoped_view.id
        action["context"] = {}
        system = self.env["tmc.system"].browse(system_id).exists()
        if system:
            action["display_name"] = system.name
        return action

    @api.model
    def _cron_purge_resolved(self):
        """Delete done notifications past the retention window, leaving pending
        ones untouched. Returns the number purged."""
        days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web_notification.retention_days", 365)
        )
        if days <= 0:
            return 0
        cutoff = fields.Datetime.now() - timedelta(days=days)
        stale = self.sudo().search(
            [
                ("state", "=", "done"),
                ("done_at", "<", cutoff),
            ]
        )
        count = len(stale)
        stale.unlink()
        return count

    def _ensure_owner(self):
        if any(notif.user_id.id != self.env.uid for notif in self):
            raise AccessError(
                self.env._("You cannot act on notifications addressed to another user.")
            )

    def action_mark_seen(self):
        self._ensure_owner()
        pending = self.filtered(lambda notif: notif.state == "pending")
        pending.sudo().write(
            {
                "state": "done",
                "done_at": fields.Datetime.now(),
                "snooze_until": False,
            }
        )
        return True

    def action_reactivate(self):
        """Bring a snoozed or seen notification back to active (pending, now)."""
        self._ensure_owner()
        try:
            with self.env.cr.savepoint():
                self.sudo().write(
                    {"state": "pending", "snooze_until": False, "done_at": False}
                )
        except IntegrityError as error:
            if error.pgcode != errorcodes.UNIQUE_VIOLATION:
                raise
            raise UserError(
                self.env._("There is already an active notification for this event.")
            ) from error
        return True

    def action_snooze(self, snooze_until):
        self.ensure_one()
        self._ensure_owner()
        if self.state != "pending":
            raise UserError(self.env._("Only pending notifications can be snoozed."))
        snooze_until = fields.Date.to_date(snooze_until)
        if not snooze_until or snooze_until <= fields.Date.context_today(self):
            raise UserError(self.env._("The snooze date must be in the future."))
        self.sudo().write({"snooze_until": snooze_until})
        return True

    def action_open_snooze_wizard(self):
        self.ensure_one()
        self._ensure_owner()
        if self.state != "pending":
            raise UserError(self.env._("Only pending notifications can be snoozed."))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Snooze notification"),
            "res_model": "web.notification.snooze.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_notification_id": self.id},
        }

    def action_open_origin(self):
        self.ensure_one()
        self._ensure_owner()
        if self.res_model not in self._allowed_origin_models():
            raise UserError(self.env._("The linked record is no longer available."))
        model = self.env.get(self.res_model)
        if model is None:
            raise UserError(self.env._("The linked record is no longer available."))
        record = model.browse(self.res_id)
        if not record.exists():
            raise UserError(self.env._("The linked record is no longer available."))
        try:
            record.check_access("read")
        except AccessError as error:
            raise UserError(
                self.env._("You are not allowed to open the linked record.")
            ) from error
        return record.get_formview_action()
