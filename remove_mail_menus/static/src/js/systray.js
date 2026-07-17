import { registry } from "@web/core/registry";

// mail registers its systray items ("mail.messaging_menu", sequence 25 and
// "mail.activity_menu", sequence 20) from its own assets. This module depends on
// mail, so its assets are loaded afterwards and these removals win.
//
// The pre-OWL `<t t-extend>` / `t-jquery` template used until 14.0 no longer has
// any effect: the systray is built from this registry, not from a template.
const systray = registry.category("systray");

systray.remove("mail.messaging_menu");
systray.remove("mail.activity_menu");
