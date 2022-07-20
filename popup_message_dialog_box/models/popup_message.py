from odoo import fields, models


class PopupMessage(models.TransientModel):

    _name = "popup.message"
    _description = "Popup Message"

    def _default_message(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    def _default_is_html(self):
        self.env.context.get("is_html", False)
        return self.env.context.get("is_html")

    plain_text_message = fields.Text(
        string="Message", readonly=True, default=_default_message
    )

    html_message = fields.Html(
        string="Message", readonly=True, default=_default_message
    )

    is_html = fields.Boolean(readonly=True, default=_default_is_html)
