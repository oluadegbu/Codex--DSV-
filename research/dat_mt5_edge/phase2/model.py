"""Paired BID/ASK offline model. All times are UTC bar-open Unix seconds."""
from dataclasses import dataclass,asdict
from collections import defaultdict
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import csv,gzip,hashlib,json,math
from pathlib import Path
UTC=timezone.utc;NY=ZoneInfo('America/New_York');LONDON=ZoneInfo('Europe/London')
@dataclass(frozen=True)
class QuoteBar:
    t:int
    bo:float;bh:float;bl:float;bc:float
    ao:float;ah:float;al:float;ac:float
    volume:float
    minutes:int=1
    @property
    def o(self):return (self.bo+self.ao)/2
    @property
    def h(self):return (self.bh+self.ah)/2
    @property
    def l(self):return (self.bl+self.al)/2
    @property
    def c(self):return (self.bc+self.ac)/2
    @property
    def end(self):return self.t+self.minutes*60

SPECS={
 'EURUSD':dict(tick=.00001,step=1000.,minqty=1000.,maxqty=1000000.,slip=.00001,commission_bps=.35,leverage=10.,point_value=1.,verified=False),
 'GBPUSD':dict(tick=.00001,step=1000.,minqty=1000.,maxqty=1000000.,slip=.00001,commission_bps=.35,leverage=10.,point_value=1.,verified=False),
 'XAUUSD':dict(tick=.001,step=1.,minqty=1.,maxqty=1000.,slip=.05,commission_bps=.35,leverage=2.,point_value=1.,verified=False),
}
# Reference identities only: these do not authorize a data substitution or broker trade.
FUTURES={'ES':(50,.25),'MES':(5,.25),'NQ':(20,.25),'MNQ':(2,.25),'YM':(5,1),'MYM':(.5,1)}

def load(path):
    raw=gzip.decompress(Path(path).read_bytes());out=[]
    for r in csv.DictReader(raw.decode().splitlines()):
        out.append(QuoteBar(int(r['timestamp']),*[float(r[k]) for k in ('bid_open','bid_high','bid_low','bid_close','ask_open','ask_high','ask_low','ask_close','volume')]))
    quality(out)
    return out,hashlib.sha256(raw).hexdigest()

def quality(bars):
    if not bars:raise ValueError('empty data')
    gaps=0;spreads=[];zero=0;last=None
    for b in bars:
        if b.minutes not in (1,3,5,15,60) or b.t%(b.minutes*60):raise ValueError('unaligned time')
        if last is not None:
            if b.t<=last:raise ValueError('nonmonotonic')
            gaps+=max(0,(b.t-last)//(b.minutes*60)-1)
        last=b.t
        if not all(math.isfinite(v) for v in (b.bo,b.bh,b.bl,b.bc,b.ao,b.ah,b.al,b.ac,b.volume)):raise ValueError('nonfinite quote')
        for o,h,l,c in [(b.bo,b.bh,b.bl,b.bc),(b.ao,b.ah,b.al,b.ac)]:
            if not 0<l<=min(o,c)<=max(o,c)<=h:raise ValueError('invalid quote OHLC')
        if b.ao<b.bo or b.ac<b.bc or b.volume<0:raise ValueError('crossed or negative volume')
        spreads.extend([b.ao-b.bo,b.ac-b.bc]);zero+=b.volume==0
    spreads.sort()
    return dict(rows=len(bars),first=bars[0].t,last=bars[-1].t,missing_wall_clock_minutes=gaps*bars[0].minutes,
                zero_volume=zero,median_spread=spreads[len(spreads)//2],p95_spread=spreads[int(.95*(len(spreads)-1))])

def aggregate(bars,minutes):
    if minutes==1:return bars
    buckets=defaultdict(list)
    for b in bars:buckets[b.t//(minutes*60)].append(b)
    out=[]
    for k,rs in sorted(buckets.items()):
        if len(rs)!=minutes or [b.t for b in rs]!=list(range(k*minutes*60,(k+1)*minutes*60,60)):continue
        out.append(QuoteBar(rs[0].t,rs[0].bo,max(b.bh for b in rs),min(b.bl for b in rs),rs[-1].bc,
                            rs[0].ao,max(b.ah for b in rs),min(b.al for b in rs),rs[-1].ac,sum(b.volume for b in rs),minutes))
    return out

def clocks(b):
    t=datetime.fromtimestamp(b.t,UTC);ny=t.astimezone(NY);ld=t.astimezone(LONDON)
    return t,ny,ld

def context(bars,minutes):
    """Context keyed by close timestamp; lookup must be <= decision timestamp."""
    return {b.end:(1 if b.c>b.o else -1 if b.c<b.o else 0) for b in aggregate(bars,minutes)}
