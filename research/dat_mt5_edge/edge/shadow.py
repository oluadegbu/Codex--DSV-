"""Read-only future SHADOW input contract. Never imports or starts MT5."""
from datetime import datetime,timedelta
from pathlib import Path
import json
import math

SYMBOLS={'BTCUSD':'BTCUSD','XAUUSD':'XAUUSD.crp','NAS100':'NAS100','SP500':'SP500'}
class FileShadowFeed:
    def __init__(self,path:Path):
        self.path=path;self.last_sequence=-1;self.last_time=None
    def read(self,now:datetime):
        if now.tzinfo is None:raise ValueError('aware clock required')
        x=json.loads(self.path.read_text())
        required={'schema','sequence','timestamp','symbol','broker_symbol','bid','ask','contract_verified','source'}
        if set(x)!=required or x['schema']!='DAT_MARKET_DATA_ONLY_V1':raise ValueError('unsupported or extra snapshot fields')
        if type(x['sequence']) is not int or x['sequence']<=self.last_sequence:raise ValueError('replay or invalid sequence')
        if x['symbol'] not in SYMBOLS or x['broker_symbol']!=SYMBOLS[x['symbol']]:raise ValueError('unapproved symbol mapping')
        if x['contract_verified'] is not True:raise ValueError('unverified contract')
        if not isinstance(x['source'],str) or not x['source']:raise ValueError('missing source')
        t=datetime.fromisoformat(x['timestamp'])
        if t.tzinfo is None or not timedelta(0)<=now-t<=timedelta(seconds=60):raise ValueError('stale/future/naive quote')
        if self.last_time and t<=self.last_time:raise ValueError('nonmonotonic quote')
        if any(type(x[k]) not in (int,float) or not math.isfinite(x[k]) or x[k]<=0 for k in ('bid','ask')) or x['bid']>x['ask']:raise ValueError('invalid quote')
        self.last_sequence=x['sequence'];self.last_time=t
        return x
