"""Pinned public-data acquisition/validation; separate from offline engine.

Default reads existing raw files only. --download explicitly fetches public data.
Raw third-party datasets are not committed. No broker credentials or MT5 API.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import argparse,csv,hashlib,json,math,urllib.request

PIN='fc162575330dad255443a75137c67cee7d89be0d'
HASHES={2017:'e04589a05a8cf25435d37910bc24b140892e92cc2eed4bebb2b1cd8c7fd88638',
        2018:'fb76d145d538ba863b76446f550be80aba0ee4b33684f5c6d881f973740ab649'}

def normalize(raw_dir:Path,out_dir:Path,download=False):
    out_dir.mkdir(parents=True,exist_ok=True)
    meta=[];out=['timestamp,open,high,low,close,volume']
    for year,expected in HASHES.items():
        p=raw_dir/f'bitfinex_BTCUSD_{year}_1m.csv'
        url=f'https://raw.githubusercontent.com/Zombie-3000/Bitfinex-historical-data/{PIN}/BTCUSD/Candles_1m/{year}/merged.csv'
        if download and not p.exists():
            raw_dir.mkdir(parents=True,exist_ok=True)
            with urllib.request.urlopen(url,timeout=60) as r:data=r.read()
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('download SHA256 mismatch')
            p.write_bytes(data)
        data=p.read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('source SHA256 mismatch')
        buckets=defaultdict(list);last=None;gaps=0;first=None;n=0
        for row in csv.reader(data.decode().splitlines()):
            t=int(row[0]);o,c,h,l,v=map(float,row[1:]);n+=1
            if first is None:first=t
            if last is not None:
                if t<=last:raise ValueError('non-increasing source timestamp')
                if t>last+60000:gaps+=(t-last)//60000-1
            last=t
            if t%60000 or not all(math.isfinite(x) for x in (o,c,h,l,v)) or not 0<l<=min(o,c)<=max(o,c)<=h or v<0:
                raise ValueError('invalid source OHLCV or timestamp')
            if datetime.fromtimestamp(t/1000,timezone.utc).year!=year:raise ValueError('source year mismatch')
            buckets[t//1800000].append((t,o,h,l,c,v))
        accepted=0;dropped=0
        for k,rs in sorted(buckets.items()):
            if len(rs)!=30 or [r[0] for r in rs]!=list(range(k*1800000,(k+1)*1800000,60000)):
                dropped+=1;continue
            ts=datetime.fromtimestamp(k*1800,timezone.utc).isoformat()
            out.append(','.join(map(str,(ts,rs[0][1],max(r[2] for r in rs),min(r[3] for r in rs),rs[-1][4],sum(r[5] for r in rs)))))
            accepted+=1
        meta.append(dict(year=year,source_sha256=expected,source_bytes=len(data),rows=n,first_ms=first,last_ms=last,
                         invalid=0,nonincreasing=0,missing_minutes=gaps,accepted_30m=accepted,dropped_buckets=dropped))
    raw=('\n'.join(out)+'\n').encode()
    (out_dir/'BTCUSD_30m.csv').write_bytes(raw)
    manifest=dict(years=meta,normalized_sha256=hashlib.sha256(raw).hexdigest())
    (out_dir/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,default=Path('data/raw'))
    p.add_argument('--output-dir',type=Path,default=Path('data'));p.add_argument('--download',action='store_true')
    a=p.parse_args();print(json.dumps(normalize(a.raw_dir,a.output_dir,a.download),indent=2))
