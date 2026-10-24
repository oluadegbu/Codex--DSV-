"""Explicit public HTTP acquisition only; no broker API or credential handling.

Dukascopy minute BID/ASK records are big-endian seconds/open/close/low/high/volume.
Months in source URL are zero-based. UTC timestamps identify bar opens.
"""
import argparse,csv,gzip,hashlib,json,lzma,math,struct,time,urllib.request
from datetime import date,datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
SCALES={'EURUSD':100000,'GBPUSD':100000,'XAUUSD':1000}

def decode(raw,day,scale):
    buf=lzma.decompress(raw)
    if len(buf)%24:raise ValueError('invalid record size')
    rows={};epoch=int(datetime.combine(day,datetime.min.time(),timezone.utc).timestamp())
    for i in range(0,len(buf),24):
        sec,o,c,l,h,v=struct.unpack('>IIIIIf',buf[i:i+24])
        if sec%60 or sec>=86400 or sec in rows or not 0<l<=min(o,c)<=max(o,c)<=h or not math.isfinite(v) or v<0:
            raise ValueError('invalid record')
        rows[sec]=(epoch+sec,o/scale,h/scale,l/scale,c/scale,v)
    return rows

def acquire(root,start,end,workers=6):
    root=Path(root);rawdir=root/'raw';rawdir.mkdir(parents=True,exist_ok=True)
    days=[];d=start
    while d<end:
        if d.weekday()<5:days.append(d) # Weekday research windows only; no Sunday data inferred.
        d+=timedelta(days=1)
    def fetch(job):
        sym,d,side=job;p=rawdir/f'{sym}_{d}_{side}.bi5'
        url=f'https://datafeed.dukascopy.com/datafeed/{sym}/{d.year}/{d.month-1:02}/{d.day:02}/{side}_candles_min_1.bi5'
        error=None
        for attempt in range(3):
            try:
                raw=p.read_bytes() if p.exists() else urllib.request.urlopen(url,timeout=10).read()
                rows=decode(raw,d,SCALES[sym])
                if not p.exists():p.write_bytes(raw)
                return sym,d,side,rows,dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),records=len(rows))
            except Exception as e:error=type(e).__name__
        return sym,d,side,None,dict(url=url,error=error)
    jobs=[(s,d,side) for s in SCALES for d in days for side in ('BID','ASK')]
    fetched={};sources=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for n,f in enumerate(as_completed([pool.submit(fetch,j) for j in jobs]),1):
            sym,d,side,rows,meta=f.result();fetched[sym,d,side]=rows
            sources.append(meta)
            if n%100==0:print(json.dumps({'completed':n,'total':len(jobs),'failed':sum('error' in x for x in sources)}),flush=True)
    reports={}
    for sym in SCALES:
        normalized=[];crossed=0;unpaired=0
        for d in days:
            bid=fetched.get((sym,d,'BID'));ask=fetched.get((sym,d,'ASK'))
            if bid is None or ask is None:continue
            unpaired+=len(set(bid)^set(ask))
            for sec in sorted(set(bid)&set(ask)):
                b=bid[sec];a=ask[sec]
                if a[1]<b[1] or a[4]<b[4]:crossed+=1;continue
                normalized.append((b[0],*b[1:5],*a[1:5],b[5]+a[5]))
        path=root/f'{sym}_1m.csv.gz'
        text='timestamp,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,volume\n'
        text+=''.join(','.join(map(str,r))+'\n' for r in normalized)
        path.write_bytes(gzip.compress(text.encode(),mtime=0))
        reports[sym]=dict(rows=len(normalized),first=normalized[0][0] if normalized else None,last=normalized[-1][0] if normalized else None,
                          crossed_removed=crossed,unpaired_minutes=unpaired,normalized_sha256=hashlib.sha256(text.encode()).hexdigest())
    report=dict(protocol='DUKASCOPY_PAIRED_MINUTE_V1',start=str(start),end_exclusive=str(end),weekday_files_only=True,
                price_scale=SCALES,instruments=reports,sources=sorted(sources,key=lambda x:x['url']))
    (root/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(reports),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--start',type=date.fromisoformat,default=date(2022,7,1));p.add_argument('--end',type=date.fromisoformat,default=date(2023,7,1));p.add_argument('--workers',type=int,default=6)
    a=p.parse_args();acquire(a.root,a.start,a.end,a.workers)
