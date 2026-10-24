"""Offline verification of preserved evidence and transferred sample diagnostics."""
import hashlib,json
from pathlib import Path
from phase4.certify import validate_quotes
ROOT=Path(__file__).resolve().parents[1]

def run(root=ROOT):
    baseline=json.loads((root/'phase5/baseline_lock.json').read_text())
    for p,expected in baseline.items():
        if hashlib.sha256((root/p).read_bytes()).hexdigest()!=expected:raise ValueError('baseline drift: '+p)
    sample=json.loads((root/'phase5/results/free_sample.json').read_text())
    raw=(root/'phase5/work/normalized.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sample['certification']['data_sha256']:raise ValueError('sample drift')
    q,_=validate_quotes(raw,'0.1',1)
    if q!=sample['quality']:raise ValueError('sample diagnostics drift')
    r={'baseline_files_unchanged':len(baseline),'normalized_sample_hash_verified':True,'normalized_sample_quality_verified':True,
       'new_free_quote_rows':sample['raw_quote_rows'],'paired_minutes':q['rows'],'certified_datasets':[],
       'new_strategy_backtests':0,'spending_usd':0,'credential_enrollments':0,'broker_connections':0,
       'decision':'CANARY_ACQUIRED_AND_QUARANTINED; FREE_FIRST_ROUTE_RECOMMENDED'}
    (root/'phase5/results/verification.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
    return r

if __name__=='__main__':print(json.dumps(run(),sort_keys=True))
