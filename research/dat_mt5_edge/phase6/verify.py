"""Check preservation only. No installer, license acceptance or broker access."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(root=ROOT):
    lock=json.loads((root/'phase6/baseline_lock.json').read_text())
    for path,expected in lock.items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=expected:raise ValueError('baseline drift: '+path)
    observed=json.loads((root/'phase6/OBSERVATIONS.json').read_text())
    assert observed['new_tickstory_exports']==0 and not observed['official_source']['terms_accepted']
    result={'phase':'6','decision':observed['decision'],'baseline_files_verified_unchanged':len(lock),
            'tickstory_installed':False,'new_exports':0,'certification':'NOT_EVALUATED_NO_EXPORT',
            'new_strategy_backtests':0,'spending_usd':0,'broker_orders':0,
            'prior_test_evidence':'84 tests recorded in Phase 5; not rerun in Phase 6'}
    (root/'phase6/results/verification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result

if __name__=='__main__':print(json.dumps(run(),sort_keys=True))
