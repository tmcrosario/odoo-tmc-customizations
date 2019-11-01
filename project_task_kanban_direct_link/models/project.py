from odoo import models, api

_EMPTY_HTML = ['<p><br></p>', '<p>\xa0<br></p>']


class Task(models.Model):
    _name = "project.task"
    _inherit = 'project.task'

    @api.onchange('description')
    def _onchange_description(self):
        for task in self:
            if task.description in _EMPTY_HTML:
                task.description = None
