"""Authenticated bounded supervision over the existing controller. No listener/service.

Separate Brain key, domain and sequence; no worker-key reuse or human approvals.
Uses the controller's AtomicPeerStore so intake/review/follow-up/audit are one commit.
"""
from dataclasses import dataclass, field
import hashlib
import hmac
import json
from dci.bridge.protocol import ProtocolError, canonical, identifier
from .windows_protocol import sha

ACTIONS = {'SUBMIT', 'REVIEW', 'CANCEL', 'PAUSE', 'RESUME', 'REPORT', 'ACK_EVENTS'}
SCOPES = {'SUBMIT': 'intake', 'REVIEW': 'review', 'CANCEL': 'control',
          'PAUSE': 'control', 'RESUME': 'control', 'REPORT': 'report', 'ACK_EVENTS': 'report'}
DOMAIN = b'DMB-OPERATIONS-v1\n'
BANNER = '🔴🔴🔴 HUMAN INPUT REQUIRED — CONTROL PLANE DEGRADED 🔴🔴🔴'


@dataclass(frozen=True)
class BrainIdentity:
    principal: str
    key_id: str
    expires: int
    scopes: frozenset
    secret: bytes = field(repr=False)

    def check(self, now):
        identifier(self.principal); identifier(self.key_id)
        if type(now) is not int or type(self.expires) is not int or now >= self.expires or type(self.secret) is not bytes or len(self.secret) != 32:
            raise PermissionError('Invalid/expired dedicated Brain identity')
        if type(self.scopes) is not frozenset or not self.scopes <= set(SCOPES.values()):
            raise PermissionError('Unknown Brain scope; no approval authority')


def semantic(packet):
    return {k: v for k, v in packet.items() if k not in {'issued_at', 'expires_at', 'mac'}}


def signed(identity, action, payload, sequence, message_id, now, reply=False):
    identity.check(now)
    packet = {'version': 1, 'principal': identity.principal, 'key_id': identity.key_id,
              'direction': 'controller_to_brain' if reply else 'brain_to_controller',
              'sequence': sequence, 'message_id': message_id, 'action': action,
              'issued_at': now, 'expires_at': min(now + 60, identity.expires), 'payload': payload}
    packet['mac'] = hmac.digest(identity.secret, DOMAIN + canonical(packet).encode(), 'sha256').hex()
    return packet


def authenticated(identity, packet, now, reply=False):
    identity.check(now)
    fields = {'version', 'principal', 'key_id', 'direction', 'sequence', 'message_id',
              'action', 'issued_at', 'expires_at', 'payload', 'mac'}
    if type(packet) is not dict or set(packet) != fields or len(canonical(packet).encode()) > 131072:
        raise ProtocolError('Exact bounded operations envelope required')
    identifier(packet['message_id'])
    if type(packet['version']) is not int or packet['version'] != 1 or packet['principal'] != identity.principal or packet['key_id'] != identity.key_id or packet['direction'] != ('controller_to_brain' if reply else 'brain_to_controller'):
        raise PermissionError('Wrong authenticated operations route')
    if type(packet['sequence']) is not int or packet['sequence'] < 1 or type(packet['issued_at']) is not int or type(packet['expires_at']) is not int or not now < packet['expires_at'] <= min(packet['issued_at'] + 60, identity.expires) or packet['issued_at'] > now + 30:
        raise PermissionError('Stale/out-of-order operations envelope')
    if type(packet['payload']) is not dict or packet['action'] not in (ACTIONS | {'ACK'} if reply else ACTIONS):
        raise ProtocolError('Allowlisted operations action required; no shell/prompts/approvals')
    if not reply and SCOPES[packet['action']] not in identity.scopes:
        raise PermissionError('Brain identity lacks action scope')
    body = {k: v for k, v in packet.items() if k != 'mac'}
    expected = hmac.digest(identity.secret, DOMAIN + canonical(body).encode(), 'sha256').hex()
    if type(packet['mac']) is not str or not hmac.compare_digest(packet['mac'], expected):
        raise PermissionError('Operations authentication failed')
    return sha(semantic(packet))


class Operations:
    def __init__(self, controller, identity):
        from .windows_controller import AtomicPeerStore
        self.controller, self.store, self.identity = controller, controller.store, identity
        if not isinstance(self.store, AtomicPeerStore): raise ProtocolError('Dedicated atomic controller required')
        # Worker/controller and Brain credentials must be independently scoped.
        if hasattr(controller, 'key') and hmac.compare_digest(controller.key.secret, identity.secret):
            raise PermissionError('Worker pairing key cannot authenticate Brain')
        binding = sha({'principal': identity.principal, 'key_id': identity.key_id,
                       'expires': identity.expires, 'scopes': sorted(identity.scopes),
                       'key_fingerprint': hashlib.sha256(identity.secret).hexdigest(),
                       'controller_kind': type(controller).__name__})
        with self.store.tx():
            old = self.store.db.execute("SELECT value FROM meta WHERE key='dmb_operations_v1'").fetchone()
            if old is None:
                self.store.db.execute('CREATE TABLE ops_requests(seq INTEGER PRIMARY KEY,id TEXT UNIQUE,digest TEXT,response TEXT)')
                self.store.db.execute('CREATE TABLE ops_reviews(task TEXT PRIMARY KEY,scope TEXT,result_digest TEXT,state TEXT,followup TEXT)')
                self.store.db.execute('CREATE TABLE ops_events(seq INTEGER PRIMARY KEY,event_id TEXT UNIQUE,body TEXT,ack INTEGER DEFAULT 0)')
                self.store.db.execute('CREATE TABLE ops_roots(task TEXT PRIMARY KEY,root TEXT,depth INTEGER)')
                self.store.db.execute("INSERT INTO meta VALUES ('dmb_operations_v1',?)", (binding,))
            elif old[0] != binding: raise PermissionError('Operations key/backend drift; no silent rebinding')

    def event(self, kind, task, payload, now):
        body = {'version': 1, 'type': kind, 'task_id': task, 'payload': payload}
        event_id = sha(body)
        if not self.store.db.execute('SELECT 1 FROM ops_events WHERE event_id=?', (event_id,)).fetchone():
            sequence = self.store.db.execute('SELECT coalesce(max(seq),0)+1 FROM ops_events').fetchone()[0]
            self.store.db.execute('INSERT INTO ops_events(seq,event_id,body) VALUES (?,?,?)', (sequence, event_id, canonical(body)))
            self.store.audit('operations', kind, {'task': task, 'event_id': event_id}, now)

    def collect(self, now):
        with self.store.tx():
            self.store.verify_audit()
            for row in self.store.db.execute('SELECT task FROM ops_roots ORDER BY rowid').fetchall():
                task = self.controller._job(row['task'])
                if task['state'] in {'SUCCEEDED', 'FAILED', 'CANCELLED', 'NEEDS_HUMAN', 'HUMAN_TIMEOUT', 'REJECTED'}:
                    digest = sha(json.loads(task['result'])) if task['result'] else sha(None)
                    if task['state'] == 'SUCCEEDED':
                        self.store.db.execute("INSERT OR IGNORE INTO ops_reviews VALUES (?,?,?,'PENDING',NULL)", (task['id'], task['scope_digest'], digest))
                        kind, details = 'REVIEW_REQUIRED', {'scope_digest': task['scope_digest'], 'result_digest': digest}
                    elif task['state'] == 'FAILED' and task['result'] and (json.loads(task['result']).get('cancelled') is True or json.loads(task['result']).get('remote_report', {}).get('status') == 'CANCELLED'):
                        kind, details = 'CANCELLED', {'state': task['state'], 'result_digest': digest}
                    else:
                        kind, details = 'NEEDS_HUMAN', {'state': task['state'], 'scope_digest': task['scope_digest'], 'result_digest': digest, 'category': 'CONTROL_PLANE_DEGRADATION', 'banner': BANNER, 'approval_inferred': False}
                    self.event(kind, task['id'], details, now)

    def _review(self, payload, now):
        if set(payload) - {'task_id', 'scope_digest', 'result_digest', 'verdict', 'followup'} or not {'task_id', 'scope_digest', 'result_digest', 'verdict'} <= set(payload) or payload['verdict'] not in {'ACCEPT', 'ESCALATE'}:
            raise ProtocolError('Exact evidence-bound review required')
        row = self.store.db.execute('SELECT * FROM ops_reviews WHERE task=?', (payload['task_id'],)).fetchone()
        task = self.controller._job(payload['task_id'])
        if row is None or row['state'] != 'PENDING' or row['scope'] != payload['scope_digest'] or row['result_digest'] != payload['result_digest'] or task['state'] != 'SUCCEEDED' or sha(json.loads(task['result'])) != row['result_digest']:
            raise ProtocolError('Review scope/result changed, pending evidence absent or already reviewed')
        if payload['verdict'] == 'ESCALATE':
            if 'followup' in payload: raise ProtocolError('Escalation cannot authorize follow-up')
            self.event('NEEDS_HUMAN', task['id'], {'category': 'SUPERVISORY_EXCEPTION', 'approval_inferred': False}, now)
        child = payload.get('followup')
        if child is not None:
            parent = self.store.db.execute('SELECT root,depth FROM ops_roots WHERE task=?', (task['id'],)).fetchone()
            count = self.store.db.execute('SELECT count(*) FROM ops_roots WHERE root=?', (parent['root'],)).fetchone()[0]
            if type(child) is not dict or child.get('dependencies') != [task['id']] or child.get('project_id') != 'DCI' or parent['depth'] >= 3 or count >= 10 or self.store.db.execute('SELECT 1 FROM tasks WHERE id=?', (child.get('task_id'),)).fetchone():
                raise PermissionError('Follow-up must be new, bounded and dependent on reviewed completion')
            self.controller.submit(child, now)
            self.store.db.execute('INSERT INTO ops_roots VALUES (?,?,?)', (child['task_id'], parent['root'], parent['depth'] + 1))
        self.store.db.execute('UPDATE ops_reviews SET state=?,followup=? WHERE task=?', ('NEEDS_HUMAN' if payload['verdict'] == 'ESCALATE' else 'ACCEPT', child.get('task_id') if child else None, task['id']))
        self.event('REVIEWED', task['id'], {'verdict': payload['verdict'], 'followup': child.get('task_id') if child else None}, now)
        return {'reviewed': task['id'], 'verdict': payload['verdict'], 'followup': child.get('task_id') if child else None}

    def _apply(self, action, payload, now):
        if action == 'SUBMIT':
            if self.store.db.execute('SELECT count(*) FROM ops_roots').fetchone()[0] >= 100:
                raise PermissionError('Operations intake budget reached; no unbounded task creation')
            task = payload.get('task_id')
            if self.store.db.execute('SELECT 1 FROM tasks WHERE id=?', (task,)).fetchone() and not self.store.db.execute('SELECT 1 FROM ops_roots WHERE task=?', (task,)).fetchone():
                raise PermissionError('Cannot adopt a task outside this operations scope')
            result = self.controller.submit(payload, now)
            self.store.db.execute('INSERT OR IGNORE INTO ops_roots VALUES (?,?,0)', (task, task))
            self.event('ACCEPTED', task, {'correlation_id': payload['correlation_id']}, now)
            return result
        if action == 'REVIEW': return self._review(payload, now)
        if action == 'CANCEL':
            if set(payload) != {'task_id'}: raise ProtocolError('Owned task cancellation only')
            if not self.store.db.execute('SELECT 1 FROM ops_roots WHERE task=?', (payload['task_id'],)).fetchone():
                raise PermissionError('Cancellation outside operations scope rejected')
            return self.controller.cancel(payload['task_id'], now)
        if action in {'PAUSE', 'RESUME'}:
            if payload: raise ProtocolError('Control parameters forbidden')
            from dci.bridge.brain import BrainTools
            return BrainTools(self.store).control(action, now)
        if action == 'ACK_EVENTS':
            if set(payload) != {'events'} or type(payload['events']) is not list or not 1 <= len(payload['events']) <= 100:
                raise ProtocolError('Exact event IDs required; delivery acknowledgement is not approval')
            for event_id in payload['events']:
                if type(event_id) is not str or not self.store.db.execute('SELECT 1 FROM ops_events WHERE event_id=?', (event_id,)).fetchone():
                    raise ProtocolError('Unknown event acknowledgement')
                self.store.db.execute('UPDATE ops_events SET ack=1 WHERE event_id=?', (event_id,))
            return {'delivery_acknowledged': len(payload['events']), 'human_approval': False}
        if payload: raise ProtocolError('Report parameters forbidden')
        self.collect(now)
        return {'mode': 'SHADOW', 'audit_valid': True,
                'events': [{'sequence': r['seq'], 'event_id': r['event_id'], 'event': json.loads(r['body'])} for r in self.store.db.execute('SELECT * FROM ops_events WHERE ack=0 ORDER BY seq LIMIT 100')],
                'reviews': [dict(r) for r in self.store.db.execute("SELECT * FROM ops_reviews WHERE state='PENDING' ORDER BY rowid LIMIT 100")],
                'needs_human': [dict(r) for r in self.store.db.execute("SELECT * FROM ops_reviews WHERE state='NEEDS_HUMAN' ORDER BY rowid LIMIT 100")],
                'held_resources': [dict(r) for r in self.store.db.execute('SELECT * FROM master_locks')],
                'external_notifications': 'DISABLED', 'human_approval_authority': False}

    def handle(self, packet, now):
        digest = authenticated(self.identity, packet, now)
        with self.store.tx():
            previous = self.store.db.execute('SELECT * FROM ops_requests WHERE seq=? OR id=?', (packet['sequence'], packet['message_id'])).fetchone()
            if previous:
                if previous['seq'] != packet['sequence'] or previous['id'] != packet['message_id'] or previous['digest'] != digest:
                    raise ProtocolError('Replayed/rebound operations request')
                result = json.loads(previous['response'])
            else:
                maximum = self.store.db.execute('SELECT coalesce(max(seq),0) FROM ops_requests').fetchone()[0]
                if packet['sequence'] != maximum + 1: raise ProtocolError('Operations sequence gap/replay')
                result = self._apply(packet['action'], packet['payload'], now)
                self.store.db.execute('INSERT INTO ops_requests VALUES (?,?,?,?)', (packet['sequence'], packet['message_id'], digest, canonical(result)))
                self.store.audit(self.identity.principal, 'authenticated_operations', {'action': packet['action'], 'message_id': packet['message_id'], 'digest': digest}, now)
        return signed(self.identity, 'ACK', {'request_id': packet['message_id'], 'request_digest': digest, 'result': result}, packet['sequence'], packet['message_id'], now, reply=True)
