"""Offline MCP Events/Standard Webhooks contract lab; no network/auth provisioning.

Ephemeral synthetic subscription identities only. A verified signed receipt is
never human approval. OAuth, remote subscriptions and provider identity remain
external certification gates. Keys stay in memory and are never stored in SQLite.
"""
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import hmac
import json
from dci.bridge.protocol import ProtocolError, canonical, identifier

MAX_BYTES=262144
EVENTS={'dmb.shadow.result','dmb.shadow.notification'}


@dataclass(frozen=True)
class LabSubscription:
    subscription_id: str
    principal: str
    event_name: str
    expires: int
    secret: bytes = field(repr=False,compare=False)
    active: bool = True

    def check(self,now):
        identifier(self.subscription_id)
        if not isinstance(self.principal,str) or not self.principal.startswith('synthetic-') or self.event_name not in EVENTS or type(self.secret) is not bytes or len(self.secret)!=32 or type(self.expires) is not int or self.active is not True or type(now) is not int or now<0 or now>=self.expires:
            raise PermissionError('ephemeral authorized synthetic subscription required')


def event_body(event):
    if not isinstance(event,dict) or set(event)!={'eventId','name','timestamp','data'} or event['name'] not in EVENTS or not isinstance(event['data'],dict):
        raise ProtocolError('invalid shadow MCP event shape')
    identifier(event['eventId'])
    at=datetime.fromisoformat(event['timestamp'].replace('Z','+00:00'))
    if at.tzinfo is None:
        raise ProtocolError('timezone required')
    d=event['data']
    expected=({'task_id','correlation_id','state','evidence'} if event['name']=='dmb.shadow.result' else {'request_id','task_id','correlation_id','scope_digest','category','summary','simulation'})
    if set(d)!=expected:
        raise ProtocolError('fixed shadow payload required; approvals/commands forbidden')
    for key in ('task_id','correlation_id'):identifier(d[key])
    if event['name']=='dmb.shadow.result':
        if d['state'] not in ('SUCCEEDED','FAILED') or not isinstance(d['evidence'],dict):raise ProtocolError('invalid result')
    else:
        identifier(d['request_id'])
        if d['simulation'] is not True or d['category'] not in ('APPROVAL','CONTROL_PLANE_DEGRADED') or not isinstance(d['summary'],str) or not isinstance(d['scope_digest'],str) or len(d['scope_digest'])!=64 or any(c not in '0123456789abcdef' for c in d['scope_digest']):
            raise ProtocolError('invalid shadow notification')
    body=canonical(event).encode()
    if len(body)>MAX_BYTES:raise ProtocolError('event exceeds official 256 KiB bound')
    return body


def signature(secret,event_id,signed_at,body):
    # Standard Webhooks v1: event ID, timestamp, exact bytes; base64 HMAC-SHA256.
    message=event_id.encode()+b'.'+str(signed_at).encode()+b'.'+body
    return 'v1,'+base64.b64encode(hmac.digest(secret,message,'sha256')).decode()


def headers(subscription,body,now):
    subscription.check(now)
    event=json.loads(body)
    event_body(event)
    if event['name']!=subscription.event_name:
        raise ProtocolError('wrong event subscription or altered bytes')
    return {'Content-Type':'application/json','webhook-id':event['eventId'],'webhook-timestamp':str(now),'webhook-signature':signature(subscription.secret,event['eventId'],now,body),'X-MCP-Subscription-Id':subscription.subscription_id}


@dataclass(frozen=True)
class ShadowReceipt:
    event_id: str
    principal: str
    body_sha256: str
    fresh: bool
    simulation: bool = True
    approval: bool = False


class EventContractLab:
    def __init__(self,store):
        self.store=store
        with store.tx():
            marker=store.db.execute("SELECT value FROM meta WHERE key='event_contract_lab'").fetchone()
            if marker is None:
                store.db.execute("INSERT INTO meta VALUES ('event_contract_lab','LOCAL_EPHEMERAL_ONLY_v1')")
                store.db.execute('CREATE TABLE event_lab_outbox(id TEXT,subscription TEXT,body BLOB,digest TEXT,state TEXT,attempts INTEGER,next_at INTEGER,lease INTEGER,PRIMARY KEY(id,subscription))')
                store.db.execute('CREATE TABLE event_lab_bindings(subscription TEXT PRIMARY KEY,principal TEXT,event_name TEXT,expires INTEGER)')
                store.db.execute('CREATE TABLE event_lab_receipts(id TEXT,subscription TEXT,digest TEXT,principal TEXT,received_at INTEGER,PRIMARY KEY(id,subscription))')
            elif marker[0]!='LOCAL_EPHEMERAL_ONLY_v1':raise ProtocolError('event lab schema mismatch')

    def _binding(self,subscription,register=False):
        row=self.store.db.execute('SELECT * FROM event_lab_bindings WHERE subscription=?',(subscription.subscription_id,)).fetchone()
        expected=(subscription.principal,subscription.event_name,subscription.expires)
        if row is None:
            if not register:raise PermissionError('unregistered shadow subscription')
            self.store.db.execute('INSERT INTO event_lab_bindings VALUES (?,?,?,?)',(subscription.subscription_id,*expected))
        elif (row['principal'],row['event_name'],row['expires'])!=expected:
            raise PermissionError('subscription scope rebound; explicit new binding required')

    def enqueue(self,event,subscription,now):
        body=event_body(event);subscription.check(now)
        if event['name']!=subscription.event_name:raise ProtocolError('wrong subscription event')
        digest=hashlib.sha256(body).hexdigest();s=self.store
        with s.tx():
            self._binding(subscription,register=True)
            prior=s.db.execute('SELECT * FROM event_lab_outbox WHERE id=? AND subscription=?',(event['eventId'],subscription.subscription_id)).fetchone()
            if prior:
                if prior['digest']!=digest or prior['subscription']!=subscription.subscription_id:raise ProtocolError('event identity conflict')
                return False
            s.db.execute('INSERT INTO event_lab_outbox VALUES (?,?,?,?,?,0,?,NULL)',(event['eventId'],subscription.subscription_id,body,digest,'QUEUED',now))
            s.audit('event-lab','enqueue',{'id':event['eventId'],'digest':digest,'simulation':True},now)
        return True

    def claim(self,subscription,now):
        subscription.check(now);s=self.store
        with s.tx():
            self._binding(subscription)
            row=s.db.execute("SELECT * FROM event_lab_outbox WHERE subscription=? AND (state='QUEUED' OR (state='RETRY_WAIT' AND next_at<=?)) ORDER BY rowid LIMIT 1",(subscription.subscription_id,now)).fetchone()
            if row is None:return None
            body=bytes(row['body'])
            if hashlib.sha256(body).hexdigest()!=row['digest']:raise ProtocolError('outbox integrity failure')
            fence=row['attempts']+1
            if fence>3:raise ProtocolError('attempt budget exhausted')
            s.db.execute("UPDATE event_lab_outbox SET state='RUNNING',attempts=?,lease=? WHERE id=? AND subscription=?",(fence,now+10,row['id'],subscription.subscription_id))
            s.audit('event-lab','claim',{'id':row['id'],'subscription':subscription.subscription_id,'attempt':fence},now)
        return {'event_id':row['id'],'subscription_id':subscription.subscription_id,'fence':fence,'body':body,'headers':headers(subscription,body,now),'simulation':True}

    def response(self,claim,status,now):
        if type(status) is not int or not 100<=status<=599:raise ProtocolError('HTTP result required')
        s=self.store
        with s.tx():
            row=s.db.execute('SELECT * FROM event_lab_outbox WHERE id=? AND subscription=?',(claim['event_id'],claim['subscription_id'])).fetchone()
            if row is None or row['state']!='RUNNING' or row['attempts']!=claim['fence'] or now>=row['lease']:
                raise ProtocolError('stale delivery fence')
            if 200<=status<300:state='ACKNOWLEDGED'
            elif status in (408,429) or 500<=status<600:state='RETRY_WAIT' if row['attempts']<3 else 'FAILED'
            else:state='PERMANENT_FAILURE'
            s.db.execute('UPDATE event_lab_outbox SET state=?,next_at=?,lease=NULL WHERE id=? AND subscription=?',(state,now+2**row['attempts'],row['id'],row['subscription']))
            s.audit('event-lab','response',{'id':row['id'],'subscription':row['subscription'],'status':status,'state':state,'approval':False},now)
        return state

    def recover(self,now):
        s=self.store
        with s.tx():
            for row in list(s.db.execute("SELECT id,subscription FROM event_lab_outbox WHERE state='RUNNING' AND lease<=?",(now,))):
                s.db.execute("UPDATE event_lab_outbox SET state='AMBIGUOUS' WHERE id=? AND subscription=?",(row['id'],row['subscription']))
                s.audit('event-lab','uncertain_delivery',{'id':row['id'],'subscription':row['subscription'],'automatic_retry':False},now)

    def receive(self,subscription,body,provided,now):
        subscription.check(now)
        if type(body) is not bytes or len(body)>MAX_BYTES or not isinstance(provided,dict):raise ProtocolError('bounded raw body/headers required')
        if provided.get('X-MCP-Subscription-Id')!=subscription.subscription_id:raise PermissionError('wrong subscription route')
        timestamp=provided.get('webhook-timestamp','')
        if not isinstance(timestamp,str) or not timestamp.isascii() or not timestamp.isdigit() or len(timestamp)>12 or abs(now-int(timestamp))>300:
            raise PermissionError('stale/future signed timestamp')
        event_id=provided.get('webhook-id','');identifier(event_id)
        expected=signature(subscription.secret,event_id,int(timestamp),body)
        supplied=provided.get('webhook-signature','')
        if not isinstance(supplied,str) or not supplied.isascii() or len(supplied)>1024 or not any(hmac.compare_digest(expected,part) for part in supplied.split()):raise PermissionError('invalid webhook authentication')
        event=json.loads(body)
        event_body(event)
        if event['eventId']!=event_id or event['name']!=subscription.event_name:raise ProtocolError('signed event identity/schema mismatch')
        digest=hashlib.sha256(body).hexdigest();s=self.store
        with s.tx():
            self._binding(subscription,register=True)
            prior=s.db.execute('SELECT * FROM event_lab_receipts WHERE id=? AND subscription=?',(event_id,subscription.subscription_id)).fetchone()
            if prior:
                if prior['digest']!=digest or prior['principal']!=subscription.principal:raise ProtocolError('conflicting/rebound event identity')
                return ShadowReceipt(event_id,subscription.principal,digest,False)
            s.db.execute('INSERT INTO event_lab_receipts VALUES (?,?,?,?,?)',(event_id,subscription.subscription_id,digest,subscription.principal,now))
            s.audit('event-lab','signed_receipt',{'id':event_id,'subscription':subscription.subscription_id,'principal':subscription.principal,'digest':digest,'approval':False},now)
        return ShadowReceipt(event_id,subscription.principal,digest,True)
