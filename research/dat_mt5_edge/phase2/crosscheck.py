"""Independent spot check of pinned mirror bars against primary public daily candles."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import urllib.request,json
from .acquire_quotes import decode,SCALES
from .model import load

def crosscheck(root):
    root=Path(root);reports={}
    def one(job):
        sym,side=job;day=date(2018,1,3)
        url=f'https://datafeed.dukascopy.com/datafeed/{sym}/2018/00/03/{side}_candles_min_1.bi5'
        try:
            data=urllib.request.urlopen(url,timeout=8).read();primary=decode(data,day,SCALES[sym]);bars,_=load(root/f'{sym}_1m.csv.gz')
            mirror={b.t:(b.bo,b.bh,b.bl,b.bc)if side=='BID'else(b.ao,b.ah,b.al,b.ac)for b in bars}
            pairs=[(r,mirror[r[0]])for r in primary.values()if r[0]in mirror]
            same=sum(all(abs(a-b)<=1/SCALES[sym]+1e-10 for a,b in zip(r[1:5],m))for r,m in pairs)
            return sym,side,dict(url=url,compared=len(pairs),matching=same,verified=len(pairs)>=1200 and same/len(pairs)>=.999)
        except Exception as e:return sym,side,dict(url=url,error=type(e).__name__,verified=False)
    with ThreadPoolExecutor(max_workers=3)as pool:
        for sym,side,r in pool.map(one,[(s,side)for s in SCALES for side in ('BID','ASK')]):reports.setdefault(sym,{})[side]=r
    p=root/'mirror_manifest.json';manifest=json.loads(p.read_text());manifest['primary_crosscheck']=reports
    manifest['primary_crossverified']=all(x['verified']for r in reports.values()for x in r.values())
    p.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n');print(json.dumps(reports),flush=True)
    return reports
