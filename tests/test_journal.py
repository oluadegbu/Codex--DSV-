import sqlite3
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path

from dci.confluence import Confluence
from dci.journal import DurableShadowBook, JournalError
from dci.models import RiskEvidence
from dci.pipeline import run_fixture
from dci.scoring import assess

FIXTURE = Path(__file__).parent / 'fixtures/synthetic.json'


def opportunity():
    c = Confluence(('A', 'B', 'C'), ('a', 'b', 'c'), D('.9'), ('e1', 'e2', 'e3'))
    return assess('T', 1100, c, RiskEvidence('T', 1100, True, True, True, D('.9'), D('.9')), D('.9'), D('.9'))


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'dci.sqlite'

    def tearDown(self):
        self.tmp.cleanup()

    def test_restart_recovers_open_position_and_exits_once(self):
        with DurableShadowBook(self.path) as journal:
            journal.enter(opportunity(), D(1))
        with DurableShadowBook(self.path) as journal:
            self.assertEqual(journal.cash, D(900))
            journal.mark('T', D('1.6'), 1200)
            expected = journal.cash
        with DurableShadowBook(self.path) as journal:
            journal.mark('T', D('1.6'), 1200)
            self.assertEqual(journal.cash, expected)
            self.assertEqual(len(journal.audit), 2)

    def test_entire_fixture_retry_is_idempotent(self):
        a = run_fixture(FIXTURE, self.path)
        b = run_fixture(FIXTURE, self.path)
        self.assertEqual(a, b)
        self.assertEqual(a, run_fixture(FIXTURE))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0], 3)

    def test_conflicting_retry_rejected(self):
        with DurableShadowBook(self.path) as journal:
            journal.enter(opportunity(), D(1))
            with self.assertRaises(JournalError):
                journal.enter(opportunity(), D(2))
            self.assertEqual(journal.cash, D(900))
            self.assertEqual(len(journal.audit), 1)

    def test_invalid_mark_rolls_back(self):
        with DurableShadowBook(self.path) as journal:
            journal.enter(opportunity(), D(1))
            with self.assertRaises(ValueError):
                journal.mark('T', D(0), 1200)
            self.assertEqual(len(journal.audit), 1)
            journal.mark('T', D('1.1'), 1200)
            self.assertEqual(len(journal.audit), 2)

    def test_hash_corruption_fails_closed(self):
        with DurableShadowBook(self.path) as journal:
            journal.enter(opportunity(), D(1))
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE events SET payload='{}' WHERE seq=1")
        with self.assertRaises(JournalError):
            DurableShadowBook(self.path)

    def test_unrelated_database_is_not_reused(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE unrelated (id INTEGER)')
        with self.assertRaises(JournalError):
            DurableShadowBook(self.path)

    def test_unknown_schema_rejected(self):
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA user_version=99')
        with self.assertRaises(JournalError):
            DurableShadowBook(self.path)

    def test_process_exit_after_commit_recovers(self):
        # Child exits without graceful journal.close(); committed state must survive.
        code = '''import os,sys
from dci.pipeline import run_fixture
run_fixture(sys.argv[1], sys.argv[2])
os._exit(0)
'''
        result = subprocess.run([sys.executable, '-c', code, str(FIXTURE), str(self.path)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(run_fixture(FIXTURE, self.path), run_fixture(FIXTURE))

    def test_two_connections_share_idempotency_boundary(self):
        with DurableShadowBook(self.path) as first, DurableShadowBook(self.path) as second:
            first.enter(opportunity(), D(1))
            second.enter(opportunity(), D(1))
            self.assertEqual(first.cash, D(900))
            self.assertEqual(len(second.audit), 1)


if __name__ == '__main__':
    unittest.main()
