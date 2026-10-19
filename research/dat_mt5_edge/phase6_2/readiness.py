"""DAT MT5 Phase 6.2: deterministic OFFLINE research gates and hypothetical fills.

No network, MT5, credentials, broker SDK, order methods, or strategy optimizer.
Synthetic fixtures only prove software behaviour. No trading edge is certified here.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from datetime import datetime, timezone, timedelta
from typing import Iterable


def decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError('decimal strings/integers required')
    try:
        d = Decimal(value)
    except (ValueError, ArithmeticError) as exc:
        raise ValueError('invalid decimal') from exc
    if not d.is_finite():
        raise ValueError('nonfinite decimal')
    return d


def positive(value: object) -> Decimal:
    d = decimal(value)
    if d <= 0:
        raise ValueError('nonpositive value')
    return d


def nonnegative(value: object) -> Decimal:
    d = decimal(value)
    if d < 0:
        raise ValueError('negative value')
    return d


@dataclass(frozen=True)
class Fold:
    name: str
    train_start: int  # UTC Unix seconds, inclusive
    train_end: int    # UTC Unix seconds, exclusive
    test_start: int   # UTC Unix seconds, inclusive
    test_end: int     # UTC Unix seconds, exclusive


def normalize_timestamp(value: str, convention: str) -> int:
    """Unambiguous source convention, independent of machine timezone/DST.

    UTC ISO offset stamps are allowed with convention UTC; fixed EST export
    requires naive local representation and ALWAYS means UTC-5 (no DST).
    """
    if not isinstance(value, str) or convention not in ('UTC','EST_NO_DST'):
        raise ValueError('unapproved clock convention')
    try:
        d=datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('invalid ISO timestamp') from exc
    if convention == 'EST_NO_DST':
        if d.tzinfo is not None:
            raise ValueError('fixed EST requires unzoned wall time')
        d=d.replace(tzinfo=timezone(timedelta(hours=-5)))
    elif d.tzinfo is None or d.utcoffset()!=timedelta(0):
        raise ValueError('UTC offset required, nonzero offsets denied')
    if d.second or d.microsecond:
        raise ValueError('minute alignment required')
    return int(d.timestamp())


def validate_folds(folds: Iterable[Fold], embargo_seconds: int) -> tuple[Fold, ...]:
    """Declare folds before performance review; never derive fold boundaries from returns."""
    if type(embargo_seconds) is not int or embargo_seconds < 0:
        raise ValueError('invalid embargo')
    out = tuple(folds)
    if not out or len({f.name for f in out}) != len(out):
        raise ValueError('missing or duplicate folds')
    previous_test_end = -1
    for f in out:
        if not f.name or any(type(x) is not int for x in
                             (f.train_start, f.train_end, f.test_start, f.test_end)):
            raise ValueError('invalid fold fields')
        if not 0 <= f.train_start < f.train_end <= f.test_start < f.test_end:
            raise ValueError('invalid fold ordering')
        if f.test_start - f.train_end < embargo_seconds:
            raise ValueError('insufficient embargo')
        if f.test_start < previous_test_end:
            raise ValueError('overlapping or nonchronological tests')
        if previous_test_end >= 0 and f.train_end < previous_test_end:
            raise ValueError('training omits previously elapsed test history')
        previous_test_end = f.test_end
    return out


def validate_sealed_holdout(folds: Iterable[Fold], sealed_start: int) -> None:
    if type(sealed_start) is not int or sealed_start <= 0:
        raise ValueError('invalid holdout boundary')
    if any(f.test_end > sealed_start for f in folds):
        raise ValueError('sealed final holdout is not available for development')


def research_gate(*, folds: Iterable[Fold], expected_by_fold: dict[str, set[int]],
                  observed_by_fold: dict[str, set[int]], trades_by_fold: dict[str, list[dict]],
                  min_trades: int = 100, min_active_days: int = 60,
                  min_fold_trades: int = 20, min_coverage: str = '0.99',
                  required_sessions: tuple[str, ...] = ('ASIA', 'LONDON', 'NEW_YORK'),
                  required_regimes: tuple[str, ...] = ('TREND', 'RANGE', 'VOLATILE'),
                  min_segment_trades: int = 10, evidence_certified: bool = False) -> dict:
    """Return eligibility gates, NEVER an edge/performance verdict.

    `expected_by_fold` comes from an independently reviewed exchange/broker calendar,
    not from observed ticks. `trades_by_fold` are supplied historical hypothetical
    events; no trades, fills, fees or profits are created by this gate.
    """
    fs = validate_folds(folds, 0)
    if any(type(x) is not int or x <= 0 for x in
           (min_trades, min_active_days, min_fold_trades, min_segment_trades)):
        raise ValueError('invalid thresholds')
    coverage_threshold = decimal(min_coverage)
    if not 0 < coverage_threshold <= 1:
        raise ValueError('invalid coverage threshold')
    if set(expected_by_fold) != {f.name for f in fs} or set(observed_by_fold) != set(expected_by_fold) or set(trades_by_fold) != set(expected_by_fold):
        raise ValueError('fold evidence mismatch')
    failures = []
    expected_total = observed_total = 0
    event_count = 0
    active = set()
    session_counts: dict[str, int] = {}
    regime_counts: dict[str, int] = {}
    per_fold = []
    for f in fs:
        expected, observed, trades = expected_by_fold[f.name], observed_by_fold[f.name], trades_by_fold[f.name]
        if not expected or any(type(t) is not int or not f.test_start <= t < f.test_end for t in expected | observed):
            raise ValueError('invalid or out-of-fold calendar/observations')
        if not observed <= expected:
            raise ValueError('unreviewed/outside-calendar observations')
        expected_total += len(expected)
        observed_total += len(observed)
        event_count += len(trades)
        if len(trades) < min_fold_trades:
            failures.append('MIN_TRADES_FOLD:'+f.name)
        cov = Decimal(len(observed)) / Decimal(len(expected))
        if cov < coverage_threshold:
            failures.append('MIN_COVERAGE_FOLD:'+f.name)
        for row in trades:
            if type(row) is not dict or type(row.get('timestamp')) is not int or not f.test_start <= row['timestamp'] < f.test_end:
                raise ValueError('invalid or nonchronological trade timestamp')
            if row['timestamp'] not in observed:
                raise ValueError('trade without observed market data')
            if row.get('session') not in required_sessions or row.get('regime') not in required_regimes:
                raise ValueError('unregistered session or regime')
            active.add(row['timestamp']//86400)
            session_counts[row['session']] = session_counts.get(row['session'], 0) + 1
            regime_counts[row['regime']] = regime_counts.get(row['regime'], 0) + 1
        per_fold.append({'name': f.name, 'observed': len(observed), 'expected': len(expected),
                         'coverage': str(cov), 'trades': len(trades)})
    if event_count < min_trades:
        failures.append('MIN_TRADES_TOTAL')
    if len(active) < min_active_days:
        failures.append('MIN_ACTIVE_DAYS')
    if Decimal(observed_total)/Decimal(expected_total) < coverage_threshold:
        failures.append('MIN_COVERAGE_TOTAL')
    for session in required_sessions:
        if session_counts.get(session, 0) < min_segment_trades:
            failures.append('MIN_SESSION:'+session)
    for regime in required_regimes:
        if regime_counts.get(regime, 0) < min_segment_trades:
            failures.append('MIN_REGIME:'+regime)
    if not evidence_certified:
        failures.append('CERTIFIED_DATA_EVIDENCE_REQUIRED')
    return {'research_eligible': not failures, 'edge_certified': False,
            'execution_authority': False, 'failures': sorted(failures),
            'total_trades': event_count, 'active_utc_days': len(active),
            'coverage': str(Decimal(observed_total)/Decimal(expected_total)),
            'folds': per_fold, 'by_session': session_counts, 'by_regime': regime_counts}


@dataclass(frozen=True)
class Contract:
    symbol: str
    pnl_currency: str
    tick_size: Decimal
    tick_value: Decimal  # PnL currency per tick per 1 unit of quantity
    commission_per_side: Decimal  # PnL currency per 1 unit of quantity
    financing_per_night: Decimal  # PnL currency per 1 unit of quantity
    verified: bool = False

    def validate(self) -> None:
        if not self.symbol or len(self.pnl_currency) != 3 or not self.pnl_currency.isalpha():
            raise ValueError('incomplete contract identity')
        positive(self.tick_size); positive(self.tick_value)
        nonnegative(self.commission_per_side); nonnegative(self.financing_per_night)
        if not self.verified:
            raise ValueError('unverified contract: hypothetical fills blocked')


@dataclass(frozen=True)
class Quote:
    timestamp_ms: int
    bid: Decimal
    ask: Decimal

    def validate(self, contract: Contract) -> None:
        if type(self.timestamp_ms) is not int or self.timestamp_ms < 0:
            raise ValueError('invalid quote clock')
        b, a = positive(self.bid), positive(self.ask)
        if b > a or b % contract.tick_size or a % contract.tick_size:
            raise ValueError('crossed/off-grid quote')


def _fill(q: Quote, buy: bool, c: Contract, spread_mult: Decimal, slip_ticks: Decimal) -> Decimal:
    middle = (q.bid + q.ask)/2
    half_spread = (q.ask - q.bid)*spread_mult/2
    raw = middle + (half_spread if buy else -half_spread)
    raw += c.tick_size*slip_ticks*(1 if buy else -1)
    direction = ROUND_CEILING if buy else ROUND_FLOOR
    return (raw/c.tick_size).to_integral_value(rounding=direction)*c.tick_size


def hypothetical_round_trip(entry: Quote, exit: Quote, *, side: int, quantity: str,
                            contract: Contract, spread_mult: str = '1', slippage_ticks: str = '0',
                            commission_mult: str = '1', financing_mult: str = '1',
                            financing_nights: int = 0) -> dict:
    """Pure side-correct bid/ask hypothetical arithmetic, not an order interface.

    Explicit financing_nights avoids making up a broker rollover schedule.
    Exchange conversion, financing schedule, quantity rules and contract must be
    independently verified. No independent fills are inferred between snapshots.
    """
    contract.validate(); entry.validate(contract); exit.validate(contract)
    if entry.timestamp_ms >= exit.timestamp_ms or type(side) is not int or side not in (-1, 1):
        raise ValueError('invalid chronology/side')
    if type(financing_nights) is not int or financing_nights < 0:
        raise ValueError('invalid overnight count')
    qty=positive(quantity);spread=positive(spread_mult);slip=nonnegative(slippage_ticks)
    comm=positive(commission_mult);finance=positive(financing_mult)
    e=_fill(entry,side==1,contract,spread,slip)
    x=_fill(exit,side==-1,contract,spread,slip)
    pnl_per_price=contract.tick_value/contract.tick_size
    gross=Decimal(side)*(x-e)*qty*pnl_per_price
    commission=qty*contract.commission_per_side*2*comm
    financing=qty*contract.financing_per_night*financing_nights*finance
    return {'entry_price':str(e),'exit_price':str(x),'gross_pnl':str(gross),
            'commissions':str(commission),'financing':str(financing),
            'net_pnl':str(gross-commission-financing),'execution_authority':False}


def sensitivity_grid(entry: Quote, exit: Quote, *, side: int, quantity: str,
                     contract: Contract, financing_nights: int = 0) -> list[dict]:
    scenarios=(('baseline_1tick','1','1','1','1'),('spread_2x','2','1','1','1'),
               ('slippage_2ticks','1','2','1','1'),('commission_2x','1','1','2','1'),
               ('financing_2x','1','1','1','2'),('combined_stress','2','2','2','2'))
    return [{'scenario':name,**hypothetical_round_trip(entry,exit,side=side,quantity=quantity,
             contract=contract,spread_mult=s,slippage_ticks=l,commission_mult=k,
             financing_mult=f,financing_nights=financing_nights)}
            for name,s,l,k,f in scenarios]


# Predeclared protocol only; frozen 2026-01-01 through 2026-09-30 remains SEALED.
SEALED_2026_HOLDOUT_START = int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())
