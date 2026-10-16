"""Durable outbound-only Brain client. HTTPS activation requires an approved host.

No provider/service provisioning. Fresh in-memory keys in tests are not human
identity certification. Persistent deployments must supply separately scoped keys.
"""
import json
import ssl
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from uuid import uuid4
from dci.bridge.protocol import ProtocolError, canonical
from .windows_protocol import sha
from .windows_worker import NoRedirect
from .operations import signed, authenticated, semantic


class OperationsHTTPS:
    def __init__(self, url, ca_file=None):
        p = urlsplit(url)
        if p.scheme != 'https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path != '/v1/dmb/operations':
            raise PermissionError('Exact approved operations HTTPS endpoint required')
        self.url = url
        context = ssl.create_default_context()
        if ca_file: context.load_verify_locations(cafile=ca_file)
        self.opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))

    def __call__(self, packet):
        request = urllib.request.Request(self.url, canonical(packet).encode(), {'Content-Type': 'application/json'}, method='POST')
        with self.opener.open(request, timeout=10) as response:
            if response.status != 200: raise PermissionError('Operations delivery not acknowledged')
            raw = response.read(131073)
        if len(raw) > 131072: raise ProtocolError('Oversized operations reply')
        return json.loads(raw)


class OperationsClient:
    def __init__(self, store, identity, transport):
        self.store, self.identity, self.transport = store, identity, transport
        binding = sha({'principal': identity.principal, 'key_id': identity.key_id,
                       'fingerprint': __import__('hashlib').sha256(identity.secret).hexdigest(),
                       'expires': identity.expires, 'scopes': sorted(identity.scopes)})
        with store.tx():
            old = store.db.execute("SELECT value FROM meta WHERE key='operations_client_v1'").fetchone()
            if old is None:
                store.db.execute('CREATE TABLE ops_outbox(seq INTEGER PRIMARY KEY,id TEXT UNIQUE,action TEXT,payload TEXT,ack TEXT)')
                store.db.execute("INSERT INTO meta VALUES ('operations_client_v1',?)", (binding,))
            elif old[0] != binding: raise PermissionError('Client identity drift; preserve outbox')

    def recover(self, now=None):
        row = self.store.db.execute('SELECT * FROM ops_outbox WHERE ack IS NULL ORDER BY seq LIMIT 1').fetchone()
        return self._send(row, now) if row else None

    def _send(self, row, now=None):
        clock = (lambda: int(time.time())) if now is None else (lambda: now)
        for attempt in range(3):
            timestamp = clock()
            packet = signed(self.identity, row['action'], json.loads(row['payload']), row['seq'], row['id'], timestamp)
            # Validate locally before any network side effect.
            digest = authenticated(self.identity, packet, timestamp)
            try:
                reply = self.transport(packet)
            except urllib.error.HTTPError as error:
                if error.code < 500 or attempt == 2: raise
                continue
            except (TimeoutError, ConnectionError, urllib.error.URLError) as error:
                if isinstance(getattr(error, 'reason', None), ssl.SSLError) or attempt == 2: raise
                continue
            authenticated(self.identity, reply, clock(), reply=True)
            value = reply['payload']
            if reply['action'] != 'ACK' or reply['sequence'] != row['seq'] or reply['message_id'] != row['id'] or set(value) != {'request_id', 'request_digest', 'result'} or value['request_id'] != row['id'] or value['request_digest'] != digest:
                raise PermissionError('Uncorrelated operations acknowledgement')
            with self.store.tx():
                self.store.db.execute('UPDATE ops_outbox SET ack=? WHERE seq=? AND ack IS NULL', (canonical(reply), row['seq']))
                self.store.audit('brain-outbound', 'operations_ack', {'message_id': row['id'], 'digest': digest}, clock())
            return value['result']
        raise ConnectionError('Delivery exhausted; durable pending message retained')

    def request(self, action, payload, now=None):
        pending = self.store.db.execute('SELECT * FROM ops_outbox WHERE ack IS NULL LIMIT 1').fetchone()
        if pending:
            if pending['action'] != action or pending['payload'] != canonical(payload):
                raise ProtocolError('Recover pending request before new operations')
            return self._send(pending, now)
        with self.store.tx():
            seq = self.store.db.execute('SELECT coalesce(max(seq),0)+1 FROM ops_outbox').fetchone()[0]
            self.store.db.execute('INSERT INTO ops_outbox VALUES (?,?,?,?,NULL)', (seq, str(uuid4()), action, canonical(payload)))
        return self.recover(now)
