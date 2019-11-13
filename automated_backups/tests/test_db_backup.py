from odoo.tests import common


class TestDbBackup(common.TransactionCase):
    def setUp(self):
        super(TestDbBackup, self).setUp()
        self.db_backup = self.env['db.backup']

        self.db_daily = self.db_backup.create(
            dict(name='test_daily', recurrence='daily', days_to_keep=30))

        self.db_monthly = self.db_backup.create(
            dict(name='test_monthly', recurrence='monthly', days_to_keep=365))

        self.db_hourly = self.db_backup.create(
            dict(name='test_hourly', recurrence='hourly', days_to_keep=1))

    def test_action_backup_all(self):
        self.assertTrue(self.db_daily.action_backup_all(interval='days'))
        self.assertTrue(self.db_monthly.action_backup_all(interval='months'))
        self.assertTrue(self.db_hourly.action_backup_all(interval='hours'))
