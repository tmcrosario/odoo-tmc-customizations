# © 2004-2009 Tiny SPRL (<http://tiny.be>).
# © 2015 Agile Business Group <http://www.agilebg.com>
# © 2016 Grupo ESOC Ingeniería de Servicios, S.L.U. - Jairo Llopis
# © 2017 Tribunal Municipal de Cuentas de Rosario - Lisandro Gallo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import os
import shutil
from contextlib import contextmanager
from datetime import datetime, timedelta
from glob import iglob
from odoo import exceptions, models, fields, api, _, tools
from odoo.service import db
import logging

_logger = logging.getLogger(__name__)


class DB_Backup(models.Model):

    _name = 'db.backup'

    _sql_constraints = [
        (
            'name_unique',
            'UNIQUE(name)',
            'Cannot duplicate a configuration'
        ),
        (
            'days_to_keep_positive',
            'CHECK(days_to_keep >= 0)',
            'Cannot remove backups from recurrence future'
        ),
    ]

    _intervals_ = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('monthly', 'Monthly')
    ]

    name = fields.Char(
        required=True
    )

    folder = fields.Char()

    days_to_keep = fields.Integer(
        default=0,
        required=True,
    )

    recurrence = fields.Selection(
        selection=_intervals_,
        required=True
    )

    @api.multi
    @api.constrains('folder')
    def _check_folder(self):
        for s in self:
            if s.folder.startswith(tools.config.filestore(self.env.cr.dbname)):
                raise exceptions.ValidationError(
                    _('Do not save backups on your filestore, or you will '
                      'backup your backups too!'))

    @api.multi
    def action_backup(self):
        backup = None
        filename = self.filename(datetime.now())
        successful = self.browse()

        for rec in self:
            with rec.backup_log():
                # Directory must exist
                try:
                    os.makedirs(rec.folder)
                except OSError:
                    pass

                with open(os.path.join(rec.folder, filename),
                          'wb') as destiny:
                    # Copy the cached backup
                    if backup:
                        with open(backup) as cached:
                            shutil.copyfileobj(cached, destiny)
                    # Generate new backup
                    else:
                        db.dump_db(self.env.cr.dbname, destiny)
                        backup = backup or destiny.name
                successful |= rec

        # Remove old files for successful backups
        successful.cleanup_old_backups()

    @api.model
    def action_backup_all(self, interval=None):
        if interval == 'days':
            return self.search([
                ('recurrence', '=', 'daily')]).action_backup()
        elif interval == 'hours':
            return self.search([
                ('recurrence', '=', 'hourly')]).action_backup()
        elif interval == 'months':
            return self.search([
                ('recurrence', '=', 'monthly')]).action_backup()
        else:
            raise exceptions.ValidationError(
                _('Wrong backup interval'))

    @api.multi
    @contextmanager
    def backup_log(self):
        try:
            _logger.info(
                'Starting database backup: %s',
                self.name
            )
            yield
        except Exception:
            _logger.exception(
                'Database backup failed: %s',
                self.name
            )
        else:
            _logger.info(
                'Database backup succeeded: %s',
                self.name
            )

    @api.multi
    def cleanup_old_backups(self):
        now = datetime.now()
        for rec in self.filtered('days_to_keep'):
            with rec.cleanup_log():
                oldest = self.filename(now - timedelta(days=rec.days_to_keep))
                for name in iglob(os.path.join(rec.folder, '*.zip')):
                    if os.path.basename(name) < oldest:
                        os.unlink(name)

    @api.multi
    @contextmanager
    def cleanup_log(self):
        self.ensure_one()
        try:
            _logger.info(
                'Starting cleanup process after database backup: %s',
                self.name
            )
            yield
        except Exception:
            _logger.exception('Cleanup of old database backups failed: %s')
        else:
            _logger.info(
                'Cleanup of old database backups succeeded: %s',
                self.name
            )

    @api.model
    def filename(self, when):
        return "{:%Y_%m_%d_%H_%M_%S}_%s_%s.zip".format(when) % (
            self.env.cr.dbname,
            self.recurrence)
