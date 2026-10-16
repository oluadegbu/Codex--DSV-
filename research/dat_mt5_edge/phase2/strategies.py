"""Predeclared variants; generating a signal never reads a future bar."""
from collections import deque
from dataclasses import dataclass,asdict
from datetime import datetime,timezone,time
import bisect,random
from .model import clocks,context
@dataclass(frozen=True)
class Variant:
    family:str
    timeframe:int
    mode:str='confirmation'
    window:str='ny_02_05'
    asia:str='utc_00_06'
    opening:int=480
    acceptance:int=2
    context_minutes:int=60
    displacement:float=1.2
    @property
    def key(self):return '|'.join(str(v) for v in asdict(self).values())

@dataclass(frozen=True)
class Intent:
    ready:int
    side:int
    stop:float
    label:str
    expires:int=0

def variants(symbol):
    out=[]
    asia2='utc_23_06' if symbol=='GBPUSD' else 'ny_18_00' if symbol=='XAUUSD' else 'utc_22_06'
    for tf in (1,3,5):
        for asia in ('utc_00_06',asia2):
            for window in ('ny_02_05','london_open','ny_05_06'):
                for mode in ('early','confirmation'):out.append(Variant('A',tf,mode,window,asia))
        for op in (480,570):
            for accept in (1,2):out.append(Variant('B',tf,opening=op,acceptance=accept))
        for mode in ('reversal','continuation'):
            for ctx in (15,60):out.append(Variant('C',tf,mode,context_minutes=ctx))
    return out

def signals(bars,v,raw,seed=None):
    out=[];hist=deque(maxlen=max(60//v.timeframe,20));state=None;last=None;day=None;asia=[];rng=None;attempted=False;bodyq=deque(maxlen=20)
    ctx=context(raw,v.context_minutes);ct=sorted(ctx)
    # Window ranges are accumulated only from already completed entry bars.
    for b in bars:
        t,ny,ld=clocks(b);minute=ny.hour*60+ny.minute
        if last is not None and b.t-last!=v.timeframe*60:
            hist.clear();state=None;bodyq.clear();asia=[];rng=None
        last=b.t
        if ny.date()!=day:day=ny.date();state=None;attempted=False;rng=None
        mean=sum(bodyq)/len(bodyq) if bodyq else 0
        dis=abs(b.c-b.o)>v.displacement*max(mean,1e-12)
        def emit(side,stop,label):
            nonlocal attempted,state
            cut=300 if v.family=='A' and v.window=='ny_02_05' else 360 if v.family=='A' and v.window=='ny_05_06' else v.opening+75 if v.family=='B' else 660
            local=ld if v.family=='A' and v.window=='london_open' else ny
            if v.family=='A' and v.window=='london_open':cut=600
            expiry=int(datetime.combine(local.date(),time(cut//60,cut%60),local.tzinfo).timestamp())
            if side*(b.c-stop)>0 and b.end<expiry:
                out.append(Intent(b.end,side,stop,label,expiry));attempted=True;state=None
        if v.family=='A':
            # Range date is UTC for UTC definitions, New York for NY definition.
            if v.asia.startswith('utc'):
                range_day=t.date();start=23 if v.asia=='utc_23_06' else 22 if v.asia=='utc_22_06' else 0
                inrange=(t.hour>=start or t.hour<6) if start else t.hour<6
                # Reset at start, not midnight, for cross-midnight ranges.
                if t.hour==start and t.minute==0:asia=[]
                required=(24-start+6 if start else 6)*60//v.timeframe
            else:
                inrange=ny.hour>=18
                if ny.hour==18 and ny.minute==0:asia=[]
                required=6*60//v.timeframe
            if inrange:asia.append(b)
            win=(120<=minute<300) if v.window=='ny_02_05' else (300<=minute<360) if v.window=='ny_05_06' else (7<=ld.hour<10)
            if win and not attempted and ny.weekday()<5 and b.volume>0 and len(asia)==required and hist:
                hi=max(x.h for x in asia);lo=min(x.l for x in asia)
                if state:
                    state['age']+=1;s=state['side'];state['extreme']=min(state['extreme'],b.l) if s>0 else max(state['extreme'],b.h)
                    if state['age']>max(1,15//v.timeframe):state=None
                    elif dis and (b.c>state['boundary'] if s>0 else b.c<state['boundary']):emit(s,state['extreme'],'sweep_displacement_reclaim')
                elif b.l<lo and b.c>lo:
                    if v.mode=='early':emit(1,b.l,'sweep_reclaim_early')
                    else:state=dict(side=1,extreme=b.l,boundary=b.h,age=0)
                elif b.h>hi and b.c<hi:
                    if v.mode=='early':emit(-1,b.h,'sweep_reclaim_early')
                    else:state=dict(side=-1,extreme=b.h,boundary=b.l,age=0)
        elif v.family=='B':
            if v.opening<=minute<v.opening+15:
                if rng is None:rng=[]
                rng.append(b)
            if v.opening+15<=minute<v.opening+75 and ny.weekday()<5 and not attempted and rng and len(rng)==15//v.timeframe and hist and b.volume>0:
                hi=max(x.h for x in rng);lo=min(x.l for x in rng)
                if state:
                    state['age']+=1;s=state['side'];edge=hi if s>0 else lo
                    if state['age']>max(1,20//v.timeframe):state=None
                    elif state['count']<v.acceptance:
                        if (b.c>edge if s>0 else b.c<edge):state['count']+=1
                        else:state=None
                    elif (b.l<=hi and b.c>hi and b.c>b.o) if s>0 else (b.h>=lo and b.c<lo and b.c<b.o):emit(s,lo if s>0 else hi,'accepted_displacement_first_retest')
                elif dis and (b.c>hi or b.c<lo):state=dict(side=1 if b.c>hi else -1,count=1,age=0)
        elif v.family=='C' and len(hist)>=60//v.timeframe and 120<=minute<660 and ny.weekday()<5 and not attempted and b.volume>0:
            hs=list(hist);hi=max(x.h for x in hs[-60//v.timeframe:]);lo=min(x.l for x in hs[-60//v.timeframe:])
            j=bisect.bisect_right(ct,b.end)-1;trend=ctx[ct[j]] if j>=0 and b.end-ct[j]<v.context_minutes*60 else 0
            if state:
                state['age']+=1;s=state['side']
                if state['age']>max(1,20//v.timeframe):state=None
                elif state['stage']=='sweep':
                    state['extreme']=min(state['extreme'],b.l) if s>0 else max(state['extreme'],b.h)
                    if dis and (b.c>state['structure'] if s>0 else b.c<state['structure']):
                        state.update(stage='retest',level=(b.o+b.c)/2,age=0)
                elif b.l<=state['level']<=b.h:
                    # First touch consumes the setup even if its closing direction is invalid.
                    if (b.c>b.o if s>0 else b.c<b.o):emit(s,state['extreme'],'external_sweep_mss_first_retracement')
                    state=None
            elif b.l<lo and b.c>lo:
                s=1
                if trend==(-s if v.mode=='reversal' else s):state=dict(side=s,extreme=b.l,structure=max(x.h for x in hs[-3:]),stage='sweep',age=0)
            elif b.h>hi and b.c<hi:
                s=-1
                if trend==(-s if v.mode=='reversal' else s):state=dict(side=s,extreme=b.h,structure=min(x.l for x in hs[-3:]),stage='sweep',age=0)
        elif v.family in ('baseline','random') and ny.weekday()<5 and hist and minute==(480 if v.family=='baseline' else random.Random((seed or 0)+t.date().toordinal()).randrange(120,660,v.timeframe)):
            side=1 if hist[-1].c>hist[-1].o else -1
            if v.family=='random':side=random.Random((seed or 0)+b.t).choice((-1,1))
            width=max(x.h for x in hist)-min(x.l for x in hist)
            if width>0:emit(side,b.c-side*width,'control')
        hist.append(b);bodyq.append(abs(b.c-b.o))
    return out
