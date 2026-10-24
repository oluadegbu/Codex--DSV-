"""Reproducible offline certification; never starts a terminal or reads market data."""
import hashlib
from dataclasses import asdict
import importlib
import io
import json
from pathlib import Path
import platform
import unittest

from phase7.simulator import Policy, fixture_contract, canonical

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class Result(unittest.TextTestResult):
    def __init__(self, *args):
        super().__init__(*args)
        self.passed = []

    def addSuccess(self, test):
        self.passed.append(test.id())
        super().addSuccess(test)


def run():
    lock = json.loads((HERE/'baseline_git_lock.json').read_text())
    repository = ROOT.parents[1]
    for path, expected in lock['blobs'].items():
        raw = (repository/path).read_bytes()  # public repository artifacts only
        actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual != expected:
            raise ValueError('prior public artifact changed: '+path)
    suite = unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module('phase7.test_simulator'))
    suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests_phase6_2')))
    runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0, resultclass=Result)
    result = runner.run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise ValueError('offline certification failed: '+str(result.testsRun)+' tests; '+runner.stream.getvalue())
    dependencies = ['phase7/simulator.py','phase7/test_simulator.py','phase7/certify.py',
                    'phase4/collector.py','phase6_2/readiness.py','phase6_2/shadow.py']
    out = {'phase':'7.0','scope':'SYNTHETIC_OFFLINE_CFD_MECHANICS_ONLY',
           'result':'PASS_WITHIN_DECLARED_MODEL','python':platform.python_version(),
           'tests_run':result.testsRun,'tests_passed':len(result.passed),'failed':0,'skipped':0,
           'new_phase7_tests':sum(t.startswith('phase7.') for t in result.passed),
           'reused_phase6_2_tests':sum(not t.startswith('phase7.') for t in result.passed),
           'test_ids':sorted(result.passed), 'baseline_commit':lock['baseline_commit'],
           'prior_public_blobs_unchanged':len(lock['blobs']),
           'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in dependencies},
           'fixture_policy':json.loads(canonical(asdict(Policy()))),
           'fixture_contract':json.loads(canonical(asdict(fixture_contract()))),
           'actual_demo_ready':False,'broker_execution_authority':False,
           'live_trading_authority':False,'mt5_starts':0,'broker_connections':0,
           'real_or_demo_orders':0,'historical_data_or_holdout_used':False,
           'profitability_or_edge_claim':False,'temporal_required':False}
    target=HERE/'results/offline_certification.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    return out


if __name__=='__main__':
    out=run()
    print(json.dumps({k:out[k] for k in ('result','tests_run','new_phase7_tests','reused_phase6_2_tests',
                                       'prior_public_blobs_unchanged','actual_demo_ready')}))
