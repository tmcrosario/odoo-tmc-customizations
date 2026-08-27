# In-App Notifications (`web_notification`)

A reusable in-app notification engine for Odoo 19 Community: a persistent per-user inbox
(`web.notification`) plus a systray bell with a pending counter. It does **not** depend
on `mail`/`discuss` and has no realtime/email/push. It depends on `tmc` for the
`tmc.system` registry (each notification belongs to a system: GD, SICON, SIGOP, …).

Any internal system can adopt it to notify users about business events.

## Who sees notifications

Recipients are **every internal user** (`base.group_user`), scoped to their own
notifications by a record rule (`user_id = user.id`). There is **no group to manage** —
adopting a system requires no user enrollment. There is no cross-user "see everyone"
role.

## Adopting the engine from another module

### 1. Depend on it

```python
{"depends": ["web_notification", ...]}
```

### 2. Register your origin model(s)

Every origin belongs to a **system** (`tmc.system`) — GD, SICON, SIGOP, …. This module
adds a `color` to `tmc.system`, used to tell notifications apart in the inbox. Systems
usually already exist; reference the right one and ship one origin record per model you
point notifications at:

```xml
<record id="notification_origin_my_model" model="web.notification.origin">
  <field name="model_id" ref="my_module.model_my_model" />
  <field name="system_id" ref="tmc.my_system_xmlid" />
</record>
```

The `res_model`/`res_id` reference is validated against this central allowlist;
scheduling a notification for a model that is not registered raises `ValueError`. A
notification's system is **derived from its origin** — producers never pass it.

### 3. Emit events from your business logic

Call the internal (underscore-prefixed, **not** RPC-exposed) producer API from
server-side Python — a `write`/state transition, an `@api.model` helper, or a cron:

```python
self.env["web.notification"]._schedule_notification(
    res_model="my.model",
    res_id=record.id,
    user_id=recipient.id,          # an internal res.users id
    event_key="my.model.overdue",  # stable technical identity, not translated
    notification_kind="deadline",  # see "Kinds" below
    name=_("Your task is overdue"),  # short, stable, translated summary line
    note=False,                    # optional, minimal detail
    date_deadline=record.date_due, # optional functional deadline
)
```

It is **idempotent**: a repeated logical event
(`res_model + res_id + user_id + notification_kind + event_key`) returns the existing
pending notification instead of creating a duplicate (a partial unique index enforces
this transactionally). A new occurrence after the previous one is resolved creates a
fresh notification.

Auto-resolve when the event no longer needs attention (e.g. on close/cancel), in the
same transaction as the business transition:

```python
self.env["web.notification"]._resolve_pending(
    res_model="my.model",
    res_id=record.id,
    notification_kinds=["deadline"],  # optional filters
    # event_keys=[...], user_id=...,
)
```

Both methods run under `sudo()` (trusted server-side callers); they validate the origin
allowlist and that the recipient is an active internal user.

## Kinds

`notification_kind` is a stable **code** resolved to a `web.notification.kind` record.
The three global base kinds are `overdue`, `deadline`, `assignment` (no system → usable
by any system). Add your own as data records; leave `system_id` empty for a global kind,
or set it to restrict the kind to one system:

```xml
<record id="notification_kind_my_kind" model="web.notification.kind">
  <field name="name">My kind</field>
  <field name="code">my_kind</field>
  <field name="system_id" ref="tmc.my_system_xmlid" />
</record>
```

Scheduling with a system-specific kind whose system does not match the origin's system
raises `ValueError`; an unknown code raises `ValueError`.

## Security / privacy notes

- **`name`/`note` are shown to the recipient verbatim.** Put only information the
  recipient is authorized to see — the engine guards the origin _link_ (leaving it empty
  without read access), not the free text.
- Recipients must be **internal** users; portal/public users are skipped.
- Users can only ever read and act on their own notifications; the mark-seen / snooze /
  open-origin actions validate ownership before any privileged write.

## Retention

Done notifications are purged by a weekly cron once they pass a retention window. The
window is the config parameter `web_notification.retention_days` (default `365`); set it
to `0` to disable purging. Pending notifications are never purged.

## Systray bell — scoped to the current app's system

The bell is **scoped to the system of the app you are in**. Map each system to its Odoo
app via `tmc.system.app_menu_id` (Notifications → Configuration → Systems). Then:

- In an app whose system **manages notifications** (has ≥1 origin): the bell shows and
  its badge counts **your active** pending notifications **for that system**; clicking
  opens the active list filtered to that system.
- If that count is 0: the bell shows with no badge.
- In an app not mapped to a notification-managing system: the bell is **hidden**.

"Active" = pending and not future-snoozed (a snoozed notification counts again once its
snooze date passes). Done notifications never count. The Notifications app's **Active**
menu lists every system's active notifications (unscoped).
