"""Offline reconstruction from eleven existing daily candle objects. No downloads."""
import csv,hashlib,io,json,lzma,math,struct
from collections import defaultdict
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from .certify import FIELDS,validate_quotes,sha

ROOT=Path(__file__).resolve().parent

def recover(root=ROOT):
    observations=json.loads((root/'recovery_observations.json').read_text())['records']
    sources=next(x for x in observations if x['type']=='manifest')['successful_sources']
    known={x['sha256']:x for x in sources};days=defaultdict(dict);objects=[]
    for item in (x for x in observations if x['type']=='raw'):
        p=root/'work/raw'/item['file'];raw=p.read_bytes()
        if sha(raw)!=item['sha256'] or sha(raw)not in known:raise ValueError('raw hash drift')
        buf=lzma.decompress(raw)
        if len(buf)%24:raise ValueError('record alignment')
        rows={};last=-1
        for i in range(0,len(buf),24):
            sec,o,c,l,h,v=struct.unpack('>IIIIIf',buf[i:i+24])
            if sec%60 or not last<sec<86400 or not 0<l<=min(o,c)<=max(o,c)<=h or not math.isfinite(v) or v<0:raise ValueError('invalid candle')
            rows[sec]=[Decimal(x)/100000 for x in (o,h,l,c)]+[Decimal(str(v))];last=sec
        _,day,side=p.stem.split('_');days[day][side]=rows
        objects.append({'file':p.name,'sha256':sha(raw),'records':len(rows),'record_integrity':'PASS'})
    output=io.StringIO();writer=csv.writer(output,lineterminator='\n');writer.writerow(FIELDS)
    pairs=[]
    for day,sides in sorted(days.items()):
        if set(sides)!=set(('BID','ASK')):continue
        b=sides['BID'];a=sides['ASK'];common=sorted(set(b)&set(a));epoch=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())
        for t in common:writer.writerow([epoch+t,*b[t][:4],*a[t][:4],b[t][4]+a[t][4]])
        pairs.append({'day':day,'paired_minutes':len(common),'unpaired_minutes':len(set(b)^set(a))})
    raw=output.getvalue().encode();quality,_=validate_quotes(raw,'0.00001',5)
    (root/'work/recovered_EURUSD_1m.csv').write_bytes(raw)
    return {'normalized_sha256':sha(raw),'quality':quality,'paired_days':pairs,'objects':objects,
            'original_objects_unchanged':True,'status':'QUARANTINED_CANARY_ONLY',
            'reasons':['ONLY_THREE_DAYS','NO_RECENT_COVERAGE','UNREVIEWED_METADATA_LICENSE_AND_COSTS','SOURCE_CAPTURE_NOT_INDEPENDENTLY_ATTESTED']}

if __name__=='__main__':print(json.dumps(recover(),sort_keys=True,indent=2))
