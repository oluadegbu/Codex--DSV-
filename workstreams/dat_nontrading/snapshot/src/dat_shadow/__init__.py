"""Isolated deterministic historical-data research; no broker or execution API."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable

MAX_BARS = 1000
MAX_QUANTITY = Decimal('100')


class ShadowViolation(ValueError):
    pass


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ShadowViolation('unsupported numeric value')
    try:
        text = str(value)
        if len(text) > 80:
            raise ShadowViolation('numeric representation resource limit exceeded')
        result = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ShadowViolation('invalid numeric value') from exc
    if not result.is_finite():
        raise ShadowViolation('nonfinite data rejected')
    if result.copy_abs() > Decimal('1e18') or result.as_tuple().exponent < -18:
        raise ShadowViolation('numeric magnitude or precision resource limit exceeded')
    return result


@dataclass(frozen=True)
class Bar:
    timestamp: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class PaperResult:
    synthetic_id: str
    sample_count: int
    entry_timestamp: int
    exit_timestamp: int
    quantity: str
    gross_pnl: str
    fees: str
    slippage: str
    net_pnl: str
    mode: str = 'SHADOW'


def validate_bars(bars: Iterable[Bar], *, observed_at: int) -> tuple[Bar, ...]:
    if isinstance(observed_at, bool) or not isinstance(observed_at, int) or observed_at < 0:
        raise ShadowViolation('invalid historical observation time')
    validated = []
    previous = -1
    for index, bar in enumerate(bars):
        if index >= MAX_BARS:
            raise ShadowViolation('sample resource limit exceeded')
        if not isinstance(bar, Bar):
            raise ShadowViolation('bar schema required')
        t = bar.timestamp
        if isinstance(t, bool) or not isinstance(t, int) or t < 0 or t <= previous:
            raise ShadowViolation('timestamps must be strictly increasing')
        if t > observed_at:
            raise ShadowViolation('future bars rejected')
        o, h, l, c, v = map(number, (bar.open, bar.high, bar.low, bar.close, bar.volume))
        if min(o, h, l, c) <= 0 or v < 0 or l > min(o, c) or h < max(o, c) or l > h:
            raise ShadowViolation('invalid OHLCV geometry')
        validated.append(Bar(t, o, h, l, c, v))
        previous = t
    if len(validated) < 2:
        raise ShadowViolation('at least two historical bars required')
    return tuple(validated)


def simulate(bars: Iterable[Bar], *, synthetic_id: str, observed_at: int,
             quantity='1', fee_bps='10', slippage_bps='20', mode='SHADOW',
             order_intent=None) -> PaperResult:
    """Mark hypothetical long exposure from first close to last close, with costs.

    Caller supplies only synthetic data labels. This returns arithmetic research
    output; there is no execution, broker, symbol mapping, or external I/O.
    """
    if mode != 'SHADOW' or order_intent is not None:
        raise ShadowViolation('only shadow arithmetic without order intent permitted')
    if not isinstance(synthetic_id, str) or not synthetic_id.startswith('SYNTH-') or not synthetic_id[6:].isalnum() or len(synthetic_id) > 48:
        raise ShadowViolation('synthetic research identifier required')
    q, fee, slip = map(number, (quantity, fee_bps, slippage_bps))
    if not (0 < q <= MAX_QUANTITY) or not (0 <= fee <= 10000) or not (0 <= slip <= 10000):
        raise ShadowViolation('invalid or unbounded research parameters')
    history = validate_bars(bars, observed_at=observed_at)
    entry, end = history[0], history[-1]
    # Isolate arithmetic from ambient Decimal context to preserve determinism.
    from decimal import localcontext
    with localcontext() as ctx:
        ctx.prec = 50
        gross = (end.close - entry.close) * q
        notional = (end.close + entry.close) * q
        fees = notional * fee / Decimal(10000)
        slippage = notional * slip / Decimal(10000)
        return PaperResult(synthetic_id, len(history), entry.timestamp, end.timestamp,
                           str(q), str(gross), str(fees), str(slippage), str(gross - fees - slippage))
