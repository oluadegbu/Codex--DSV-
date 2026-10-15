"""Controller pulls an approved HTTPS relay; neither Windows nor controller listens.

Relay carrier key is separate from end-to-end Brain and worker keys. Provider
activation remains disabled until host, pairing and persistence are approved.
"""
import hmac
import json
from dci.bridge.protocol import ProtocolError, canonical
from .operations import signed, BANNER
from .operations_client import OperationsClient
from .windows_protocol import sha


class OutboundRelayPump:
    def __init__(self, operations, carrier_identity, transport):
        self.ops, self.store, self.carrier = operations, operations.store, carrier_identity
        if carrier_identity.scopes != frozenset({'report'}) or hmac.compare_digest(carrier_identity.secret, operations.identity.secret) or (hasattr(operations.controller, 'key') and hmac.compare_digest(carrier_identity.secret, operations.controller.key.secret)):
            raise PermissionError('Separate report-only relay carrier identity required')
        self.client = OperationsClient(self.store, carrier_identity, transport)
        with self.store.tx():
            self.store.db.execute('CREATE TABLE IF NOT EXISTS ops_relay_replies(route TEXT,id TEXT,digest TEXT,body TEXT,ack INTEGER DEFAULT 0,PRIMARY KEY(route,id))')
            self.store.db.execute("INSERT OR IGNORE INTO meta VALUES ('ops_relay_applied_seq','0')")

    def _apply_received(self, now):
        cursor = int(self.store.db.execute("SELECT value FROM meta WHERE key='ops_relay_applied_seq'").fetchone()[0])
        rows = self.store.db.execute('SELECT seq,ack FROM ops_outbox WHERE ack IS NOT NULL AND seq>? ORDER BY seq', (cursor,)).fetchall()
        for row in rows:
            value = json.loads(row['ack'])['payload']['result']
            if type(value) is not dict or set(value) != {'requests', 'accepted_replies'} or type(value['requests']) is not list or len(value['requests']) > 10 or type(value['accepted_replies']) is not list or len(value['accepted_replies']) > 10:
                raise ProtocolError('Exact bounded relay batch required')
            with self.store.tx():
                # The carrier ACK was durable before this point. A crash here
                # replays the batch from that ACK and existing authority dedup.
                for ack in value['accepted_replies']:
                    if type(ack) is not dict or set(ack) != {'route', 'id', 'digest'}:
                        raise ProtocolError('Exact relay receipt required')
                    old = self.store.db.execute('SELECT digest FROM ops_relay_replies WHERE route=? AND id=?', (ack['route'], ack['id'])).fetchone()
                    if old is None or old[0] != ack['digest']: raise PermissionError('Unknown relay receipt; never infer approval')
                    self.store.db.execute('UPDATE ops_relay_replies SET ack=1 WHERE route=? AND id=?', (ack['route'], ack['id']))
                for item in value['requests']:
                    if type(item) is not dict or set(item) != {'route', 'packet'} or item['route'] not in {'brain', 'windows'}:
                        raise ProtocolError('Allowlisted relay route required')
                    packet = item['packet']
                    if item['route'] == 'brain': response = self.ops.handle(packet, now)
                    elif hasattr(self.ops.controller, 'receive'): response = self.ops.controller.receive(packet, now)
                    else: raise PermissionError('No Windows route on paper backend')
                    digest = sha({k: v for k, v in response.items() if k not in {'issued_at', 'sent_at', 'expires_at', 'mac'}})
                    previous = self.store.db.execute('SELECT digest FROM ops_relay_replies WHERE route=? AND id=?', (item['route'], packet['message_id'])).fetchone()
                    if previous and previous[0] != digest: raise ProtocolError('Relay response identity rebound')
                    self.store.db.execute('INSERT INTO ops_relay_replies(route,id,digest,body) VALUES (?,?,?,?) ON CONFLICT(route,id) DO UPDATE SET body=excluded.body,ack=0', (item['route'], packet['message_id'], digest, canonical(response)))
                self.store.db.execute("UPDATE meta SET value=? WHERE key='ops_relay_applied_seq'", (str(row['seq']),))
                self.store.audit('outbound-relay', 'batch_applied', {'sequence': row['seq'], 'requests': len(value['requests']), 'human_approval': False}, now)

    def pump(self, now):
        try:
            return self._pump(now)
        except Exception as error:
            with self.store.tx():
                self.ops.event('NEEDS_HUMAN', 'control-plane', {
                    'category': 'CONTROL_PLANE_DEGRADATION', 'banner': BANNER,
                    'reason': type(error).__name__, 'approval_inferred': False,
                    'pending_messages_retained': True}, now)
            raise

    def _pump(self, now):
        self._apply_received(now)
        pending = self.store.db.execute('SELECT 1 FROM ops_outbox WHERE ack IS NULL').fetchone()
        if pending:
            self.client.recover(now)
        else:
            replies = []
            for row in self.store.db.execute('SELECT * FROM ops_relay_replies WHERE ack=0 ORDER BY rowid LIMIT 10'):
                old = json.loads(row['body'])
                if row['route'] == 'brain':
                    packet = signed(self.ops.identity, 'ACK', old['payload'], old['sequence'], old['message_id'], now, reply=True)
                else:
                    from .windows_protocol import sign
                    packet = sign(self.ops.controller.key, 'controller_to_worker', 'REPLY', old['sequence'], old['payload'], now, old['message_id'])
                replies.append({'route': row['route'], 'id': row['id'], 'digest': row['digest'], 'packet': packet})
            self.client.request('REPORT', {'role': 'controller', 'replies': replies, 'max_requests': 10}, now)
        self._apply_received(now)
        self.ops.collect(now)
        return {'mode': 'SHADOW', 'inbound_listener': False,
                'unacknowledged_replies': self.store.db.execute('SELECT count(*) FROM ops_relay_replies WHERE ack=0').fetchone()[0],
                'human_approval': False}
