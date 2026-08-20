import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {FormController} from "@web/views/form/form_controller";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

// Discard first, then super, so core sees no pending changes to auto-save.
patch(FormController.prototype, {
    _wcfbConfirmDiscard() {
        return new Promise((resolve) => {
            let confirmed = false;
            this.dialogService.add(
                ConfirmationDialog,
                {
                    title: _t("Unsaved changes"),
                    body: _t(
                        "This record has unsaved changes that will be discarded. Do you want to proceed?"
                    ),
                    confirmLabel: _t("Discard changes"),
                    cancelLabel: _t("Keep editing"),
                    confirm: () => {
                        confirmed = true;
                    },
                    cancel: () => {
                        confirmed = false;
                    },
                },
                {onClose: () => resolve(confirmed)}
            );
        });
    },

    async beforeLeave(options = {}) {
        if (this.model.root.dirty && !options.forceLeave) {
            if (!(await this._wcfbConfirmDiscard())) {
                return false;
            }
            await this.model.root.discard();
        }
        return super.beforeLeave(options);
    },

    async onPagerUpdate(params) {
        if (await this.model.root.isDirty()) {
            if (!(await this._wcfbConfirmDiscard())) {
                return undefined;
            }
            await this.model.root.discard();
        }
        return super.onPagerUpdate(params);
    },

    async create() {
        if (await this.model.root.isDirty()) {
            if (!(await this._wcfbConfirmDiscard())) {
                return undefined;
            }
            await this.model.root.discard();
        }
        return super.create();
    },
});
