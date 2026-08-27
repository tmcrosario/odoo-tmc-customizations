import {ListController} from "@web/views/list/list_controller";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

export class NotificationListController extends ListController {
    async afterExecuteActionButton(clickParams) {
        await super.afterExecuteActionButton(clickParams);
        // Keep the systray bell count in sync after seen/snooze.
        this.env.bus.trigger("web_notification.refresh");
    }
}

registry.category("views").add("web_notification_list", {
    ...listView,
    Controller: NotificationListController,
});
