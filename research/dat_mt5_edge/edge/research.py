"""Reproducible chronological experiment and conservative promotion gates."""
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
from .core import CsvBars,Spec,run,metrics,validate_bars
from .strategies import STRATEGIES

FOLDS=[('IS_2017', '2017-01-01','2018-01-01'),
       ('OOS_2018_H1','2018-01-01','2018-07-01'),
       ('OOS_2018_H2','2018-07-01','2019-01-01')]

def dt(s):return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

def experiment(path,spec):
    bars=CsvBars(path).bars();results=[];ledger=[]
    for cls in STRATEGIES:
        folds=[];oos=[];ins=[]
        for label,a,b in FOLDS:
            trades,stats=run(bars,cls(),spec,start=dt(a),end=dt(b))
            stress_trades,stress=run(bars,cls(),spec,stress=2.,start=dt(a),end=dt(b))
            for t in trades:
                t.fold=label;t.regime='2017_bull' if label.startswith('IS') else '2018_bear'
                ledger.append(dict(strategy=cls.name,**asdict(t)))
            (ins if label.startswith('IS') else oos).extend(trades)
            sessions={s:metrics([t for t in trades if t.session==s]) for s in sorted({t.session for t in trades})}
            folds.append(dict(fold=label,start=a,end_exclusive=b,stats=stats,
                              doubled_cost_stats=stress,by_session=sessions))
        im=metrics(ins);om=metrics(oos)
        reasons=[]
        coverage=len([b for b in bars if dt('2018-01-01')<=b.time<dt('2019-01-01')])/(365*48)
        if coverage<.99:reasons.append('OOS_BAR_COVERAGE_LT_99_PERCENT')
        if not spec.execution_verified:reasons.append('UNVERIFIED_EXECUTABLE_PRICES_AND_CONTRACT')
        if len(oos)<100:reasons.append('OOS_SAMPLE_LT_100')
        if len({t.entry_time[:10] for t in oos})<60:reasons.append('OOS_ACTIVE_DAYS_LT_60')
        if om['average_r'] is None or om['average_r']<=0:reasons.append('NONPOSITIVE_OOS_EXPECTANCY')
        if not om['mean_r_ci95'] or om['mean_r_ci95'][0]<=0:reasons.append('OOS_DESCRIPTIVE_CI_INCLUDES_ZERO')
        if any(f['stats']['trades']<30 or f['stats']['net_pnl']<=0 or f['doubled_cost_stats']['net_pnl']<=0 for f in folds[1:]):
            reasons.append('UNSTABLE_OR_INSUFFICIENT_OOS_FOLDS')
        if any(f['stats']['max_drawdown_fraction']>.10 for f in folds[1:]):reasons.append('OOS_DRAWDOWN_GT_10_PERCENT')
        degradation=im['average_r']-om['average_r'] if im['average_r'] is not None and om['average_r'] is not None else None
        results.append(dict(strategy=cls.name,in_sample=im,out_of_sample=om,
                            oos_degradation_r=degradation,oos_bar_coverage=coverage,max_oos_fold_drawdown=max(f['stats']['max_drawdown_fraction'] for f in folds[1:]),decision='REJECT' if reasons else 'RESEARCH_REVIEW_ONLY',
                            rejection_reasons=reasons,folds=folds))
    return dict(protocol='phase1-fixed-v1',symbol=spec.symbol,venue=spec.venue,
                data_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),quality=validate_bars(bars),
                specification=asdict(spec),results=results,trade_ledger=ledger,
                caveat='Assumed midpoint fills and costs; no verified Vantage execution; no profitability claim.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True)
    p.add_argument('--spec',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();spec=Spec(**json.loads(a.spec.read_text()));spec.validate()
    report=experiment(a.data,spec)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
    for r in report['results']:
        print(r['strategy'],r['decision'],json.dumps(r['out_of_sample'],sort_keys=True))

if __name__=='__main__':main()
