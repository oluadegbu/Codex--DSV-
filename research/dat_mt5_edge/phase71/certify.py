"""Offline tests and source preservation only. No MT5 compilation or connection."""
import hashlib
import importlib
import io
import json
from pathlib import Path
import platform
import unittest

from phase71.preflight import collector_source_audit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def run():
    lock=json.loads((HERE/'baseline_git_lock.json').read_text())
    repo=ROOT.parents[1]
    for path,sha in lock['blobs'].items():
        raw=(repo/path).read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual!=sha:raise ValueError('prior public artifact changed: '+path)
    suite=unittest.TestSuite()
    for module in ('phase71.test_preflight','phase7.test_simulator'):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(module)))
    suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests_phase6_2')))
    class Result(unittest.TextTestResult):
        def __init__(self,*args):super().__init__(*args);self.passed=[]
        def addSuccess(self,test):self.passed.append(test.id());super().addSuccess(test)
    runner=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0,resultclass=Result)
    result=runner.run(suite)
    if not result.wasSuccessful() or result.skipped:raise ValueError(runner.stream.getvalue())
    audit=collector_source_audit((HERE/'ReadOnlyDemoPreflight.mq5').read_text())
    files=('preflight.py','ReadOnlyDemoPreflight.mq5','test_preflight.py','certify.py')
    out={'phase':'7.1','scope':'OFFLINE_SNAPSHOT_AND_SOURCE_CALL_SURFACE_ONLY',
         'python':platform.python_version(),'tests_run':result.testsRun,
         'phase71_tests':sum(x.startswith('phase71.') for x in result.passed),
         'phase70_and_reused_regressions':sum(not x.startswith('phase71.') for x in result.passed),
         'failed':0,'skipped':0,'passed_test_ids':sorted(result.passed),
         'prior_public_blobs_unchanged':len(lock['blobs']),'baseline_commit':lock['baseline_commit'],
         'collector_source_audit':audit,
         'source_sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in files},
         'designated_server':'VantageMarkets-Demo','actual_account_allowlist':'EMPTY',
         'operational_gate_a':'NO_GO_PENDING_PRIVATE_TARGET_BUILD_AND_APPROVAL',
         'actual_identity_isolation_investor_access_verified':False,
         'native_compilation_or_terminal_execution':'NOT_RUN',
         'broker_orders_or_mutations':0,'broker_connections':0,'mt5_starts':0,
         'credentials_accessed':False,'gate_b_authorized':False,'shadow':'OFF','holdout_accessed':False}
    path=HERE/'results/offline_verification.json';path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    return out


if __name__=='__main__':
    r=run();print(json.dumps({k:r[k] for k in ('tests_run','phase71_tests','phase70_and_reused_regressions',
                                              'prior_public_blobs_unchanged','operational_gate_a')}))
