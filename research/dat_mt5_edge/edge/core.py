"""Deterministic offline research. No broker SDK, subprocess, login or order API."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Protocol
import csv
import hashlib
import json
import math
import statistics

UTC = timezone.utc

@dataclass(frozen=True)
class Bar:
    time: datetime  # UTC bar OPEN; OHLC only observable at time + interval
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass(frozen=True)
class Spec:
    symbol: str
    venue: str
    unit_value: float
    quantity_step: float
    min_quantity: float
    max_quantity: float
    tick_size: float
    spread_bps: float
    commission_bps: float  # per side, on notional
    slippage_bps: float  # adverse per side
    max_leverage: float = 1.0
    interval_minutes: int = 30
    short_allowed: bool = False
    execution_verified: bool = False
    risk_fraction: float = 0.0025
    initial_equity: float = 100000.0

    def validate(self):
        numbers = [v for v in asdict(self).values() if isinstance(v, (float, int))]
        if not all(math.isfinite(v) for v in numbers):
            raise ValueError('nonfinite specification')
        if min(self.unit_value, self.quantity_step, self.min_quantity,
               self.max_quantity, self.tick_size, self.max_leverage, self.initial_equity) <= 0:
            raise ValueError('invalid contract specification')
        if self.min_quantity > self.max_quantity or not 0 < self.risk_fraction <= .01:
            raise ValueError('invalid size/risk bounds')
        if min(self.spread_bps, self.commission_bps, self.slippage_bps) < 0:
            raise ValueError('negative transaction cost')
        if self.interval_minutes != 30:
            raise ValueError('initial strategy protocol requires 30m bars')

class ReadOnlyBars(Protocol):
    def bars(self) -> list[Bar]: ...

class CsvBars:
    """File-only market-data interface. MT5 must export separately after approval."""
    def __init__(self, path: Path):
        self.path = path

    def bars(self) -> list[Bar]:
        rows = []
        with self.path.open(newline='') as f:
            for r in csv.DictReader(f):
                t = datetime.fromisoformat(r['timestamp'])
                if t.tzinfo is None:
                    raise ValueError('naive timestamp')
                rows.append(Bar(t.astimezone(UTC), *[float(r[k]) for k in
                            ('open', 'high', 'low', 'close', 'volume')]))
        validate_bars(rows)
        return rows

def validate_bars(bars: list[Bar]) -> dict:
    if not bars:
        raise ValueError('empty data')
    gaps = 0
    for i, b in enumerate(bars):
        if b.time.tzinfo is None or b.time.utcoffset() != timedelta(0):
            raise ValueError('timestamps must be UTC aware')
        if b.time.minute not in (0, 30) or b.time.second or b.time.microsecond:
            raise ValueError('unaligned 30m bar')
        if not all(math.isfinite(v) for v in (b.open,b.high,b.low,b.close,b.volume)):
            raise ValueError('nonfinite bar')
        if not 0 < b.low <= min(b.open,b.close) <= max(b.open,b.close) <= b.high or b.volume < 0:
            raise ValueError('invalid OHLCV')
        if i:
            dt = (b.time-bars[i-1].time).total_seconds()
            if dt <= 0:
                raise ValueError('duplicate or unordered timestamp')
            if dt % 1800:
                raise ValueError('invalid interval')
            gaps += int(dt/1800)-1
    return {'bars':len(bars), 'first':bars[0].time.isoformat(),
            'last':bars[-1].time.isoformat(), 'missing_30m_bars':gaps,
            'sha256_semantic':hashlib.sha256(json.dumps([asdict(b) for b in bars],
                                      default=str,sort_keys=True).encode()).hexdigest()}

@dataclass(frozen=True)
class Signal:
    side: int
    stop: float
    session: str
    reason: str

@dataclass
class Trade:
    entry_time: str
    exit_time: str
    side: int
    quantity: float
    entry: float
    exit: float
    stop: float
    target: float
    pnl: float
    r: float
    costs: float
    session: str
    reason: str
    fold: str = ''
    regime: str = ''


def quote(mid: float, side: int, entering: bool, spec: Spec, stress=1.0) -> float:
    """Midpoint OHLC proxy -> adverse executable-price assumption, rounded outward."""
    direction = side if entering else -side
    bps = (spec.spread_bps/2 + spec.slippage_bps)*stress
    p = mid*(1+direction*bps/10000)
    return (math.ceil(p/spec.tick_size-1e-9) if direction>0 else
            math.floor(p/spec.tick_size+1e-9))*spec.tick_size


def run(bars: list[Bar], strategy, spec: Spec, stress=1.0,
        start: datetime|None=None, end: datetime|None=None) -> tuple[list[Trade],dict]:
    """Closed-bar signals, next-open fills. One position; stops before targets.

    Gaps cancel pending signals; open risk exits at next available open with gap
    slippage. Each calendar session day ends flat. Marks include open P&L.
    """
    spec.validate(); validate_bars(bars)
    cash=spec.initial_equity; peak=cash; dd=0.; pos=None; pending=None
    trades=[]; rejected={'short_not_executable':0,'size_or_stop':0,'gap_signal':0}
    used_days=set()
    def close(b, mid, reason):
        nonlocal cash,pos
        p=pos; exit_px=quote(mid,p['side'],False,spec,stress)
        fee=exit_px*p['q']*spec.unit_value*spec.commission_bps*stress/10000
        gross=p['side']*(exit_px-p['entry'])*p['q']*spec.unit_value
        net=gross-p['fee']-fee;cash+=gross-fee
        cost=((abs(p['entry']-p['mid'])+abs(exit_px-mid))*p['q']*spec.unit_value+p['fee']+fee)
        exit_time=b.time+timedelta(minutes=30) if reason=='SESSION_END' else b.time
        trades.append(Trade(p['time'].isoformat(),exit_time.isoformat(),p['side'],p['q'],
                            p['entry'],exit_px,p['stop'],p['target'],net,net/p['risk'],cost,p['session'],reason))
        pos=None
    for i,b in enumerate(bars):
        active=(start is None or b.time>=start) and (end is None or b.time<end)
        gap=i>0 and b.time-bars[i-1].time!=timedelta(minutes=30)
        if pos and gap: close(b,b.open,'DATA_GAP')
        if pending and gap: rejected['gap_signal']+=1;pending=None
        if pending and active and not pos:
            s=pending;pending=None
            if s.side<0 and not spec.short_allowed:
                rejected['short_not_executable']+=1
            else:
                px=quote(b.open,s.side,True,spec,stress)
                # Stop is a MID trigger; risk includes modeled execution at that stop.
                sp=quote(s.stop,s.side,False,spec,stress)
                per_unit=s.side*(px-sp)*spec.unit_value
                fee_per_unit=(px+sp)*spec.unit_value*spec.commission_bps*stress/10000
                total_risk=per_unit+fee_per_unit
                maxq=min(spec.max_quantity,cash*spec.max_leverage/(px*spec.unit_value))
                q=math.floor(min(cash*spec.risk_fraction/max(total_risk,1e-12),maxq)/spec.quantity_step)*spec.quantity_step
                if s.side*(px-s.stop)<=spec.tick_size or q<spec.min_quantity or cash<=0:
                    rejected['size_or_stop']+=1
                else:
                    fee=px*q*spec.unit_value*spec.commission_bps*stress/10000
                    cash-=fee
                    # Fixed 2R MID target; net R includes all modeled costs.
                    target=b.open+s.side*2*abs(b.open-s.stop)
                    pos=dict(side=s.side,q=q,entry=px,mid=b.open,stop=s.stop,target=target,
                             risk=q*total_risk,fee=fee,time=b.time,session=s.session)
        if pos:
            p=pos;s=p['side']
            # Conservative adverse excursion before a possible exit; gap through stop at open.
            worst=min(b.open,p['stop']) if s>0 and b.open<p['stop'] else (max(b.open,p['stop']) if s<0 and b.open>p['stop'] else (max(b.low,p['stop']) if s>0 else min(b.high,p['stop'])))
            worst_px=quote(worst,s,False,spec,stress)
            worst_equity=cash+s*(worst_px-p['entry'])*p['q']*spec.unit_value-worst_px*p['q']*spec.unit_value*spec.commission_bps*stress/10000
            dd=max(dd,(peak-worst_equity)/peak if peak else 1.)
            stop_hit=b.low<=p['stop'] if s>0 else b.high>=p['stop']
            target_hit=b.high>=p['target'] if s>0 else b.low<=p['target']
            if stop_hit:
                close(b,min(b.open,p['stop']) if s>0 else max(b.open,p['stop']),'STOP')
            elif target_hit: close(b,p['target'],'TARGET')
            else:
                # Exit at this close before missing bars, fold end or UTC day boundary.
                nxt=bars[i+1] if i+1<len(bars) else None
                if nxt is None or (end and nxt.time>=end) or (b.time+timedelta(minutes=30)).date()!=b.time.date():
                    close(b,b.close,'SESSION_END')
        mark=cash
        if pos:
            exit_px=quote(b.close,pos['side'],False,spec,stress)
            mark+=pos['side']*(exit_px-pos['entry'])*pos['q']*spec.unit_value
            mark-=exit_px*pos['q']*spec.unit_value*spec.commission_bps*stress/10000
        peak=max(peak,mark);dd=max(dd,(peak-mark)/peak if peak else 1.)
        # Observe even outside entry interval for causal warmup; no pending carry across fold.
        sig=strategy.observe(b)
        next_t=b.time+timedelta(minutes=30)
        if sig and active and not pos and b.time.date() not in used_days and (end is None or next_t<end):
            pending=sig;used_days.add(b.time.date())
        if not active:pending=None
    stats=metrics(trades);stats.update(max_drawdown_fraction=dd,ending_equity=cash,rejected=rejected)
    return trades,stats


def metrics(trades):
    pnls=[t.pnl for t in trades];rs=[t.r for t in trades]
    gain=sum(x for x in pnls if x>0);loss=-sum(x for x in pnls if x<0)
    n=len(rs);mean=statistics.mean(rs) if n else None
    # Descriptive normal interval; dependence/selection means it cannot certify edge.
    se=statistics.stdev(rs)/math.sqrt(n) if n>1 else None
    return dict(trades=n,win_rate=sum(x>0 for x in pnls)/n if n else None,
                expectancy_usd=statistics.mean(pnls) if n else None,average_r=mean,
                profit_factor=gain/loss if loss else None,profit_factor_unbounded=bool(gain and not loss),
                net_pnl=sum(pnls),transaction_costs=sum(t.costs for t in trades),
                mean_r_ci95=[mean-1.96*se,mean+1.96*se] if se is not None else None)
