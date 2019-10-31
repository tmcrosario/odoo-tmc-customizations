from odoo import models, fields


class Task(models.Model):
    _name = "project.task"
    _inherit = 'project.task'

    reviewer_id = fields.Many2one(comodel_name='res.users', string='Reviewer')
