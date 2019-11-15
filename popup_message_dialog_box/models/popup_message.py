from odoo import fields, models


class PopupMessage(models.TransientModel):
    _name = 'popup.message'

    def _default_name(self):
        if self.env.context.get('message', False):
            return self.env.context.get('message')
        return False

    name = fields.Text(string='Message', readonly=True, default=_default_name)
