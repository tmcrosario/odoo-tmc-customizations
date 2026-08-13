from odoo import fields, models


# Kept in models/ to avoid a risky directory move mid-migration
class PopupMessage(models.TransientModel):  # pylint: disable=no-wizard-in-models
    _name = "popup.message"
    _description = "Popup Message"

    def _default_message(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    def _default_is_html(self):
        return self.env.context.get("is_html", False)

    plain_text_message = fields.Text(
        readonly=True, default=lambda self: self._default_message()
    )

    html_message = fields.Html(
        string="HTML Message",
        readonly=True,
        default=lambda self: self._default_message(),
    )

    is_html = fields.Boolean(
        readonly=True, default=lambda self: self._default_is_html()
    )
