"""HEG simulation only. Delivery is never authorization."""
from dataclasses import dataclass
from uuid import uuid4
from .protocol import ProtocolError


@dataclass(frozen=True)
class SimulationSession:
    identity: str
    authenticated: bool
    simulation: bool = True


class SimulatedNotifications:
    def __init__(self, whatsapp=True, email=True):
        self.available = {'whatsapp': whatsapp, 'email': email}

    def deliver(self, channel, request):
        # No imports or calls to network/email/messaging clients.
        return 'simulated-ack-' + str(uuid4()) if self.available[channel] else None


class HumanGateway:
    def __init__(self, store, notifications=None):
        self.store = store
        self.notifications = notifications or SimulatedNotifications()
        if type(self.notifications) is not SimulatedNotifications:
            raise PermissionError('external notifications are not authorized')

    def tick(self, now):
        s = self.store
        with s.tx():
            for raw in list(s.db.execute("SELECT * FROM escalations WHERE decision IS NULL ORDER BY rowid")):
                request = dict(raw)
                if now >= request['expires']:
                    s.db.execute("UPDATE escalations SET decision='TIMEOUT',decided_at=? WHERE id=?", (now, request['id']))
                    s.db.execute("UPDATE tasks SET state='HUMAN_TIMEOUT' WHERE id=? AND state='NEEDS_HUMAN'", (request['task'],))
                    s._status(request['task'], 'HUMAN_TIMEOUT', 'approval expired; remains non-executable', now)
                    continue
                if s.db.execute("SELECT 1 FROM deliveries WHERE request=? AND state='ACKNOWLEDGED'", (request['id'],)).fetchone():
                    continue
                for channel in ('whatsapp', 'email'):
                    row = s.db.execute("SELECT * FROM deliveries WHERE request=? AND channel=?", (request['id'], channel)).fetchone()
                    if row and (row['state'] == 'ACKNOWLEDGED' or row['attempts'] >= 3 or now < row['next_at']):
                        if row['state'] == 'ACKNOWLEDGED':
                            break
                        continue
                    attempts = row['attempts'] + 1 if row else 1
                    ack = self.notifications.deliver(channel, request)
                    state = 'ACKNOWLEDGED' if ack else ('FAILED' if attempts >= 3 else 'RETRY_WAIT')
                    s.db.execute("INSERT INTO deliveries VALUES (?,?,?,?,?,?) ON CONFLICT(request,channel) DO UPDATE SET attempts=excluded.attempts,state=excluded.state,next_at=excluded.next_at,acknowledgement=excluded.acknowledgement", (request['id'], channel, attempts, state, now+2**attempts, ack))
                    s.audit('heg', 'notification', {'request': request['id'], 'channel': channel, 'state': state, 'attempt': attempts, 'simulation': True}, now)
                    if ack:
                        break

    def decide(self, session, request_id, scope_digest, decision, now):
        if type(session) is not SimulationSession or not session.simulation or not session.authenticated or session.identity != 'synthetic-supervisor':
            raise PermissionError('authenticated simulated supervisor required; no live identity adapter')
        if decision not in ('APPROVE', 'REJECT'):
            raise ProtocolError('invalid decision')
        s = self.store
        with s.tx():
            row = s.db.execute("SELECT * FROM escalations WHERE id=?", (request_id,)).fetchone()
            if row is None or row['scope'] != scope_digest or row['decision'] is not None or now >= row['expires']:
                raise ProtocolError('wrong scope, expired request or replayed decision')
            task = s.task(row['task'])
            if task['state'] != 'NEEDS_HUMAN' or task['expires'] <= now:
                raise ProtocolError('task is not approval eligible')
            # An ordinary approval can release only the explicit synthetic gate.
            # Degraded execution requires reconciliation, never a blind re-run.
            if decision == 'APPROVE' and (row['category'] != 'APPROVAL' or task['action'] != 'gated_shadow_note'):
                raise ProtocolError('uncertain outcome needs reconciliation; approval cannot retry')
            state = 'QUEUED' if decision == 'APPROVE' else 'REJECTED'
            s.db.execute("UPDATE escalations SET decision=?,identity=?,decided_at=? WHERE id=?", (decision, session.identity, now, request_id))
            s.db.execute("UPDATE tasks SET state=? WHERE id=?", (state, task['id']))
            s._status(task['id'], state, 'authenticated simulated ' + decision.lower(), now)
            s.audit('heg', 'decision', {'request': request_id, 'scope': scope_digest, 'identity': session.identity, 'decision': decision, 'simulation': True}, now)
