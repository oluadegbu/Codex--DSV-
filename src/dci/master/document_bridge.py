"""DDB v1: signed documents over an atomic branch; no daemon or remote shell.

Reuse AtomicPeerStore, audit and fixed Operations/runtime authority. GitHub is a
carrier, not a human approver. Private Ed25519 signing keys never cross roles.
"""
import hashlib
import json
import re
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from dci.bridge.protocol import ProtocolError, canonical, identifier
from .windows_controller import AtomicPeerStore
from .windows_protocol import sha

BRANCH = 'coordination/dmb-ddb-v1'
DOMAIN = b'DIRECTIVE-DDB-v1\n'
KINDS = {'supervisor': {'DIRECTIVE', 'COMPLETE'}, 'worker': {'REPORT', 'ACK', 'HEARTBEAT'}}
CADENCE = {'watch': 180, 'supervisor': 300, 'worker': 300}
ZERO = '0' * 64
LIMIT = 32768


def exact(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ProtocolError('Exact DDB fields required')


def hexvalue(value, length=64):
    if type(value) is not str or not re.fullmatch('[0-9a-f]{'+str(length)+'}', value):
        raise ProtocolError('Invalid DDB digest')


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ProtocolError('Bounded DDB integer required')


@dataclass(frozen=True)
class Policy:
    body: dict
    approved_sha256: str

    def __post_init__(self):
        exact(self.body, {'version', 'mode', 'policy_id', 'expires', 'max_tasks', 'template',
                          'report_max_age', 'document_ttl', 'worker_id', 'worker_key_id', 'signers'})
        if sha(self.body) != self.approved_sha256 or type(self.body['version']) is not int or self.body['version'] != 1 or self.body['mode'] != 'SHADOW':
            raise PermissionError('Exact out-of-band human-approved policy pin required')
        for k in ('policy_id', 'worker_id', 'worker_key_id'): identifier(self.body[k])
        integer(self.body['expires'], 1, 2**53)
        integer(self.body['max_tasks'], 1, 10)
        integer(self.body['report_max_age'], 300, 900)
        integer(self.body['document_ttl'], 600, 900)
        if self.body['template'] != 'shadow_research':
            raise PermissionError('Only existing fixed DCI paper-research template enabled')
        exact(self.body['signers'], {'supervisor', 'worker'})
        for public in self.body['signers'].values(): hexvalue(public)
        if len(set(self.body['signers'].values())) != 2: raise PermissionError('Separate role keys required')

    def check(self, now):
        integer(now, 1, 2**53)
        if sha(self.body) != self.approved_sha256: raise PermissionError('Policy changed after pin validation')
        if now >= self.body['expires']: raise PermissionError('DDB policy expired')


def validate_body(kind, body):
    if kind == 'DIRECTIVE':
        exact(body, {'directive_id', 'task_id', 'correlation_id', 'template', 'source_report'})
        for k in ('directive_id', 'task_id', 'correlation_id'): identifier(body[k])
        if body['template'] != 'shadow_research': raise PermissionError('Unapproved DDB template')
        hexvalue(body['source_report'])
    elif kind == 'REPORT':
        exact(body, {'effort_id', 'directive_id', 'task_id', 'status', 'evidence'})
        identifier(body['effort_id'])
        if body['status'] not in {'IDLE', 'SUCCEEDED', 'NEEDS_HUMAN'}: raise ProtocolError('Unsupported report state')
        if body['status'] == 'IDLE':
            if any(body[k] is not None for k in ('directive_id', 'task_id', 'evidence')): raise ProtocolError('Invalid idle report')
        else:
            identifier(body['directive_id']); identifier(body['task_id'])
            if body['status'] == 'NEEDS_HUMAN':
                if body['evidence'] != {'category': 'EXECUTION_UNCERTAIN'}: raise ProtocolError('Sanitized failure only')
            else:
                exact(body['evidence'], {'kind', 'scope_digest', 'result_digest', 'artifact_sha256', 'git_commit', 'audit_valid', 'exit_code'})
                e = body['evidence']
                for k in ('scope_digest', 'result_digest', 'artifact_sha256'): hexvalue(e[k])
                hexvalue(e['git_commit'], 40)
                if e['kind'] != 'VERIFIED_LOCAL_PAPER' or e['audit_valid'] is not True or type(e['exit_code']) is not int or e['exit_code'] != 0:
                    raise PermissionError('Verified bounded shadow evidence required')
    elif kind == 'COMPLETE':
        exact(body, {'directive_id', 'report_digest', 'verdict'})
        identifier(body['directive_id']); hexvalue(body['report_digest'])
        if body['verdict'] != 'ACCEPT_ATTESTED_SHADOW': raise ProtocolError('No human approval authority')
    elif kind == 'ACK':
        exact(body, {'directive_id', 'directive_digest', 'state'})
        identifier(body['directive_id']); hexvalue(body['directive_digest'])
        if body['state'] != 'DURABLY_RECEIVED': raise ProtocolError('Delivery is not approval')
    elif kind == 'HEARTBEAT':
        exact(body, {'state'})
        if body['state'] not in {'IDLE', 'BUSY', 'BLOCKED'}: raise ProtocolError('Invalid heartbeat')
    else: raise ProtocolError('Unknown document kind')


def validate_document(doc, policy, now, historical=False):
    policy.check(now)
    exact(doc, {'version', 'mode', 'id', 'role', 'sequence', 'previous', 'issued_at', 'expires_at',
                'policy_sha256', 'kind', 'body', 'content_sha256', 'signature'})
    if len(canonical(doc).encode()) > LIMIT: raise ProtocolError('Document too large')
    if type(doc['version']) is not int or doc['version'] != 1 or doc['mode'] != 'SHADOW' or doc['policy_sha256'] != policy.approved_sha256:
        raise PermissionError('Wrong document policy/mode')
    identifier(doc['id']); integer(doc['sequence'], 1, 10000)
    hexvalue(doc['previous']); hexvalue(doc['content_sha256']); hexvalue(doc['signature'], 128)
    if doc['role'] not in KINDS or doc['kind'] not in KINDS[doc['role']]: raise PermissionError('Single-writer role violation')
    integer(doc['issued_at'], 1, now + 30)
    integer(doc['expires_at'], doc['issued_at'] + 1, min(doc['issued_at'] + policy.body['document_ttl'], policy.body['expires']))
    if not historical and doc['expires_at'] <= now: raise PermissionError('Stale DDB document')
    validate_body(doc['kind'], doc['body'])
    unsigned = {k: v for k, v in doc.items() if k != 'signature'}
    if sha({k: v for k, v in unsigned.items() if k != 'content_sha256'}) != doc['content_sha256']:
        raise PermissionError('DDB content hash mismatch')
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(policy.body['signers'][doc['role']])).verify(bytes.fromhex(doc['signature']), DOMAIN + canonical(unsigned).encode())
    except InvalidSignature as error: raise PermissionError('DDB signer authentication failed') from error
    return sha(doc)


def document_files(doc):
    """Only compiled JSON destinations; mailbox text cannot choose paths."""
    role, seq, name, kind = doc['role'], doc['sequence'], doc['id'], doc['kind']
    paths = [f'state/events/{role}/{seq:08d}-{name}.json']
    if kind == 'REPORT': paths += [f'reports/history/{name}.json', 'reports/latest.json']
    elif kind == 'DIRECTIVE': paths += [f'directives/pending/{doc["body"]["directive_id"]}.json']
    elif kind == 'COMPLETE': paths += [f'directives/completed/{doc["body"]["directive_id"]}.json']
    elif kind == 'ACK': paths += [f'state/acks/{name}.json']
    else: paths += ['state/heartbeat.json']
    return {p: canonical(doc) for p in paths}


def verified_snapshot(files, policy, now):
    if type(files) is not dict or len(files) > 512: raise ProtocolError('Bounded branch snapshot required')
    streams = {role: [] for role in KINDS}
    for path, raw in files.items():
        if type(raw) is not str or len(raw.encode()) > LIMIT: raise ProtocolError('Bounded JSON documents only')
        if path.startswith('state/events/'):
            doc = json.loads(raw, object_pairs_hook=unique_object)
            validate_document(doc, policy, now, historical=True)
            if path not in document_files(doc): raise PermissionError('Wrong event route')
            streams[doc['role']].append(doc)
    expected = {}
    for role, docs in streams.items():
        docs.sort(key=lambda d: d['sequence']); previous = ZERO
        ids = set()
        for seq, doc in enumerate(docs, 1):
            if doc['sequence'] != seq or doc['previous'] != previous or doc['id'] in ids:
                raise ProtocolError('Missing/replayed/conflicting DDB stream')
            ids.add(doc['id']); previous = sha(doc)
            for path, raw in document_files(doc).items():
                if path in expected and path not in {'reports/latest.json', 'state/heartbeat.json'}:
                    raise ProtocolError('Immutable document overwrite')
                expected[path] = raw
    if files != expected: raise PermissionError('Unowned paths or inconsistent document mirrors')
    return streams


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ProtocolError('Duplicate JSON field')
        result[key] = value
    return result


class DocumentNode:
    def __init__(self, store, role, policy, private_key, transport):
        if not isinstance(store, AtomicPeerStore) or role not in KINDS: raise PermissionError('Existing atomic DMB state required')
        self.store, self.role, self.policy, self.key, self.transport = store, role, policy, private_key, transport
        from cryptography.hazmat.primitives import serialization
        public = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
        if public != policy.body['signers'][role]: raise PermissionError('Signer not pinned to role')
        binding = sha({'role': role, 'policy': policy.approved_sha256})
        with store.tx():
            old = store.db.execute("SELECT value FROM meta WHERE key='ddb_binding_v1'").fetchone()
            if old and old[0] != binding: raise PermissionError('Policy/signer drift; explicit human-reviewed migration required')
            if not old:
                statements = [
                    'CREATE TABLE ddb_outbox(seq INTEGER PRIMARY KEY,id TEXT UNIQUE,body TEXT,published TEXT)',
                    'CREATE TABLE ddb_seen(role TEXT,seq INTEGER,digest TEXT,PRIMARY KEY(role,seq))',
                    'CREATE TABLE ddb_jobs(id TEXT PRIMARY KEY,digest TEXT,body TEXT,state TEXT)',
                    'CREATE TABLE ddb_plan(id TEXT PRIMARY KEY,report TEXT,completed INTEGER DEFAULT 0)',
                    'CREATE TABLE ddb_local_reviews(id TEXT PRIMARY KEY,body TEXT,applied INTEGER DEFAULT 0)',
                    'CREATE TABLE ddb_cadence(name TEXT PRIMARY KEY,last INTEGER)',
                ]
                for sql in statements: store.db.execute(sql)
                store.db.execute("INSERT INTO meta VALUES ('ddb_binding_v1',?)", (binding,))

    def require_open(self):
        if self.store.db.execute("SELECT 1 FROM meta WHERE key='ddb_blocked'").fetchone():
            raise PermissionError('DDB NEEDS_HUMAN; retained evidence requires reconciliation')

    def block(self, now, category='CONTROL_PLANE_DEGRADATION'):
        self.store.verify_audit()
        with self.store.tx():
            detail = {'category': category, 'approval_inferred': False, 'notifications': 'DISABLED'}
            self.store.db.execute("INSERT OR IGNORE INTO meta VALUES ('ddb_blocked',?)", (canonical(detail),))
            request = 'ddb-'+self.role+'-'+self.policy.approved_sha256[:20]
            self.store.db.execute('INSERT OR IGNORE INTO escalations(id,task,scope,expires,category,summary) VALUES (?,?,?,?,?,?)',
                (request, 'ddb-control-plane', self.policy.approved_sha256, self.policy.body['expires'], category, 'DDB halted; review retained signed documents and audit.'))
            self.store.audit('ddb-'+self.role, 'NEEDS_HUMAN', detail, now)

    def enqueue(self, kind, body, doc_id, now):
        self.policy.check(now); identifier(doc_id); validate_body(kind, body)
        if kind not in KINDS[self.role]: raise PermissionError('Wrong document writer')
        with self.store.tx():
            self.store.verify_audit()
            old = self.store.db.execute('SELECT body FROM ddb_outbox WHERE id=?', (doc_id,)).fetchone()
            if old:
                doc = json.loads(old[0])
                if doc['kind'] != kind or doc['body'] != body: raise ProtocolError('Rebound document ID')
                return doc
            last = self.store.db.execute('SELECT seq,body FROM ddb_outbox ORDER BY seq DESC LIMIT 1').fetchone()
            doc = {'version': 1, 'mode': 'SHADOW', 'id': doc_id, 'role': self.role,
                   'sequence': last['seq'] + 1 if last else 1, 'previous': sha(json.loads(last['body'])) if last else ZERO,
                   'issued_at': now, 'expires_at': min(now + self.policy.body['document_ttl'], self.policy.body['expires']),
                   'policy_sha256': self.policy.approved_sha256, 'kind': kind, 'body': body}
            doc['content_sha256'] = sha(doc)
            doc['signature'] = self.key.sign(DOMAIN + canonical(doc).encode()).hex()
            validate_document(doc, self.policy, now)
            self.store.db.execute('INSERT INTO ddb_outbox VALUES (?,?,?,NULL)', (doc['sequence'], doc_id, canonical(doc)))
            self.store.audit('ddb-'+self.role, 'document_queued', {'id': doc_id, 'digest': sha(doc)}, now)
            return doc

    def flush(self, now):
        try:
            return self._flush(now)
        except (PermissionError, ProtocolError, ValueError, KeyError):
            self.block(now)
            raise

    def _flush(self, now):
        """At most 3 CAS attempts per document; unknown publication remains pending."""
        self.policy.check(now); self.store.verify_audit()
        rows = self.store.db.execute('SELECT * FROM ddb_outbox WHERE published IS NULL ORDER BY seq LIMIT 10').fetchall()
        for row in rows:
            doc = json.loads(row['body'])
            for attempt in range(3):
                head, files = self.transport.snapshot()
                streams = verified_snapshot(files, self.policy, now)
                prior = next((d for d in streams[self.role] if d['sequence'] == doc['sequence']), None)
                if prior:
                    if prior != doc: raise PermissionError('Conflicting writer/document')
                    published = head; break
                validate_document(doc, self.policy, now)
                if len(streams[self.role]) != doc['sequence'] - 1: raise ProtocolError('Publisher stream gap')
                try:
                    published = self.transport.publish(head, document_files(doc)); break
                except (ConnectionError, TimeoutError):
                    if attempt == 2: raise
            with self.store.tx():
                self.store.db.execute('UPDATE ddb_outbox SET published=? WHERE seq=?', (published, row['seq']))
                self.store.audit('ddb-'+self.role, 'document_published', {'id': doc['id'], 'head': published}, now)
        return len(rows)

    def consume(self, now, handler):
        self.require_open()
        try:
            return self._consume(now, handler)
        except (PermissionError, ProtocolError, ValueError, KeyError):
            self.block(now)
            raise

    def _consume(self, now, handler):
        self.policy.check(now); self.store.verify_audit()
        head, files = self.transport.snapshot(); streams = verified_snapshot(files, self.policy, now)
        peer = 'worker' if self.role == 'supervisor' else 'supervisor'
        with self.store.tx():
            seen = self.store.db.execute('SELECT * FROM ddb_seen WHERE role=? ORDER BY seq', (peer,)).fetchall()
            if len(streams[peer]) < len(seen): raise PermissionError('Remote history rollback')
            for row in seen:
                if sha(streams[peer][row['seq']-1]) != row['digest']: raise PermissionError('Remote history substitution')
            for doc in streams[peer][len(seen):]:
                # Expired history cannot introduce new authority/evidence.
                validate_document(doc, self.policy, now)
                handler(doc, now)
                self.store.db.execute('INSERT INTO ddb_seen VALUES (?,?,?)', (peer, doc['sequence'], sha(doc)))
                self.store.audit('ddb-'+self.role, 'document_received', {'id': doc['id'], 'head': head}, now)
        return len(streams[peer]) - len(seen)

    def due(self, name, now, evidence=False):
        if name not in CADENCE: raise ProtocolError('Compiled cadence required')
        self.policy.check(now)
        with self.store.tx():
            old = self.store.db.execute('SELECT last FROM ddb_cadence WHERE name=?', (name,)).fetchone()
            if old and now < old[0]: raise PermissionError('Clock rollback')
            if old and not evidence and now - old[0] < CADENCE[name]: return False
            self.store.db.execute('INSERT INTO ddb_cadence VALUES (?,?) ON CONFLICT(name) DO UPDATE SET last=excluded.last', (name, now))
            return True


class Supervisor:
    """Deterministic policy engine; not ChatGPT, an LLM, or human approval."""
    def __init__(self, node):
        if node.role != 'supervisor': raise PermissionError('Supervisor signer required')
        self.node = node

    def handle(self, doc, now):
        if doc['kind'] != 'REPORT': return
        n = self.node; n.require_open(); report = doc['body']; db = n.store.db
        if now - doc['issued_at'] > n.policy.body['report_max_age']: raise PermissionError('Stale report cannot authorize work')
        if report['status'] == 'NEEDS_HUMAN':
            n.block(now, 'SUPERVISORY_EXCEPTION')
            return
        active = db.execute('SELECT * FROM ddb_plan WHERE completed=0').fetchall()
        if report['status'] == 'SUCCEEDED':
            if len(active) != 1 or active[0]['id'] != report['directive_id'] or report['task_id'] != 'ddb-task-'+report['directive_id']:
                raise ProtocolError('Unsolicited/conflicting completion')
            n.enqueue('COMPLETE', {'directive_id': report['directive_id'], 'report_digest': sha(doc), 'verdict': 'ACCEPT_ATTESTED_SHADOW'}, 'complete-'+report['directive_id'], now)
            db.execute('UPDATE ddb_plan SET completed=1 WHERE id=?', (report['directive_id'],))
        elif active or db.execute('SELECT count(*) FROM ddb_plan').fetchone()[0]:
            raise ProtocolError('Conflicting idle report')
        count = db.execute('SELECT count(*) FROM ddb_plan').fetchone()[0]
        if count >= n.policy.body['max_tasks']: return
        directive_id = 'd'+str(count+1)+'-'+sha(doc)[:16]
        body = {'directive_id': directive_id, 'task_id': 'ddb-task-'+directive_id,
                'correlation_id': 'ddb-corr-'+directive_id, 'template': n.policy.body['template'], 'source_report': sha(doc)}
        n.enqueue('DIRECTIVE', body, 'directive-'+directive_id, now)
        db.execute('INSERT INTO ddb_plan(id,report) VALUES (?,?)', (directive_id, sha(doc)))

    def poll(self, now): return self.node.consume(now, self.handle)


class Worker:
    def __init__(self, node, backend):
        if node.role != 'worker': raise PermissionError('Worker signer required')
        self.node, self.backend = node, backend

    def idle(self, now):
        return self.node.enqueue('REPORT', {'effort_id': 'initial-idle', 'directive_id': None, 'task_id': None, 'status': 'IDLE', 'evidence': None}, 'initial-idle', now)

    def handle(self, doc, now):
        n = self.node; db = n.store.db; b = doc['body']
        if doc['kind'] == 'COMPLETE':
            old = db.execute('SELECT body FROM ddb_outbox WHERE id=?', ('report-'+b['directive_id'],)).fetchone()
            if old is None: raise PermissionError('Unknown supervisory completion report')
            report = json.loads(old[0])
            if sha(report) != b['report_digest'] or report['body']['status'] != 'SUCCEEDED':
                raise PermissionError('Completion does not bind this verified report')
            db.execute('INSERT INTO ddb_local_reviews(id,body) VALUES (?,?)', (b['directive_id'], canonical(report['body'])))
            return
        if doc['kind'] != 'DIRECTIVE': return
        # A directive must reference an actual worker report in this local journal.
        source = db.execute("SELECT body FROM ddb_outbox WHERE json_extract(body,'$.kind')='REPORT'").fetchall()
        source = next((json.loads(r[0]) for r in source if sha(json.loads(r[0])) == b['source_report']), None)
        if source is None: raise PermissionError('Unknown source report')
        validate_document(source, n.policy, now)
        if now-source['issued_at'] > n.policy.body['report_max_age']: raise PermissionError('Stale source report')
        if db.execute("SELECT 1 FROM ddb_jobs WHERE state!='REPORTED'").fetchone(): raise PermissionError('Conflicting active directive')
        if db.execute('SELECT count(*) FROM ddb_jobs').fetchone()[0] >= n.policy.body['max_tasks']: raise PermissionError('Worker task budget exhausted')
        db.execute("INSERT INTO ddb_jobs VALUES (?,?,?,'RECEIVED')", (b['directive_id'], sha(doc), canonical(doc)))
        n.enqueue('ACK', {'directive_id': b['directive_id'], 'directive_digest': sha(doc), 'state': 'DURABLY_RECEIVED'}, 'ack-'+b['directive_id'], now)

    def poll(self, now): return self.node.consume(now, self.handle)

    def execute_one(self, now):
        n = self.node; n.require_open(); n.policy.check(now); n.store.verify_audit()
        self.apply_reviews(now)
        row = n.store.db.execute("SELECT * FROM ddb_jobs WHERE state!='REPORTED' ORDER BY rowid LIMIT 1").fetchone()
        if not row: return None
        doc = json.loads(row['body']); validate_document(doc, n.policy, now)
        # Commit intent before crossing the existing runtime boundary. Backend
        # must recover the SAME task ID; never launch arbitrary text or a retry.
        with n.store.tx(): n.store.db.execute("UPDATE ddb_jobs SET state='EXECUTING' WHERE id=?", (row['id'],))
        try:
            evidence = self.backend.run(doc['body'], now)
        except Exception:
            # A failure report never retries uncertain effects or authorizes follow-up.
            evidence = None
        body = {'effort_id': 'effort-'+row['id'], 'directive_id': row['id'], 'task_id': doc['body']['task_id'],
                'status': 'SUCCEEDED' if evidence is not None else 'NEEDS_HUMAN',
                'evidence': evidence if evidence is not None else {'category': 'EXECUTION_UNCERTAIN'}}
        with n.store.tx():
            result = n.enqueue('REPORT', body, 'report-'+row['id'], now)
            n.store.db.execute("UPDATE ddb_jobs SET state='REPORTED' WHERE id=?", (row['id'],))
            if evidence is None: n.block(now, 'EXECUTION_UNCERTAIN')
        return result

    def apply_reviews(self, now):
        for row in self.node.store.db.execute('SELECT * FROM ddb_local_reviews WHERE applied=0 ORDER BY rowid LIMIT 10').fetchall():
            self.backend.review(json.loads(row['body']), now)
            with self.node.store.tx():
                self.node.store.db.execute('UPDATE ddb_local_reviews SET applied=1 WHERE id=?', (row['id'],))
                self.node.store.audit('ddb-worker', 'attested_shadow_review_applied', {'directive_id': row['id'], 'human_approval': False}, now)


class PaperOperationsBackend:
    """Reuse genuine local paper processes, receipt verification and durable IDs.

    No Codex/Windows certification is inferred from this backend. A native Codex
    backend stays disabled until its real document-path integration is certified.
    """
    def __init__(self, operations, client):
        from .control_plane import ShadowControlPlane
        if not isinstance(operations.controller, ShadowControlPlane): raise PermissionError('Certified paper backend only')
        self.ops, self.client = operations, client

    def run(self, directive, now):
        from pathlib import Path
        c = self.ops.controller
        arguments = {k: directive[k] for k in ('task_id', 'correlation_id')}
        arguments['project_id'] = 'DCI'
        pending = self.client.store.db.execute('SELECT 1 FROM ops_outbox WHERE ack IS NULL').fetchone()
        if pending: self.client.recover(now)
        self.client.request('SUBMIT', arguments, now)
        if self.ops.store.db.execute("SELECT 1 FROM tasks WHERE state IN ('QUEUED','RUNNING','RETRY_WAIT') AND id!=?", (directive['task_id'],)).fetchone():
            raise PermissionError('Unrelated local controller work must remain isolated')
        c.tick(); self.ops.collect(now)
        job = c._job(directive['task_id'])
        if job['state'] != 'SUCCEEDED': return None
        result = json.loads(job['result'])
        c._verify(job, Path(result['artifact']))
        self.ops.store.verify_audit()
        return {'kind': 'VERIFIED_LOCAL_PAPER', 'scope_digest': job['scope_digest'], 'result_digest': sha(result),
                'artifact_sha256': result['files_sha256']['result.json'], 'git_commit': result['git_after'],
                'audit_valid': True, 'exit_code': 0}

    def review(self, report, now):
        from pathlib import Path
        c = self.ops.controller; job = c._job(report['task_id'])
        result = json.loads(job['result']) if job['result'] else None
        if job['state'] != 'SUCCEEDED' or sha(result) != report['evidence']['result_digest'] or job['scope_digest'] != report['evidence']['scope_digest']:
            raise PermissionError('Changed review evidence')
        c._verify(job, Path(result['artifact']))
        old = self.ops.store.db.execute('SELECT state FROM ops_reviews WHERE task=?', (report['task_id'],)).fetchone()
        if old is None: raise ProtocolError('Existing supervisory review required')
        if old[0] == 'ACCEPT': return
        self.client.recover(now)
        self.client.request('REVIEW', {'task_id': report['task_id'], 'scope_digest': job['scope_digest'],
                                    'result_digest': sha(result), 'verdict': 'ACCEPT'}, now)
