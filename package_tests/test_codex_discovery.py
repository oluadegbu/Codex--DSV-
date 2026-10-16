"""Missing-PATH and fail-closed discovery regression; no Codex launch."""
import hashlib
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from dci.master import windows_codex_locator as locator
from windows_package_runtime import verify_predecessor_unstarted


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.path=self.root/'Programs/OpenAI/Codex/bin/codex.exe';self.path.parent.mkdir(parents=True)
        self.data=b'fixture native file; not an executable';self.path.write_bytes(self.data)
        self.policy=patch.dict(locator.OFFICIAL_CODEX,{'x86_64':(len(self.data),hashlib.sha256(self.data).hexdigest())});self.policy.start()
    def tearDown(self):self.policy.stop();self.temp.cleanup()
    def test_user_local_verified_executable_without_subprocess_path(self):
        def missing():raise AssertionError('PATH must not be queried for existing user-local installation')
        self.assertEqual(locator.discover(self.root,missing,'x86_64'),self.path)
    def test_untrusted_primary_never_falls_back_to_path(self):
        self.path.write_bytes(b'untrusted')
        with self.assertRaises(PermissionError):locator.discover(self.root,lambda:self.path.as_posix(),'x86_64')
    def test_missing_primary_and_missing_path_stays_closed(self):
        self.path.unlink()
        def missing():raise subprocess.CalledProcessError(1,['Get-Command'])
        with self.assertRaises(FileNotFoundError):locator.discover(self.root,missing,'x86_64')
    def test_path_executable_requires_same_official_hash(self):
        self.path.unlink();other=self.root/'other/codex.exe';other.parent.mkdir();other.write_bytes(b'wrong binary')
        with self.assertRaises(PermissionError):locator.discover(self.root,lambda:str(other),'x86_64')


class PredecessorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.dbpath=self.root/'DMB-0.1.1-35291220795c/package/app/artifacts/windows-foreground/controller.sqlite';self.dbpath.parent.mkdir(parents=True)
        db=sqlite3.connect(self.dbpath);db.execute('PRAGMA user_version=101');db.execute('CREATE TABLE tasks(id,state,attempts,lease)');db.execute("INSERT INTO tasks VALUES ('windows-shadow-001','QUEUED',0,NULL)")
        for t in ('executions','win_offers','master_locks','win_identity'):db.execute('CREATE TABLE '+t+' (entry)')
        db.commit();db.close()
    def tearDown(self):self.temp.cleanup()
    def test_proven_prestart_retains_exact_database_bytes(self):
        before=self.dbpath.read_bytes();report=verify_predecessor_unstarted(self.root)
        self.assertEqual(report['status'],'PROVEN_BEFORE_DISPATCH');self.assertEqual(self.dbpath.read_bytes(),before)
    def test_started_or_uncertain_predecessor_cannot_be_routed_around(self):
        db=sqlite3.connect(self.dbpath);db.execute("UPDATE tasks SET state='NEEDS_HUMAN',attempts=1");db.commit();db.close()
        with self.assertRaises(PermissionError):verify_predecessor_unstarted(self.root)
    def test_v012_journal_blocks_new_version_even_when_v011_is_unstarted(self):
        journal=self.root/'DMBWindowsWorker-v1-0.1.2/state/bridge.sqlite'
        journal.parent.mkdir(parents=True);journal.write_bytes(b'preserve unknown outcome')
        with self.assertRaises(PermissionError):verify_predecessor_unstarted(self.root)

    def test_wal_or_worker_journal_blocks_replacement(self):
        Path(str(self.dbpath)+'-wal').write_bytes(b'unknown uncheckpointed outcome')
        with self.assertRaises(PermissionError):verify_predecessor_unstarted(self.root)
        Path(str(self.dbpath)+'-wal').unlink();worker=self.root/'DMBWindowsWorker-v1/state/bridge.sqlite';worker.parent.mkdir(parents=True);worker.write_bytes(b'preserve')
        with self.assertRaises(PermissionError):verify_predecessor_unstarted(self.root)


if __name__=='__main__':unittest.main()
