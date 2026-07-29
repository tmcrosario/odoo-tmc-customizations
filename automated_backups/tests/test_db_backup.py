import os
import shutil
import tempfile
from unittest.mock import patch

from odoo.tests import common

from odoo.addons.automated_backups.models import db_backup


class TestDbBackup(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.db_backup = self.env["db.backup"]

        # action_backup_all searches every record, so real ones would be dumped
        self.db_backup.search([]).unlink()

        # Own folder: cleanup_old_backups deletes .zip files where it points
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, True)

        self.db_daily = self.db_backup.create(
            dict(
                name="test_daily",
                recurrence="daily",
                days_to_keep=30,
                folder=self.folder,
            )
        )

        self.db_monthly = self.db_backup.create(
            dict(
                name="test_monthly",
                recurrence="monthly",
                days_to_keep=365,
                folder=self.folder,
            )
        )

        self.db_hourly = self.db_backup.create(
            dict(
                name="test_hourly",
                recurrence="hourly",
                days_to_keep=1,
                folder=self.folder,
            )
        )

    def dumps(self):
        return sorted(
            os.path.join(self.folder, name)
            for name in os.listdir(self.folder)
            if name.endswith(".zip")
        )

    def test_action_backup_all(self):
        self.assertTrue(self.db_daily.action_backup_all(interval="days"))
        self.assertTrue(self.db_monthly.action_backup_all(interval="months"))
        self.assertTrue(self.db_hourly.action_backup_all(interval="hours"))

        dumps = self.dumps()
        self.assertEqual(len(dumps), 3, "expected one dump per recurrence")
        for dump in dumps:
            self.assertTrue(
                os.path.getsize(dump),
                "%s is empty" % os.path.basename(dump),
            )

    def test_shared_folder_keeps_the_dump(self):
        # Records sharing folder and recurrence resolve to a single path, and
        # the second one used to truncate the dump the first had just written
        twin = self.db_backup.create(
            dict(
                name="test_daily_twin",
                recurrence="daily",
                days_to_keep=30,
                folder=self.folder,
            )
        )

        (self.db_daily + twin).action_backup()

        dumps = self.dumps()
        self.assertEqual(len(dumps), 1)
        self.assertTrue(os.path.getsize(dumps[0]), "the twin truncated the dump")

    def test_hourly_cleanup_keeps_other_recurrences(self):
        # Shared folder: the hourly cleanup (keep 1 day) must not delete the
        # daily/monthly dumps, which carry their own longer retention
        dbname = self.env.cr.dbname
        old_daily = os.path.join(
            self.folder, "2000_01_01_00_00_00_%s_daily.zip" % dbname
        )
        old_monthly = os.path.join(
            self.folder, "2000_01_01_00_00_00_%s_monthly.zip" % dbname
        )
        for path in (old_daily, old_monthly):
            with open(path, "wb") as handle:
                handle.write(b"old but good")

        self.db_hourly.cleanup_old_backups()

        self.assertTrue(
            os.path.exists(old_daily), "hourly cleanup deleted the daily dump"
        )
        self.assertTrue(
            os.path.exists(old_monthly), "hourly cleanup deleted the monthly dump"
        )

    def test_failed_dump_does_not_trigger_cleanup(self):
        # A dump that writes nothing must not count as success, or cleanup runs
        # and deletes good older backups on the strength of a failed one
        stale = os.path.join(self.folder, "2000_01_01_00_00_00_db_daily.zip")
        with open(stale, "wb") as handle:
            handle.write(b"old but good")

        with patch.object(db_backup.db, "dump_db", lambda *args, **kwargs: None):
            self.db_daily.action_backup()

        self.assertTrue(os.path.exists(stale), "cleanup deleted a good backup")
