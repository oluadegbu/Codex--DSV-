"""Offline preservation check; no data acquisition or execution authority."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(root=ROOT):
    lock=json.loads((root/'phase6_1/baseline_lock.json').read_text())
    for path,expected in lock.items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=expected:raise ValueError('baseline drift: '+path)
    obs=json.loads((root/'phase6_1/OBSERVATIONS.json').read_text())
    result={'phase':'6.1','baseline_files_unchanged':len(lock),'tickstory':'UNSUITABLE_FOR_THIS_PHASE',
      'directivecodex_session_observed_active':obs['windows_read_only']['session_active'],
      'supported_non_elevated_execution_route':False,'windows_execution':'BLOCKED',
      'new_acquired_datasets':0,'new_certifications':'NOT_EVALUATED_NO_ADMISSIBLE_NEW_DATA',
      'new_strategy_backtests':0,'spending_usd':0,'new_credentials':0,'mt5_starts':0,'broker_orders':0}
    (root/'phase6_1/results/verification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result

if __name__=='__main__':print(json.dumps(run(),sort_keys=True))
