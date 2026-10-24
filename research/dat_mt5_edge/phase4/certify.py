"""Pure deterministic checks. Evidence trust is separate from a dataset's claims.
No acquisition, broker, credential or execution dependencies.
"""
import csv,hashlib,io,json
from datetime import datetime,timedelta,timezone
from decimal import Decimal,InvalidOperation

FIELDS=['timestamp','bid_open','bid_high','bid_low','bid_close','ask_open','ask_high','ask_low','ask_close','volume']
PROOFS=('provenance','license','clock','calendar','contract','costs','normalization')

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def number(value):
    if isinstance(value,bool):raise ValueError('boolean number')
    try:v=Decimal(str(value))
    except InvalidOperation:raise ValueError('invalid number')
    if not v.is_finite():raise ValueError('nonfinite')
    return v

def utc_epoch(text,convention):
    """Source convention must be independently reviewed; EST is fixed UTC-5."""
    if convention not in ('UTC','EST_NO_DST'):raise ValueError('ambiguous source timezone')
    d=datetime.fromisoformat(text)
    if d.tzinfo is not None:raise ValueError('expected naive source representation')
    tz=timezone.utc if convention=='UTC' else timezone(timedelta(hours=-5))
    return int(d.replace(tzinfo=tz).timestamp())

def validate_quotes(raw,tick,digits):
    tick=number(tick)
    if tick<=0 or type(digits)is not int or not 0<=digits<=12:raise ValueError('precision metadata')
    if tick*10**digits!=(tick*10**digits).to_integral_value():raise ValueError('tick/digits mismatch')
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8')))
    if reader.fieldnames!=FIELDS:raise ValueError('quote schema')
    seen=set();last=None;spreads=[];zero=0;times=[]
    for row in reader:
        if None in row or any(x is None for x in row.values()):raise ValueError('ragged row')
        t=int(row['timestamp'])
        if str(t)!=row['timestamp'] or t%60:raise ValueError('UTC minute alignment')
        if t in seen:raise ValueError('duplicate minute')
        if last is not None and t<=last:raise ValueError('nonmonotonic')
        p=[number(row[k]) for k in FIELDS[1:9]];v=number(row['volume'])
        if v<0:raise ValueError('negative volume')
        for o,h,l,c in (p[:4],p[4:]):
            if not 0<l<=min(o,c)<=max(o,c)<=h:raise ValueError('invalid OHLC')
        # Matching extrema of paired quote bars must preserve bid <= ask as well.
        if any(a<b for b,a in zip(p[:4],p[4:])):raise ValueError('crossed quote')
        for price in p:
            q=price/tick
            if abs(q-q.to_integral_value())>Decimal('0.00000001'):raise ValueError('off tick grid')
        spreads.extend((p[4]-p[0],p[7]-p[3]));zero+=v==0
        seen.add(t);times.append(t);last=t
    if not times:raise ValueError('empty quotes')
    spreads.sort()
    return {'rows':len(times),'first':times[0],'last':times[-1],
            'max_observed_wall_clock_gap_minutes':max([0]+[(b-a)//60-1 for a,b in zip(times,times[1:])]),
            'zero_volume':zero,'median_spread':str(spreads[len(spreads)//2]),
            'p95_spread':str(spreads[int(.95*(len(spreads)-1))])},set(times)

def certify(manifest,raw,calendar_raw,artifacts,reviewed_bundles,asof):
    """Artifacts map proof role to bytes; reviewed_bundles is maintained separately.
    A manifest cannot self-certify with verified=true. Review includes source/licensing
    and decoder correspondence; hashes prove identity, not truth of source statements.
    """
    errors=[];quality=None;coverage=None
    bundle=sha(canonical(manifest))
    if bundle not in reviewed_bundles:errors.append('UNREVIEWED_EVIDENCE_BUNDLE')
    if manifest.get('data_sha256')!=sha(raw):errors.append('DATA_HASH_MISMATCH')
    if manifest.get('calendar_sha256')!=sha(calendar_raw):errors.append('CALENDAR_HASH_MISMATCH')
    for role in PROOFS:
        proof=artifacts.get(role)
        if not proof or manifest.get('proofs',{}).get(role)!=sha(proof):errors.append('MISSING_OR_CHANGED_'+role.upper())
    spec=manifest.get('contract',{})
    try:
        tick=number(spec['tick_size']);point=number(spec['point_value']);value=number(spec['tick_value'])
        if min(tick,point,value)<=0 or tick*point!=value:raise ValueError('tick-value mismatch')
        if not all(spec.get(k) for k in ('symbol','venue','price_units','pnl_currency','volume_semantics')):raise ValueError('incomplete contract')
        if spec['volume_semantics'] not in ('available_quote_volume','trade_volume','tick_count','unavailable'):raise ValueError('unknown volume semantics')
        if manifest.get('purpose')=='broker_shadow' and not spec.get('broker_symbol'):raise ValueError('missing broker mapping')
        if manifest.get('asset_class')=='futures' and (not spec.get('contract_id') or manifest.get('adjusted_prices') is not False):raise ValueError('futures contract/roll')
        costs=manifest['costs']
        if any(number(costs[k])<0 for k in ('commission_per_side','slippage_ticks','financing_per_day')):raise ValueError('negative costs')
        if not costs.get('currency') or not costs.get('schedule_date'):raise ValueError('cost schedule')
        if costs['currency']!=spec['pnl_currency']:raise ValueError('cost/PNL currency conversion required')
        if manifest.get('timezone')!='UTC' or manifest.get('timestamp_semantics')!='BAR_OPEN':raise ValueError('clock semantics')
        quality,times=validate_quotes(raw,tick,spec['digits'])
    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
        errors.append('STRUCTURE_OR_METADATA:'+str(exc));times=set()
    expected=set()
    try:
        vals=json.loads(calendar_raw)
        if not isinstance(vals,list) or not vals or any(type(t)is not int or t%60 for t in vals):raise ValueError('calendar minutes')
        if vals!=sorted(set(vals)):raise ValueError('calendar duplicates/order')
        expected=set(vals)
        missing=expected-times;outside=times-expected
        coverage={'expected':len(expected),'observed_expected':len(times&expected),'missing':len(missing),'outside':len(outside),
                  'ratio':len(times&expected)/len(expected),'missing_sha256':sha(canonical(sorted(missing)))}
        if missing or outside:errors.append('UNREMEDIATED_SESSION_GAPS_OR_OUTSIDE_CALENDAR')
    except (ValueError,TypeError):errors.append('INVALID_CALENDAR')
    # No calendar inferred from observed quotes: expected minutes must be reviewed independently.
    overlaps=[]
    for lo,hi in manifest.get('previously_evaluated_intervals',[]):
        if any(lo<=t<hi for t in times):overlaps.append([lo,hi])
    if overlaps:errors.append('PREVIOUSLY_EVALUATED_NOT_FRESH_OOS')
    if not isinstance(manifest.get('previously_evaluated_intervals'),list):errors.append('MISSING_HOLDOUT_LINEAGE')
    certified=not errors
    active_days=len({t//86400 for t in times&expected})
    recent=bool(times) and max(times)>=asof-120*86400 and max(times)<asof
    return {'bundle_sha256':bundle,'data_sha256':sha(raw),'status':'CERTIFIED_RESEARCH_DATA' if certified else 'QUARANTINED',
            'research_ready':certified and active_days>=60 and recent,'active_utc_days':active_days,
            'recent_within_120_days':recent,'quality':quality,'coverage':coverage,'blockers':sorted(set(errors)),
            'fresh_oos':certified and not overlaps,'execution_authority':False}
