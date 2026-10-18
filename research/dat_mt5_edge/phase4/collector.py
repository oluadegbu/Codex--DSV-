"""Passive MT5-export consumer: bytes in, validated quote tuples out.
No SDK, file I/O, sockets, callbacks, dynamic imports or terminal/account functions.
This is NOT an MT5 exporter and does not authenticate the external producer.
"""
import json
from decimal import Decimal

KEYS={'schema','source_id','symbol','sequence','timestamp_ms','bid','ask'}

def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('duplicate JSON key')
        result[k]=v
    return result

def decimal(value):
    if type(value)not in (str,int):raise ValueError('decimal string required')
    x=Decimal(value)
    if not x.is_finite() or x<=0:raise ValueError('invalid price')
    return x

class PassiveCollector:
    def __init__(self,source_id,symbol,tick_size,max_spread,max_age_ms=5000):
        if type(source_id)is not str or not source_id or type(symbol)is not str or not symbol:raise ValueError('identity')
        self.source_id=source_id;self.symbol=symbol
        self.tick=decimal(tick_size);self.max_spread=decimal(max_spread)
        if type(max_age_ms)is not int or not 0<max_age_ms<=60000:raise ValueError('age policy')
        self.max_age_ms=max_age_ms;self.sequence=-1;self.timestamp=-1
    def consume(self,raw,now_ms):
        if type(raw)is not bytes or len(raw)>4096:raise ValueError('bounded bytes required')
        if type(now_ms)is not int:raise ValueError('clock required')
        q=json.loads(raw,object_pairs_hook=unique)
        if type(q)is not dict or set(q)!=KEYS or q['schema']!='MT5_QUOTES_V1':raise ValueError('quote-only schema')
        if q['source_id']!=self.source_id or q['symbol']!=self.symbol:raise ValueError('unapproved source/symbol')
        seq=q['sequence'];t=q['timestamp_ms']
        if type(seq)is not int or type(t)is not int or seq<=self.sequence or t<=self.timestamp:raise ValueError('replay/order')
        if not 0<=now_ms-t<=self.max_age_ms:raise ValueError('stale/future quote')
        b=decimal(q['bid']);a=decimal(q['ask'])
        if a<b or a-b>self.max_spread:raise ValueError('spread')
        if b%self.tick or a%self.tick:raise ValueError('tick grid')
        # Commit sequence only after every check passes. A fresh instance cannot
        # establish durable replay protection; restart reconciliation is external.
        self.sequence=seq;self.timestamp=t
        return (self.symbol,t,str(b),str(a),seq)
