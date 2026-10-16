"""Public commit-pinned Dukascopy tick mirror. Does not use broker access.

CSV bid/ask ticks are aggregated without carry-forward to minute OHLC.
Timezone is interpreted as upstream Dukascopy UTC; independent primary-feed
cross-verification is a qualification gate, never inferred from price patterns.
"""
import csv,gzip,hashlib,json,math,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,date,timedelta,timezone
from pathlib import Path

def run(root,pins,workers=8):
    root=Path(root);rd=root/'mirror_raw';rd.mkdir(parents=True,exist_ok=True)
    archive_inventory=json.loads((root/'archive_inventory.json').read_text()) if (root/'archive_inventory.json').exists() else {}
    if archive_inventory and any(archive_inventory[s]['pin']!=pin for s,pin in pins.items()):raise ValueError('archive pin mismatch')
    jobs=[]
    for month in (1,4,7):
        d=date(2018,month,1)
        while d.month==month:
            if d.weekday()<5:
                for sym,pin in pins.items():
                    for hour in range(24):jobs.append((sym,pin,d,hour))
            d+=timedelta(days=1)
    def fetch(job):
        sym,pin,d,hour=job
        name=f'{d}--{hour:02}h_ticks.csv';path=f'{sym}/2018/{d.month:02}/{name}'
        url=f'https://raw.githubusercontent.com/FX-Data/FX-Data-{sym}-DS/{pin}/{path}'
        p=rd/f'{sym}_{name}';prefix=f'{d.year:04}.{d.month:02}.{d.day:02} {hour:02}:';base=int(datetime.combine(d,datetime.min.time(),timezone.utc).timestamp())+hour*3600
        try:
            if archive_inventory and not p.exists():raise FileNotFoundError('not present in pinned archive')
            data=p.read_bytes() if p.exists() else urllib.request.urlopen(url,timeout=8).read()
            buckets={};last=-1;tick_count=0;invalid=0
            for r in csv.reader(data.decode().splitlines()):
                if len(r)!=5:raise ValueError('tick schema')
                stamp=r[0]
                if not stamp.startswith(prefix)or len(stamp)!=23 or stamp[16]!=':'or stamp[19]!='.':raise ValueError('tick date/hour mismatch')
                minute=int(stamp[14:16]);second=int(stamp[17:19]);millis=int(stamp[20:23])
                if minute>=60 or second>=60:raise ValueError('invalid tick time')
                sec=base+minute*60+second+millis/1000;bid,ask,bv,av=map(float,r[1:])
                if sec<last or not all(math.isfinite(x) for x in (bid,ask,bv,av)) or not 0<bid<=ask or min(bv,av)<0:raise ValueError('invalid tick')
                last=sec;tick_count+=1;k=int(sec)//60*60
                if k not in buckets:buckets[k]=[k,bid,bid,bid,bid,ask,ask,ask,ask,bv+av]
                else:
                    a=buckets[k];a[2]=max(a[2],bid);a[3]=min(a[3],bid);a[4]=bid
                    a[6]=max(a[6],ask);a[7]=min(a[7],ask);a[8]=ask;a[9]+=bv+av
            if not p.exists():p.write_bytes(data)
            return sym,list(buckets.values()),dict(url=url,sha256=hashlib.sha256(data).hexdigest(),ticks=tick_count,minutes=len(buckets))
        except Exception as e:return sym,[],dict(url=url,error=type(e).__name__)
    allrows={s:[] for s in pins};sources=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for n,f in enumerate(as_completed([pool.submit(fetch,j) for j in jobs]),1):
            sym,rows,meta=f.result();allrows[sym].extend(rows);sources.append(meta)
            if n%200==0:print(json.dumps(dict(done=n,total=len(jobs),failed=sum('error'in x for x in sources))),flush=True)
    stats={}
    for sym,rows in allrows.items():
        rows.sort(key=lambda r:r[0]);assert len({r[0] for r in rows})==len(rows)
        text='timestamp,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,volume\n'+''.join(','.join(map(str,r))+'\n' for r in rows)
        (root/f'{sym}_1m.csv.gz').write_bytes(gzip.compress(text.encode(),mtime=0))
        stats[sym]=dict(rows=len(rows),sha256=hashlib.sha256(text.encode()).hexdigest(),first=rows[0][0]if rows else None,last=rows[-1][0]if rows else None)
    report=dict(protocol='PINNED_DUKASCOPY_TICK_MIRROR_V1',pins=pins,months=[1,4,7],year=2018,timezone_interpretation='UTC',primary_crossverified=False,
                archive_inventory=archive_inventory,instruments=stats,sources=sorted(sources,key=lambda x:x['url']))
    (root/'mirror_manifest.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(stats),flush=True)
