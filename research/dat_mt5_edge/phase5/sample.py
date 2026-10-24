"""Offline Tardis free-sample normalizer; arrival-time chronology, no sorting/fills."""
import csv,gzip,hashlib,io,json
from decimal import Decimal
from datetime import datetime,timezone
from pathlib import Path
from phase4.certify import certify,validate_quotes,FIELDS

URL='https://datasets.tardis.dev/v1/kraken/quotes/2026/06/01/XBT-USD.csv.gz'
RAW_SHA='cc5fbee1ae52d3eb38381990048bbfbd51a2f7f5aade612df7fc58e6a41968f6'
COLUMNS=['exchange','symbol','timestamp','local_timestamp','ask_amount','ask_price','bid_price','bid_amount']

def normalize(raw):
    if hashlib.sha256(raw).hexdigest()!=RAW_SHA:raise ValueError('primary sample hash drift')
    buf=gzip.decompress(raw)
    if len(buf)>256*1024*1024:raise ValueError('decompressed ceiling')
    reader=csv.DictReader(io.StringIO(buf.decode()))
    if reader.fieldnames!=COLUMNS:raise ValueError('schema drift')
    buckets={};last_recv=-1;last_exchange=-1;back=0;future=0;max_lag=0;repeats=0;rows=0
    first=None;last=None
    start=1780272000000000;end=start+86400000000
    for r in reader:
        if r['exchange']!='kraken' or r['symbol']!='XBT/USD':raise ValueError('identity drift')
        exch=int(r['timestamp']);recv=int(r['local_timestamp'])
        if recv<last_recv or not start<=recv<end:raise ValueError('arrival chronology/day')
        back+=exch<last_exchange;future+=exch>recv;repeats+=recv==last_recv
        max_lag=max(max_lag,recv-exch)
        b,a,bv,av=[Decimal(r[k]) for k in ('bid_price','ask_price','bid_amount','ask_amount')]
        if not all(x.is_finite() for x in (b,a,bv,av)) or not 0<b<=a or min(bv,av)<0:raise ValueError('invalid quote')
        minute=(recv//60000000)*60
        if minute not in buckets:buckets[minute]=[b,b,b,b,a,a,a,a,bv+av]
        else:
            q=buckets[minute];q[1]=max(q[1],b);q[2]=min(q[2],b);q[3]=b;q[5]=max(q[5],a);q[6]=min(q[6],a);q[7]=a;q[8]=bv+av
        first=recv if first is None else first;last=recv;last_recv=recv;last_exchange=exch;rows+=1
    out=io.StringIO();w=csv.writer(out,lineterminator='\n');w.writerow(FIELDS)
    for t,q in buckets.items():w.writerow([t,*q])
    normalized=out.getvalue().encode();quality,_=validate_quotes(normalized,'0.1',1)
    calendar=json.dumps(list(range(start//1000000,end//1000000,60)),separators=(',',':')).encode()
    # Diagnostic unit/tick assumptions are NOT independent historical contract proof.
    manifest={'data_sha256':hashlib.sha256(normalized).hexdigest(),'calendar_sha256':hashlib.sha256(calendar).hexdigest(),
      'contract':{'symbol':'XBT/USD','venue':'KRAKEN_SPOT','price_units':'USD/BTC','pnl_currency':'USD','volume_semantics':'available_quote_volume',
                  'tick_size':'0.1','digits':1,'point_value':'1','tick_value':'0.1'},
      'costs':{'commission_per_side':'0','slippage_ticks':'0','financing_per_day':'0','currency':'USD','schedule_date':'UNVERIFIED_DIAGNOSTIC_ONLY'},
      'timezone':'UTC','timestamp_semantics':'BAR_OPEN','previously_evaluated_intervals':[]}
    decision=certify(manifest,normalized,calendar,{},[],1792368000)
    return normalized,{'url':URL,'raw_sha256':RAW_SHA,'decoded_sha256':hashlib.sha256(buf).hexdigest(),'raw_bytes':len(raw),
      'raw_quote_rows':rows,'first_receive_us':first,'last_receive_us':last,'exchange_timestamp_backsteps':back,
      'exchange_time_after_receive_count':future,'repeated_receive_timestamps':repeats,'max_observed_receive_lag_us':max_lag,
      'normalization':'Original file order, UTC receive-time minute buckets; no sorting, filling or synthetic quotes',
      'volume':'End-of-minute sum of best bid and ask available BTC quantities; not trade volume or tick count',
      'quality':quality,'certification':decision,'strategy_backtests':0}

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    raw=(root/'work/kraken_quotes_2026-06-01_XBT-USD.csv.gz').read_bytes()
    data,result=normalize(raw)
    (root/'work/normalized.csv').write_bytes(data)
    (root/'results/free_sample.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
