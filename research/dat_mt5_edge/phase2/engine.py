"""Offline paired-quote execution, time-bounded trades, conservative bar ambiguity."""
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import math,statistics,random
from .model import NY
@dataclass
class Trade:
    entry:int;exit:int;side:int;quantity:float;entry_price:float;exit_price:float
    pnl:float;r:float;mae_r:float;mfe_r:float;costs:float;reason:str;label:str

def simulate(bars,intents,spec,cost_factor=1.,rr=2.,max_hold=90):
    if cost_factor<1 or rr<=0 or max_hold<=0:raise ValueError('invalid scenario')
    events={x.ready:x for x in intents};cash=100000.;peak=cash;dd=0.;pos=None;trades=[];denied=0;last=None
    def fee(px,q):return px*q*spec['point_value']*spec['commission_bps']*cost_factor/10000
    def fill(b,side,entering,trigger=None):
        # Side-aware real quote OHLC; stress widens spread around the midpoint.
        buy=side>0 if entering else side<0
        quote=(b.ao if buy else b.bo) if trigger is None else trigger
        spread=b.ao-b.bo
        quote+=(1 if buy else -1)*(spec['slip']*cost_factor+spread*(cost_factor-1)/2)
        tick=spec['tick'];return (math.ceil(quote/tick-1e-8) if buy else math.floor(quote/tick+1e-8))*tick
    def close(b,trigger,reason):
        nonlocal cash,pos
        p=pos;px=fill(b,p['side'],False,trigger);f=fee(px,p['q'])
        pnl=p['side']*(px-p['px'])*p['q']*spec['point_value']-p['fee']-f
        cash+=pnl+p['fee']
        excursion=p['side']*(px-p['px'])*p['q']*spec['point_value']
        p['mae']=max(p['mae'],-excursion,0.);p['mfe']=max(p['mfe'],excursion,0.)
        # Commission + measured entry spread + entry/exit assumed slip; exit bid/ask
        # cost cannot be independently separated at an intrabar trigger timestamp.
        cost=p['fee']+f+(p['spread']+(b.ao-b.bo)*cost_factor)*p['q']*spec['point_value']/2+2*spec['slip']*cost_factor*p['q']*spec['point_value']
        trades.append(Trade(p['entry'],b.t,p['side'],p['q'],p['px'],px,pnl,pnl/p['risk'],p['mae']/p['risk'],p['mfe']/p['risk'],cost,reason,p['label']))
        pos=None
    for b in bars:
        ny=datetime.fromtimestamp(b.t,timezone.utc).astimezone(NY)
        gap=last is not None and b.t-last!=60;last=b.t
        if pos and gap:close(b,None,'UNOBSERVED_GAP')
        if pos and (ny.hour>=16 or b.t-pos['entry']>=max_hold*60):close(b,None,'TIME_EXIT')
        intent=events.get(b.t)
        if intent and (not intent.expires or b.t<intent.expires) and pos is None and not gap and b.volume>0 and ny.weekday()<5 and 2<=ny.hour<12:
            s=intent.side;px=fill(b,s,True);stop=intent.stop
            # Stops/targets trigger on bid for longs, ask for shorts.
            distance=s*(px-stop)
            expected_stop=fill(b,s,False,stop)
            risk_per=s*(px-expected_stop)*spec['point_value']+fee(px,1)+fee(expected_stop,1)
            q=math.floor(min(cash*.0025/max(risk_per,1e-12),cash*spec['leverage']/(px*spec['point_value']),spec['maxqty'])/spec['step'])*spec['step']
            if distance<=spec['tick'] or q<spec['minqty'] or cash<=0:denied+=1
            else:
                f=fee(px,q);cash-=f
                pos=dict(side=s,px=px,stop=stop,target=px+s*rr*distance,q=q,fee=f,risk=q*risk_per,entry=b.t,
                         spread=(b.ao-b.bo)*cost_factor,mae=0.,mfe=0.,label=intent.label)
        if pos:
            p=pos;s=p['side'];o,h,l=(b.bo,b.bh,b.bl)if s>0 else(b.ao,b.ah,b.al)
            stop=l<=p['stop']if s>0 else h>=p['stop'];target=h>=p['target']if s>0 else l<=p['target']
            worst=min(o,p['stop']) if s>0 and o<p['stop'] else max(o,p['stop']) if s<0 and o>p['stop'] else max(l,p['stop']) if s>0 else min(h,p['stop'])
            # MAE/MFE are conservative minute-bar bounds, not exact tick-order claims.
            adverse=max(0,-s*(worst-p['px']))*p['q']*spec['point_value']
            favorable=max(0,s*((o if stop else min(h,p['target']) if s>0 else max(l,p['target']))-p['px']))*p['q']*spec['point_value']
            p['mae']=max(p['mae'],adverse);p['mfe']=max(p['mfe'],favorable)
            mark=cash+s*(worst-p['px'])*p['q']*spec['point_value']-fee(worst,p['q'])
            dd=max(dd,(peak-mark)/peak)
            if stop:close(b,min(o,p['stop'])if s>0 else max(o,p['stop']),'STOP')
            elif target:close(b,p['target'],'TARGET')
        mark=cash
        if pos:
            p=pos;mark+=p['side']*((b.bc if p['side']>0 else b.ac)-p['px'])*p['q']*spec['point_value']
            mark-=fee(b.bc if p['side']>0 else b.ac,p['q'])
        peak=max(peak,mark);dd=max(dd,(peak-mark)/peak)
    if pos:close(bars[-1],bars[-1].bc if pos['side']>0 else bars[-1].ac,'SAMPLE_END')
    dd=max(dd,(peak-cash)/peak)
    return trades,dict(max_drawdown=dd,denied=denied,net_pnl=cash-100000)

def metrics(trades):
    n=len(trades);rs=[t.r for t in trades];pnl=[t.pnl for t in trades]
    gain=sum(x for x in pnl if x>0);loss=-sum(x for x in pnl if x<0)
    return dict(trades=n,win_rate=sum(x>0 for x in pnl)/n if n else None,average_r=statistics.mean(rs)if n else None,
                expectancy_usd=statistics.mean(pnl)if n else None,profit_factor=gain/loss if loss else None,
                pnl=sum(pnl),costs=sum(t.costs for t in trades),mae_r=statistics.mean(t.mae_r for t in trades)if n else None,
                mfe_r=statistics.mean(t.mfe_r for t in trades)if n else None,
                active_days=len({t.entry//86400 for t in trades}),long_trades=sum(t.side>0 for t in trades),short_trades=sum(t.side<0 for t in trades),
                unobserved_gap_exits=sum(t.reason=='UNOBSERVED_GAP'for t in trades))

def block_ci(trades,seed=491,replicates=300):
    """Bootstrap daily blocks; descriptive only, not multiple-testing adjusted."""
    days={}
    for t in trades:days.setdefault(t.entry//86400,[]).append(t.r)
    if len(days)<20:return None
    blocks=list(days.values());rng=random.Random(seed);means=[]
    for _ in range(replicates):
        rs=[r for _ in blocks for r in rng.choice(blocks)];means.append(statistics.mean(rs))
    means.sort();return [means[int(.025*replicates)],means[int(.975*replicates)]]
