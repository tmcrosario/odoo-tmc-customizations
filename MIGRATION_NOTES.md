# Migration Notes — odoo-tmc-customizations (14.0 → 19.0)

Repo contains four modules: `automated_backups`, `popup_message_dialog_box`,
`remove_mail_menus`, `remove_odoo_bindings`.

## Summary of changes by category

### Models

- `automated_backups/models/db_backup.py`: no API changes required. Already uses the
  modern `self.env.cr.dbname` (not `self._cr`), `self.env.context`, `@api.constrains`,
  and `odoo.exceptions`. `_sql_constraints` left as-is (still supported in 19.0 — spec
  says do not convert without cause). The `@api.model def filename` helper is a read
  helper, not a `create` override, so no `model_create_multi` change applies.
- `popup_message_dialog_box/models/popup_message.py`: no changes. Already uses
  `self.env.context` and modern `fields.*` defaults. No `name_get` / `@api.one|multi` /
  `read_group` / `track_visibility`.
- `remove_mail_menus` / `remove_odoo_bindings`: no Python models.

### Views

- `automated_backups/views/db_backup_views.xml`: `<tree string="Backups">…</tree>` →
  `<list string="Backups">…</list>` (17.0 tag rename) and the view record's
  `<field name="type">tree</field>` → `list`. Record xmlid `db_backup_view_tree` kept
  unchanged (only the tag/type content changed). The `db_backup_action_form` act_window
  has no `view_mode` key, so nothing to convert there.
- `popup_message_dialog_box/views/popup_message_views.xml`: converted two deprecated
  `attrs` (removed in 17.0) — see "attrs conversions to review".
- No `<tree>` / `t-esc` / `tree_view_ref` / `oe_chatter` / `states=` elsewhere.

### Security

- No `security/` directory in any module. No `res.groups` / `groups_id` records, no
  `ir.model.access.csv`. Nothing to migrate.

### Tests

- `automated_backups/tests/test_db_backup.py`: no changes. Uses no `@common.at_install`
  / `@common.post_install` decorators. `create(dict(...))` calls are single-record dict
  creates, which remain valid input to `create` in 19.0 (only model-side `create`
  _overrides_ needed the `model_create_multi` change, and there is none here). Imports
  cleanly; not executed this round.

### Manifests

- `automated_backups`: version → `19.0.1.0.0`; `depends [] → ["base"]` (the module
  defines a model, cron, menus under `base.menu_automation`, and a server action —
  `base` was an implicit dependency); removed the `# yapf: disable` trailing comment.
  License already `AGPL-3`; `installable` already `True`.
- `popup_message_dialog_box`: version → `19.0.1.0.0`; `depends [] → ["base"]` (defines a
  TransientModel + form view). License already `AGPL-3`.
- `remove_mail_menus`: version → `19.0.1.0.0`. Removed the obsolete `qweb` manifest key
  (dropped in 15.0) and moved `static/src/xml/systray.xml` to the new
  `assets: {"web.assets_backend": [...]}` key. `depends ["mail"]` kept. License
  `AGPL-3`.
- `remove_odoo_bindings`: version → `19.0.1.0.0`. Removed the obsolete `qweb` key and
  moved `static/src/xml/base.xml` to the `assets` key; added explicit `depends ["base"]`
  (it only re-parents `base.*` menus and had no `depends` at all). License `AGPL-3`.

## 18.0 branch

- None existed. Branches present were `10.0`, `13.0`, `14.0`. Branch `19.0` created
  fresh from `14.0`.

## Removed dependencies

- None removed.

## Dependencies to verify before push

- `mail` (remove_mail_menus) — Odoo core module; verify the `mail.menu_root_discuss`
  menu xmlid and the `mail.systray.MessagingMenu` / `mail.systray.ActivityMenu` OWL
  template names still exist in 19.0 (see human-review note).

## attrs conversions to review

- `popup_message_dialog_box/views/popup_message_views.xml`:
  - `attrs="{'invisible':[('is_html','=', True)]}"` → `invisible="is_html"`
    (single-tuple, equality-to-True on a boolean → truthiness; straightforward).
  - `attrs="{'invisible':[('is_html','=', False)]}"` → `invisible="not is_html"`
    (single-tuple, equality-to-False on a boolean → negated truthiness;
    straightforward). Neither is a compound domain; listed for completeness.

## Autosave / onchange → constrains conversions

- None. No `@api.onchange` methods exist in any module.

## Items left for human review

- `remove_odoo_bindings/static/src/xml/base.xml` uses the legacy pre-OWL QWeb
  inheritance mechanism (`<t t-extend="UserMenu.Actions">` + `<t t-jquery=...>`). That
  mechanism and the `UserMenu.Actions` template were removed when the web client moved
  to OWL (15.0+). The deprecation fix applied here is purely the manifest move from
  `qweb` to the `assets` key; the template body itself almost certainly no longer
  matches any 19.0 template and will not hide the account/documentation/support entries.
  This needs a functional rewrite (the user-menu items are now OWL components) — left
  as-is per the "apply deprecation fixes, do not redesign" instruction. FLAG for human
  rewrite.
- `remove_mail_menus/static/src/xml/systray.xml` overrides `mail.systray.MessagingMenu`
  and `mail.systray.ActivityMenu` via `position="replace"`. These OWL template names may
  have changed in 19.0; verify the names still resolve, otherwise the systray menus will
  not be removed. Manifest-level migration (qweb → assets) was applied; template-name
  correctness FLAGGED for human verification.
- `automated_backups`: `db.dump_db(self.env.cr.dbname, destiny)` and
  `tools.config.filestore(...)` are core service/util calls that can drift between
  versions; not changed (no static deprecation signal), but worth a boot-time check.

## Lint findings

pre-commit ran fully (ruff, ruff-format, prettier with plugin-xml, pylint with optional
checks, pylint-odoo, odoo-pre-commit-hooks). Auto-fixers were applied. Actions taken and
remaining reporter findings:

Fixed during this round (safe, standard modernizations):

- `check-executables-have-shebangs`: the four `remove_odoo_bindings` source files
  (`__manifest__.py`, `__init__.py`, `data/ir_ui_menu.xml`, `static/src/xml/base.xml`)
  carried a stray executable bit in the committed 14.0 tree. Cleared with `chmod -x`.
- ruff `B904` (`automated_backups/models/db_backup.py`): added `... from err` to the
  `ValidationError` raised inside the `except ValueError` block.
- ruff `UP008` (`automated_backups/tests/test_db_backup.py`):
  `super(TestDbBackup, self)` → bare `super()`.

Remaining reporter findings (non-blocking, intentionally NOT changed — pylint-odoo /
odoo-pre-commit-hooks are reporters, not gates):

- `manifest-required-author` (all manifests): the OCA rcfile wants "Odoo Community
  Association (OCA)". These are private TMC modules — expected.
- `missing-readme` (all four modules): no `README.rst`. Private modules; not added.
- `inheritable-method-lambda` (`db_backup.py:40`, `popup_message.py:18/22/25`):
  pylint-odoo prefers `default=lambda self: self._x()` over `default=_x`. Style-only,
  still works; left as-is to keep the migration diff minimal.
- `prefer-env-translation` (`db_backup.py` `_check_folder`, `action_backup`,
  `action_backup_all`): 19.0 prefers `self.env._(...)` over the module-level `_`. Valid
  future cleanup; left as-is (still works).
- `no-wizard-in-models` (`popup_message.py`): the TransientModel lives under `models/`
  rather than `wizard/`. Pre-existing layout; not restructured.
- `unknown-option-value` (`too-complex`, `unnecessary-utf8-coding-comment`) from the
  canonical OCA `.pylintrc` — message names absent from this pylint-odoo version;
  harmless, canonical file kept verbatim.

Note: `ruff`/`prettier`/`xml-check` validate syntax/format only, NOT Odoo runtime API
correctness — real API validation is deferred to the boot/test stage.

## Translations

- Translation regeneration deferred to a later stage. Existing `i18n/es_AR.po` files
  left untouched. </content> </invoke>
