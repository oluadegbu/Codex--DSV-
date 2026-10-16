"""Fixed, causal operational definitions; no parameter search or centered pivots."""
from collections import deque
from datetime import timedelta
from zoneinfo import ZoneInfo
from .core import Signal

class Candidate:
    def __init__(self):
        self.history=deque(maxlen=100);self.day=None;self.state=None;self.ema=None;self.last=None
        self.asia=[];self.opening=None

    def prepare(self,b,zone):
        if self.last and b.time-self.last!=timedelta(minutes=30):
            self.history.clear();self.state=None;self.ema=None;self.asia=[];self.opening=None
        self.last=b.time
        local=b.time.astimezone(ZoneInfo(zone))
        if local.date()!=self.day:
            self.day=local.date();self.state=None;self.asia=[];self.opening=None
        body=sum(abs(x.close-x.open) for x in list(self.history)[-20:])/min(20,len(self.history)) if self.history else 0
        self.ema=b.close if self.ema is None else self.ema+2/21*(b.close-self.ema)
        return local,body

    def finish(self,b,signal=None):
        self.history.append(b)
        return signal

class LondonSweep(Candidate):
    name='A_london_asia_sweep'
    def observe(self,b):
        local,body=self.prepare(b,'Europe/London');hour=local.hour+local.minute/60
        if local.weekday()>=5:return self.finish(b)
        if hour<7:self.asia.append(b)
        # Require all 14 bars of local midnight-to-07:00 range; DST transition days fail closed.
        if not 7<=hour<10 or len(self.asia)!=14:return self.finish(b)
        hi=max(x.high for x in self.asia);lo=min(x.low for x in self.asia)
        if self.state:
            side,extreme,boundary,age=self.state
            if age>=4:self.state=None;return self.finish(b)
            self.state=(side,max(extreme,b.high) if side<0 else min(extreme,b.low),boundary,age+1)
            displacement=abs(b.close-b.open)>1.2*body and (b.close<b.open if side<0 else b.close>b.open)
            if displacement and (b.close<boundary if side<0 else b.close>boundary):
                stop=self.state[1];self.state=None
                return self.finish(b,Signal(side,stop,'London','sweep_then_opposing_displacement'))
        elif b.high>hi and b.close<hi:
            self.state=(-1,b.high,b.low,0)
        elif b.low<lo and b.close>lo:
            self.state=(1,b.low,b.high,0)
        return self.finish(b)

class NewYorkORB(Candidate):
    name='B_ny_orb_retest'
    def observe(self,b):
        local,_=self.prepare(b,'America/New_York');minute=local.hour*60+local.minute
        if local.weekday()>=5:return self.finish(b)
        if minute==570:self.opening=(b.high,b.low)
        if not self.opening or not 600<=minute<720:return self.finish(b)
        hi,lo=self.opening
        if self.state:
            side,age=self.state
            if age>=4:self.state=None;return self.finish(b)
            self.state=(side,age+1)
            if side>0 and b.low<=hi and b.close>hi:
                self.state=None;return self.finish(b,Signal(1,lo,'New_York','orb_retest_continuation'))
            if side<0 and b.high>=lo and b.close<lo:
                self.state=None;return self.finish(b,Signal(-1,hi,'New_York','orb_retest_continuation'))
        elif b.close>hi:self.state=(1,0)
        elif b.close<lo:self.state=(-1,0)
        return self.finish(b)

class SweepMSSFVG(Candidate):
    name='C_external_sweep_mss_retest'
    def observe(self,b):
        local,body=self.prepare(b,'America/New_York');hist=list(self.history)
        if local.weekday()>=5:return self.finish(b)
        if len(hist)<48 or not 7<=local.hour<16:return self.finish(b)
        hi=max(x.high for x in hist[-48:]);lo=min(x.low for x in hist[-48:])
        if self.state:
            st=self.state;st['age']+=1
            if st['age']>8:self.state=None;return self.finish(b)
            side=st['side']
            if st['stage']=='sweep':
                st['extreme']=min(st['extreme'],b.low) if side>0 else max(st['extreme'],b.high)
                shift=b.close>st['structure'] if side>0 else b.close<st['structure']
                if shift and abs(b.close-b.open)>1.2*body:
                    # FVG only known when this third candle closes. Retest must be later.
                    zone=(hist[-2].high,b.low) if side>0 else (b.high,hist[-2].low)
                    st.update(stage='retest',zone=zone if zone[0]<zone[1] else None,age=0)
            else:
                zone=st['zone'];fvg=zone is not None and b.low<=zone[1] and b.high>=zone[0]
                ema=b.low<=self.ema<=b.high
                direction=b.close>b.open if side>0 else b.close<b.open
                if (fvg or ema) and direction:
                    self.state=None
                    return self.finish(b,Signal(side,st['extreme'],'New_York','external_sweep_mss_fvg_or_ema'))
        elif b.low<lo and b.close>lo:
            self.state=dict(side=1,extreme=b.low,structure=max(x.high for x in hist[-6:]),stage='sweep',age=0)
        elif b.high>hi and b.close<hi:
            self.state=dict(side=-1,extreme=b.high,structure=min(x.low for x in hist[-6:]),stage='sweep',age=0)
        return self.finish(b)

STRATEGIES=[LondonSweep,NewYorkORB,SweepMSSFVG]
