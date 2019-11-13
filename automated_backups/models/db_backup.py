# 2004-2009 Tiny SPRL (<http://tiny.be>).
# 2015 Agile Business Group <http://www.agilebg.com>
# 2016 Grupo ESOC Ingenieria de Servicios, S.L.U. - Jairo Llopis
# 2017 Tribunal Municipal de Cuentas de Rosario - Lisandro Gallo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import os
import shutil
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from glob import iglob

from odoo import models, fields, api, _, tools, exceptions
from odoo.service import db

_LOGGER = logging.getLogger(__name__)


class DbBackup(models.Model):

    _name = 'db.backup'

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Cannot duplicate a configuration'),
        ('days_to_keep_positive', 'CHECK(days_to_keep >= 0)',
         'Cannot remove backups from recurrence future'),
    ]

    _intervals_ = [('hourly', 'Hourly'), ('daily', 'Daily'),
                   ('monthly', 'Monthly')]

    def _default_folder(self):
        return os.path.join(tools.config["data_dir"], "backups",
                            self.env.cr.dbname)

    name = fields.Char(required=True)

    folder = fields.Char(default=_default_folder, required=True)

    days_to_keep = fields.Integer(
        default=0,
        required=True,
    )

    recurrence = fields.Selection(selection=_intervals_, required=True)

    @api.constrains('folder')
    def _check_folder(self):
        for rec in self:
            if rec.folder.startswith(tools.config.filestore(
                    self.env.cr.dbname)):
                raise exceptions.ValidationError(
                    _('Do not save backups on your filestore, or you will '
                      'backup your backups too!'))

    def action_backup(self):
        backup = None
        filename = self.filename(datetime.now())
        successful = self.browse()

        for rec in self:
            with rec.backup_log():
                # Directory must exist
                try:
                    if not os.path.isdir(rec.folder):
                        os.makedirs(rec.folder)
                except ValueError as err:
                    _LOGGER.exception('%s', err)
                    raise exceptions.ValidationError(
                        _('Backup directory must be set!'))
                except OSError as err:
                    _LOGGER.exception('%s', err)

                with open(os.path.join(rec.folder, filename), 'wb') as destiny:
                    # Copy the cached backup
                    if backup:
                        with open(backup) as cached:
                            shutil.copyfileobj(cached, destiny)
                    # Generate new backup
                    else:
                        try:
                            db.dump_db(self.env.cr.dbname, destiny)
                            backup = backup or destiny.name
                        except IOError as err:
                            _LOGGER.exception('%s', err)
                successful |= rec

        # Remove old files for successful backups
        successful.cleanup_old_backups()

    def action_backup_all(self, interval=None):
        if interval == 'days':
            return self.search([('recurrence', '=', 'daily')]).action_backup()
        elif interval == 'hours':
            return self.search([('recurrence', '=', 'hourly')]).action_backup()
        elif interval == 'months':
            return self.search([('recurrence', '=', 'monthly')
                                ]).action_backup()
        else:
            raise exceptions.ValidationError(_('Wrong backup interval'))

    @contextmanager
    def backup_log(self):
        try:
            _LOGGER.info('Starting database backup: %s', self.name)
            yield
        except OSError:
            _LOGGER.exception('Database backup failed: %s', self.name)
        else:
            _LOGGER.info('Database backup succeeded: %s', self.name)

    def cleanup_old_backups(self):
        now = datetime.now()
        for rec in self.filtered('days_to_keep'):
            with rec.cleanup_log():
                oldest = self.filename(now - timedelta(days=rec.days_to_keep))
                for name in iglob(os.path.join(rec.folder, '*.zip')):
                    if os.path.basename(name) < oldest:
                        os.unlink(name)

    @contextmanager
    def cleanup_log(self):
        self.ensure_one()
        try:
            _LOGGER.info('Starting cleanup process after database backup: %s',
                         self.name)
            yield
        except OSError:
            _LOGGER.exception('Cleanup of old database backups failed: %s')
        else:
            _LOGGER.info('Cleanup of old database backups succeeded: %s',
                         self.name)

    @api.model
    def filename(self, when):
        return "{:%Y_%m_%d_%H_%M_%S}_%s_%s.zip".format(when) % (
            self.env.cr.dbname, self.recurrence)
