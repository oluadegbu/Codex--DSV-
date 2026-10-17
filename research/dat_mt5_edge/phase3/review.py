"""Revalidate frozen pilot bytes and publish certification decisions, not new edge tests.
Run from research/dat_mt5_edge: python -m phase3.review
"""
import csv,gzip,hashlib,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from phase2.model import load,quality
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_RUN='7e60b6d5456783f3d74abd593ea29c5330998cd88848b75d814387f91ec3c181'

def digest(data):return hashlib.sha256(data).hexdigest()

def blockers(symbol,quality_record):
    reasons=['PRIMARY_QUOTES_NOT_CROSSVERIFIED','UTC_CONVERSION_CHAIN_UNPROVEN',
             'NO_RECENT_HISTORY','COSTS_AND_UNITS_NOT_CERTIFIED',
             'SESSION_CALENDAR_AND_GAP_REMEDIATION_INCOMPLETE']
    if symbol=='XAUUSD':reasons+=['PRICE_SCALE_UNRESOLVED','VANTAGE_MAPPING_UNVERIFIED']
    return reasons

def eligible(data_certified,n,days,ci_lower,stress_expectancy,positive_folds):
    # Necessary conditions only; multiple-testing and economic comparison still required.
    return (data_certified and n>=100 and days>=60 and ci_lower>0
            and stress_expectancy>0 and positive_folds>=2)

def session(timestamp):
    d=datetime.fromtimestamp(timestamp,timezone.utc).astimezone(ZoneInfo('America/New_York'))
    m=d.hour*60+d.minute
    for lo,hi,label in [(120,300,'02-05'),(300,360,'05-06'),(360,480,'06-08'),(480,570,'08-09:30'),(570,660,'09:30-11')]:
        if lo<=m<hi:return label
    return 'other'

def run(root=ROOT):
    frozen=(root/'phase2/results/phase2.json').read_bytes()
    if digest(frozen)!=EXPECTED_RUN:raise ValueError('frozen pilot report drift')
    p=json.loads(frozen);inventory={}
    for symbol,record in p['instruments'].items():
        bars,sha=load(root/f'phase2/work/data/{symbol}_1m.csv.gz')
        if sha!=record['sha256']:raise ValueError('normalized data drift: '+symbol)
        q=quality(bars)
        if q!=record['quality']:raise ValueError('quality mismatch')
        inventory[symbol]={'normalized_sha256':sha,'quality':q,'pilot_session_coverage':record['coverage'],
                           'certified':False,'blockers':blockers(symbol,q)}
    ledger_raw=gzip.decompress((root/'phase2/work/risk_corrected/trades.json.gz').read_bytes())
    if digest(ledger_raw)!=p['ledger_sha256']:raise ValueError('ledger drift')
    ledger=json.loads(ledger_raw)
    if len(ledger)!=p['ledger_rows']:raise ValueError('ledger count mismatch')
    out=root/'phase3/results';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for trial in p['trials']:
        v=trial['variant'];o=trial['oos']
        row={'instrument':trial['symbol'],'strategy':v['family'],'timeframe':v['timeframe'],'variant':trial['key'],
             'evidence':'CARRIED_FORWARD_UNCERTIFIED_2018_PILOT','decision':'REJECT',**o,
             'trades_per_observed_24h':trial['trades_per_observed_24h'],
             'max_oos_fold_drawdown':trial['max_oos_fold_drawdown'],
             'oos_degradation_R':trial['average_r_degradation'],
             'block_ci_lower':(trial['block_ci'] or [None,None])[0],'block_ci_upper':(trial['block_ci'] or [None,None])[1],
             'fold_details':json.dumps(trial['folds'],sort_keys=True,separators=(',',':')),
             'reasons':';'.join(trial['reasons'])}
        rows.append(row)
    write_csv(out/'pilot_variant_metrics.csv',rows)
    groups=defaultdict(list)
    for t in ledger:
        if t['period']=='IS_JAN':continue
        groups[(t['symbol'],t['variant'],t['side'],session(t['entry']))].append(t)
    subsets=[]
    for (symbol,variant,side,sess),ts in sorted(groups.items()):
        pos=sum(max(0,t['pnl']) for t in ts);neg=-sum(min(0,t['pnl']) for t in ts)
        subsets.append(dict(instrument=symbol,variant=variant,direction='long' if side==1 else 'short',
          ny_session=sess,trades=len(ts),win_rate=sum(t['pnl']>0 for t in ts)/len(ts),
          expectancy_R=sum(t['r'] for t in ts)/len(ts),profit_factor=pos/neg if neg else None,
          mae_R=sum(t['mae_r'] for t in ts)/len(ts),mfe_R=sum(t['mfe_r'] for t in ts)/len(ts),
          costs=sum(t['costs'] for t in ts),evidence='UNCERTIFIED_PILOT_SUBSET'))
    write_csv(out/'pilot_direction_session_metrics.csv',subsets)
    result={'protocol':'PHASE3_CERTIFICATION_REVIEW_V1','review_date':'2026-10-16',
            'frozen_phase2_sha256':digest(frozen),'ledger_sha256':digest(ledger_raw),
            'inventory':inventory,'certified_instruments':[],'qualified_rankings':[],
            'new_edge_backtests':0,'pilot_trials_revalidated':len(rows),
            'pilot_ledger_rows_verified':len(ledger),'decision':'NONE',
            'reason':'No certified data; frozen pilot also fails sample and stability gates.'}
    (out/'certification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)

if __name__=='__main__':print(json.dumps(run(),sort_keys=True))
