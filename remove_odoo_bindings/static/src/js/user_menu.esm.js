// Explicit edge: load the core items module first so its registrations exist
import "@web/webclient/user_menu/user_menu_items";
import {registry} from "@web/core/registry";

// 19.0: the user menu is built from the "user_menuitems" registry, not from the
// pre-OWL `UserMenu.Actions` template that the old `t-extend` / `t-jquery`
// override targeted (that mechanism was dropped in 15.0 and silently did nothing).
//
// This module depends on `web`, whose assets register these items, so this file
// is loaded afterwards and the removals win.
//
// Of the three entries the 14.0 version removed, only two still exist: the
// odoo.com account link and the support link. There is no longer a
// "documentation" item in the user menu.
const userMenu = registry.category("user_menuitems");

userMenu.remove("odoo_account");
userMenu.remove("support");
