"""Reproducible Phase 4 inventory/certification. Offline; no strategy execution."""
import gzip,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from phase2.model import load
from .certify import certify,sha,validate_quotes
from .recover import recover
ROOT=Path(__file__).resolve().parents[1]
ASOF=int(datetime(2026,10,18,tzinfo=timezone.utc).timestamp())

def run(root=ROOT):
    lock=json.loads((root/'phase4/baseline_lock.json').read_text())
    for name,expected in lock.items():
        if sha((root/name).read_bytes())!=expected:raise ValueError('immutable baseline drift: '+name)
    recovered=recover(root/'phase4')
    (root/'phase4/results/recovery.json').write_text(json.dumps(recovered,sort_keys=True,indent=2)+'\n')
    registry=json.loads((root/'phase4/reviewed_bundles.json').read_text())['bundle_sha256']
    inventory={}
    for symbol in ('EURUSD','GBPUSD','XAUUSD'):
        path=root/f'phase2/work/data/{symbol}_1m.csv.gz';raw=gzip.decompress(path.read_bytes());bars,digest=load(path)
        # These metadata are explicitly unverified pilot assumptions. Missing proofs
        # and calendar cannot be replaced by invented verified=true flags.
        manifest={'data_sha256':digest,'contract':{'symbol':symbol,'tick_size':'0.00001' if symbol!='XAUUSD' else '0.001','digits':5 if symbol!='XAUUSD' else 3},
                  'previously_evaluated_intervals':[[1514764800,1546300800]]}
        inventory[symbol]=certify(manifest,raw,b'[]',{},registry,ASOF)
        inventory[symbol]['available_rows']=len(bars)
        try:inventory[symbol]['structural_diagnostics']=validate_quotes(raw,manifest['contract']['tick_size'],manifest['contract']['digits'])[0]
        except ValueError as exc:inventory[symbol]['structural_diagnostics']={'failure':str(exc)}
    raw=(root/'phase4/work/recovered_EURUSD_1m.csv').read_bytes()
    inventory['EURUSD_RECOVERED_2022']=certify({'data_sha256':sha(raw),'contract':{},'previously_evaluated_intervals':[]},raw,b'[]',{},registry,ASOF)
    btc=root/'data/BTCUSD_30m.csv'
    source=json.loads((root/'data/source_manifest.json').read_text())
    if sha(btc.read_bytes())!=source['normalized_sha256']:raise ValueError('BTC proxy drift')
    inventory['BTCUSD']={'status':'QUARANTINED_TRADE_CANDLE_PROXY','sha256':sha(btc.read_bytes()),'research_ready':False,'blockers':['NO_BID_ASK','PREVIOUSLY_EVALUATED_2017_2018','STALE_HISTORY','UNVERIFIED_EXECUTABLE_COSTS']}
    for symbol in ('USDJPY','ES','MES','NQ','MNQ','YM','MYM'):
        inventory[symbol]={'status':'NO_QUALIFIED_EXPORT','research_ready':False,'blockers':['NO_CERTIFIED_CONTRACT_AWARE_QUOTES']}
    result={'protocol':'PHASE4_OFFLINE_REVIEW_V1','baseline_files_verified':len(lock),'baseline_unchanged':True,
            'inventory':inventory,'certified_instruments':[],'new_edge_backtests':0,'ranked_candidates':[],
            'broker_connections':0,'broker_mutations':0,'collector':'PASSIVE_BYTES_CONSUMER_ONLY'}
    (root/'phase4/results/readiness.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result

if __name__=='__main__':print(json.dumps(run(),sort_keys=True))
