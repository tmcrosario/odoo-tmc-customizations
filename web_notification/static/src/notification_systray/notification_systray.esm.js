import {
    Component,
    markup,
    onMounted,
    onWillStart,
    onWillUnmount,
    useState,
} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

const REFRESH_INTERVAL = 60000;

export class NotificationBell extends Component {
    static template = "web_notification.NotificationBell";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.menu = useService("menu");
        this.title = _t("Notifications");
        this.state = useState({visible: false, count: 0});
        this._systemId = false;
        this._seq = 0;
        this._onFocus = () => this._refresh();
        this._onVisibility = () => {
            if (!document.hidden) {
                this._refresh();
            }
        };
        this._onAppChanged = () => this._refresh();
        this._onBusRefresh = () => this._refresh();

        onWillStart(() => this._refresh());
        onMounted(() => {
            this._interval = window.setInterval(
                () => this._refresh(),
                REFRESH_INTERVAL
            );
            window.addEventListener("focus", this._onFocus);
            document.addEventListener("visibilitychange", this._onVisibility);
            this.env.bus.addEventListener("MENUS:APP-CHANGED", this._onAppChanged);
            this.env.bus.addEventListener(
                "web_notification.refresh",
                this._onBusRefresh
            );
        });
        onWillUnmount(() => {
            window.clearInterval(this._interval);
            window.removeEventListener("focus", this._onFocus);
            document.removeEventListener("visibilitychange", this._onVisibility);
            this.env.bus.removeEventListener("MENUS:APP-CHANGED", this._onAppChanged);
            this.env.bus.removeEventListener(
                "web_notification.refresh",
                this._onBusRefresh
            );
        });
    }

    get _currentAppMenuId() {
        const app = this.menu.getCurrentApp();
        return app ? app.id : false;
    }

    async _refresh() {
        // A newer call (e.g. an app switch) supersedes an in-flight one via the token.
        const seq = ++this._seq;
        const appMenuId = this._currentAppMenuId;
        try {
            const data = await this.orm.call(
                "web.notification",
                "notification_systray_data",
                [appMenuId]
            );
            if (seq === this._seq) {
                this._systemId = data.system_id;
                this.state.visible = Boolean(data.system_id);
                this.state.count = data.count;
            }
        } catch {
            // Keep the last valid state.
        }
    }

    async onClick() {
        if (!this._systemId) {
            return;
        }
        const action = await this.orm.call(
            "web.notification",
            "notification_systray_action",
            [this._systemId]
        );
        if (action.help) {
            // A dict action bypasses the action service's markup wrap.
            action.help = markup(action.help);
        }
        await this.action.doAction(action);
        this._refresh();
    }
}

registry
    .category("systray")
    .add(
        "web_notification.NotificationBell",
        {Component: NotificationBell},
        {sequence: 25}
    );
