import {registry} from "@web/core/registry";

// mail contributes four entries to the top bar. This module depends on mail, so
// its assets load afterwards and these removals win.
//
// The pre-OWL `<t t-extend>` / `t-jquery` template used until 14.0 no longer has
// any effect: these are built from registries, not from templates.
//
// Note: only the *menu items* are removed. mail's "im_status" entry in the
// `services` registry is left alone -- that service backs the presence feature
// and other code depends on it.
const systray = registry.category("systray");

systray.remove("mail.messaging_menu");
systray.remove("mail.activity_menu");
systray.remove("discuss.CallMenu");

// The presence dropdown ("Online" / "Away" / "Busy" / "Offline") is registered as
// a user-menu item, even though it renders in the same top-right area.
registry.category("user_menuitems").remove("im_status");
