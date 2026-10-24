"""Fixed-grid pilot; no optimization or OOS-selected forward candidate."""
import argparse,gzip,hashlib,json,statistics
from dataclasses import asdict
from datetime import datetime,timezone
from pathlib import Path
from .model import load,quality,aggregate,SPECS,FUTURES,NY
from .strategies import variants,signals,Variant
from .engine import simulate,metrics,block_ci

def epoch(s):return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())
PERIODS=[('IS_JAN','2018-01-01','2018-02-01'),('WF1_APR','2018-04-01','2018-05-01'),('WF2_JUL','2018-07-01','2018-08-01')]

def coverage(bars):
    # Research windows 00:00–12:00 NY weekdays, excluding all unobserved dates/months.
    present={b.t for b in bars};count=expected=0
    for _,a,z in PERIODS:
        for t in range(epoch(a),epoch(z),60):
            ny=datetime.fromtimestamp(t,timezone.utc).astimezone(NY)
            if ny.weekday()<5 and 0<=ny.hour<12:
                expected+=1;count+=t in present
    return dict(observed=count,expected=expected,ratio=count/expected)

def run(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report=dict(protocol='PHASE2_FIXED_PILOT_V1',instruments={},futures={k:dict(status='BLOCKED_NO_CONTRACT_HISTORY',point_value=v[0],tick=v[1],contract_verified=False)for k,v in FUTURES.items()},trials=[])
    manifest=json.loads((root/'mirror_manifest.json').read_text())
    report['source_pins']=manifest['pins'];report['primary_crossverified']=manifest['primary_crossverified'];report['primary_crosscheck']=manifest.get('primary_crosscheck',{})
    ledger=[]
    lock=json.loads(Path(__file__).with_name('source_lock.json').read_text())
    report['source_failures']=sum('error'in x for x in manifest['sources'])
    report['source_files']=len(manifest['sources'])
    report['archive_inventory']=manifest.get('archive_inventory',{})
    for sym,spec in SPECS.items():
        bars,sha=load(root/f'{sym}_1m.csv.gz');assert sha==manifest['instruments'][sym]['sha256']
        qual=quality(bars);cov=coverage(bars);report['instruments'][sym]=dict(quality=qual,coverage=cov,sha256=sha,spec=spec)
        if sha!=lock['normalized'][sym]['sha256']:raise ValueError('unqualified dataset hash')
        q=lock['data_qualification'][sym];report['instruments'][sym]['qualification']=q
        if not q['pilot_price_units_accepted']:
            report['instruments'][sym]['status']='QUARANTINED_NO_PERFORMANCE_INFERENCE'
            continue
        report['instruments'][sym]['status']='PILOT_ONLY_NOT_EXECUTION_VERIFIED'
        grouped={n:aggregate(bars,n)for n in (1,3,5)}
        # No fitted selection: frozen January IS, April forward validation, July holdout.
        slices={name:[b for b in bars if epoch(a)<=b.t<epoch(z)]for name,a,z in PERIODS}
        vv=variants(sym)+[Variant('baseline',5)]+[Variant('random',5,mode=str(seed))for seed in range(10)]
        for n,v in enumerate(vv):
            intents=signals(grouped[v.timeframe],v,bars,seed=int(v.mode)if v.family=='random'else None)
            folds=[];oos=[];ins=[]
            for label,a,z in PERIODS:
                selected=[s for s in intents if epoch(a)<=s.ready<epoch(z)]
                tr,extra=simulate(slices[label],selected,spec);m=metrics(tr);m.update(extra)
                stress,sextra=simulate(slices[label],selected,spec,cost_factor=2);m2=metrics(stress);m2.update(sextra)
                sens=[]
                for rr in (1.5,2.5):
                    ts,_=simulate(slices[label],selected,spec,rr=rr);sens.append(dict(rr=rr,**metrics(ts)))
                folds.append(dict(period=label,base=m,double_cost=m2,target_sensitivity=sens))
                (ins if label.startswith('IS')else oos).extend(tr)
                for t in tr:ledger.append(dict(symbol=sym,variant=v.key,period=label,**asdict(t)))
            reasons=[];om=metrics(oos);im=metrics(ins);ci=block_ci(oos)
            if cov['ratio']<.99:reasons.append('INCOMPLETE_SESSION_COVERAGE')
            if not manifest['primary_crossverified']:reasons.append('PRIMARY_TIMEZONE_PROVENANCE_NOT_CROSSVERIFIED')
            if not spec['verified']:reasons.append('UNVERIFIED_ACCOUNT_COSTS_AND_CONTRACT')
            if len(oos)<100 or om['active_days']<60:reasons.append('INSUFFICIENT_OOS_SAMPLE')
            if any(f['base']['trades']<30 or (f['base']['average_r']or 0)<=0 or (f['double_cost']['average_r']or 0)<=0 for f in folds[1:]):reasons.append('UNSTABLE_FORWARD_FOLDS')
            if not ci or ci[0]<=0:reasons.append('NO_POSITIVE_BLOCK_CI')
            if om['unobserved_gap_exits']:reasons.append('UNOBSERVED_EXIT_PATH')
            dd=max(f['base']['max_drawdown']for f in folds[1:])
            frequency=len(oos)/(len(slices['WF1_APR'])+len(slices['WF2_JUL']))*1440 if oos else 0
            if dd>.10:reasons.append('DRAWDOWN_LIMIT')
            report['trials'].append(dict(symbol=sym,variant=asdict(v),key=v.key,in_sample=im,oos=om,folds=folds,block_ci=ci,max_oos_fold_drawdown=dd,
                                         trades_per_observed_24h=frequency,average_r_degradation=(im['average_r']-om['average_r'])if im['average_r']is not None and om['average_r']is not None else None,
                                         decision='REJECT'if reasons else'RESEARCH_REVIEW_ONLY',reasons=reasons))
            if (n+1)%20==0:print(sym,n+1,'/',len(vv),flush=True)
    # Eligibility before expectancy: noneligible variants have no edge rank.
    eligible=[t for t in report['trials']if not t['reasons']and t['variant']['family']not in ('baseline','random')]
    eligible.sort(key=lambda t:(t['oos']['average_r'],-t['max_oos_fold_drawdown']),reverse=True)
    report['eligible_rankings']=[dict(rank=i+1,symbol=t['symbol'],key=t['key'])for i,t in enumerate(eligible)]
    report['strongest_forward_shadow_candidates']=[] # Never promote from pilot/OOS inspection.
    blob=json.dumps(ledger,sort_keys=True,separators=(',',':')).encode();(out/'trades.json.gz').write_bytes(gzip.compress(blob,mtime=0))
    report['ledger_sha256']=hashlib.sha256(blob).hexdigest();report['ledger_rows']=len(ledger)
    (out/'phase2.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',newline='\n')
    print(json.dumps(dict(trials=len(report['trials']),ledger_rows=len(ledger),eligible=len(eligible))),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.data,a.output)
