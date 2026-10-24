"""Deterministic local CFD lifecycle. NOT an MT5 adapter or execution authority.

All accounts/contracts/quotes are synthetic fixtures. No SDK, socket, subprocess,
credential, wall clock, plugin or external service is used. One synchronous owner.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
from pathlib import Path
import sqlite3

from phase4.collector import PassiveCollector
from phase6_2.readiness import Contract, Quote, decimal, positive, nonnegative

LABEL = 'OFFLINE_SIMULATION_ONLY_NON_EDGE_EXECUTION_TEST'
ZERO = Decimal(0)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str, allow_nan=False)


class Blocked(ValueError):
    pass


class Disconnected(Blocked):
    pass


class UnknownAcknowledgement(Blocked):
    pass


@dataclass(frozen=True)
class Identity:
    account: str = 'FIXTURE-DEMO-001'
    server: str = 'OFFLINE-FIXTURE-SERVER'
    kind: str = 'DEMO'
    currency: str = 'USD'
    transport: str = 'IN_PROCESS_FIXTURE'


@dataclass(frozen=True)
class Policy:
    identity: Identity = Identity()
    min_lot: str = '0.01'
    lot_step: str = '0.01'
    max_lot: str = '0.10'
    risk_per_trade: str = '1.00'
    max_open_risk: str = '2.00'
    daily_loss: str = '1.00'
    max_positions: int = 1  # pending reservations count too
    max_spread: str = '0.05'
    max_age_ms: int = 5000
    max_signal_life_ms: int = 30000
    minimal_size_only: bool = True

    def validate(self):
        i = self.identity
        if (i.kind != 'DEMO' or i.transport != 'IN_PROCESS_FIXTURE' or
                not i.account.startswith('FIXTURE-') or not i.server.startswith('OFFLINE-') or i.currency != 'USD'):
            raise Blocked('fixture demo-only account required')
        for x in (self.min_lot, self.lot_step, self.max_lot, self.risk_per_trade,
                  self.max_open_risk, self.daily_loss, self.max_spread):
            positive(x)
        if decimal(self.min_lot) > decimal(self.max_lot) or decimal(self.min_lot) % decimal(self.lot_step):
            raise Blocked('invalid quantity rules')
        if type(self.max_positions) is not int or not 1 <= self.max_positions <= 2:
            raise Blocked('bounded fixture position cap required')
        if type(self.max_age_ms) is not int or not 0 < self.max_age_ms <= 5000:
            raise Blocked('quote age cap')
        if type(self.max_signal_life_ms) is not int or not 0 < self.max_signal_life_ms <= 30000:
            raise Blocked('signal lifetime cap')
        if type(self.minimal_size_only) is not bool:
            raise Blocked('size mode')


@dataclass(frozen=True)
class Signal:
    signal_id: str
    side: int
    kind: str
    stop: str
    target: str
    expires_ms: int
    price: str | None = None
    label: str = LABEL


def fixture_contract():
    # verified means internally specified synthetic units, NOT broker certification.
    return Contract('TESTCFD', 'USD', Decimal('0.01'), Decimal('1'),
                    Decimal('0.50'), Decimal('0'), verified=True)


class Ledger:
    """Transactional local event chain. Detects edits, not adversarial tail rollback."""
    def __init__(self, path: Path, identity: dict, initialize=False):
        path = Path(path)
        new = not path.exists()
        self.was_new = new
        if new and not initialize:
            raise Blocked('missing durable ledger')
        if not path.parent.is_dir():
            raise Blocked('isolated ledger parent required')
        self.db = sqlite3.connect(path, timeout=1)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA journal_mode=DELETE')
        self.db.execute('CREATE TABLE IF NOT EXISTS state(k TEXT PRIMARY KEY,v TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS events(n INTEGER PRIMARY KEY,payload TEXT NOT NULL,prev TEXT NOT NULL,hash TEXT NOT NULL)')
        if new:
            with self.db:
                self.put('identity', identity)
                self.event('INITIALIZED', {'label': LABEL})
        elif self.get('identity') != identity:
            self.db.close()
            raise Blocked('ledger identity/config mismatch')
        try:
            self.verify()
        except Exception:
            self.db.close()
            raise

    def get(self, key, default=None):
        row = self.db.execute('SELECT v FROM state WHERE k=?', (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def require(self, keys):
        for key in keys:
            if self.db.execute('SELECT 1 FROM state WHERE k=?', (key,)).fetchone() is None:
                raise Blocked('incomplete durable state: '+key)

    def put(self, key, value):
        self.db.execute('INSERT OR REPLACE INTO state VALUES(?,?)', (key, canonical(value)))

    def event(self, kind, details):
        last = self.db.execute('SELECT n,hash FROM events ORDER BY n DESC LIMIT 1').fetchone()
        n, prev = (last[0]+1, last[1]) if last else (1, '0'*64)
        payload = canonical({'kind': kind, 'label': LABEL, 'details': details})
        digest = hashlib.sha256((prev+payload).encode()).hexdigest()
        self.db.execute('INSERT INTO events VALUES(?,?,?,?)', (n, payload, prev, digest))

    def verify(self):
        prev = '0'*64
        for expected, row in enumerate(self.db.execute('SELECT n,payload,prev,hash FROM events ORDER BY n'), 1):
            n, payload, before, digest = row
            if n != expected or before != prev or hashlib.sha256((prev+payload).encode()).hexdigest() != digest:
                raise Blocked('audit chain invalid')
            prev = digest
        if prev == '0'*64:
            raise Blocked('empty audit chain')
        return prev

    def close(self):
        self.db.close()


class SimBroker:
    """Local fixture ledger only. Does not accept transport plugins or real orders."""
    def __init__(self, path, identity=Identity(), *, initialize=False):
        self.identity = identity
        self.contract = fixture_contract()
        self.store = Ledger(path, {'role': 'SIM_BROKER', 'account': asdict(identity),
                                  'contract': json.loads(canonical(asdict(self.contract)))}, initialize)
        if self.store.was_new:
            with self.store.db:
                self.store.put('cash', '1000')
                self.store.put('orders', {})
                self.store.put('quote', None)
        try:
            self.store.require(('cash', 'orders', 'quote'))
            decimal(self.store.get('cash'))
            if type(self.store.get('orders')) is not dict:
                raise Blocked('corrupt broker orders')
        except Exception:
            self.store.close()
            raise
        self.available = True  # simulated availability flag, never a connection
        self.reject_next = False
        self.lose_ack_next = False

    def _available(self):
        if not self.available:
            raise Disconnected('simulated disconnect')

    def orders(self):
        self._available()
        return self.store.get('orders')

    def cash(self):
        return decimal(self.store.get('cash'))

    def _cash(self, amount):
        self.store.put('cash', str(self.cash()+amount))

    def quote(self):
        return self.store.get('quote')

    def _entry(self, request, quote):
        tick = self.contract.tick_size
        side = request['side']
        raw = decimal(quote['ask'] if side == 1 else quote['bid']) + side*tick
        if request['kind'] == 'LIMIT':
            limit = decimal(request['price'])
            raw = min(raw, limit) if side == 1 else max(raw, limit)
        return raw

    def _protect(self, request, entry):
        side = request['side']
        stop, target = positive(request['stop']), positive(request['target'])
        if stop % self.contract.tick_size or target % self.contract.tick_size:
            raise Blocked('off-grid protections')
        if side*(entry-stop) < self.contract.tick_size or side*(target-entry) < self.contract.tick_size:
            raise Blocked('invalid SL/TP relative to actual fill')

    def submit(self, client_id, request):
        self._available()
        orders = self.orders()
        if client_id in orders:
            if orders[client_id]['request'] != request:
                raise Blocked('broker idempotency conflict')
            return orders[client_id]
        q = self.quote()
        if q is None:
            raise Blocked('no fixture market')
        row = {'request': request, 'status': 'PENDING', 'entry': None, 'exit': None,
               'entry_ms': None, 'exit_ms': None, 'reason': None, 'net_pnl': None}
        with self.store.db:
            if self.reject_next:
                self.reject_next = False
                row.update(status='REJECTED', reason='INJECTED_BROKER_REJECTION')
            elif request['kind'] == 'MARKET':
                self._open(row, q)
            orders[client_id] = row
            self.store.put('orders', orders)
            self.store.event('SUBMISSION', {'client_id': client_id, 'row': row})
        if self.lose_ack_next:
            self.lose_ack_next = False
            raise UnknownAcknowledgement('accepted result withheld by fixture')
        return row

    def _open(self, row, q):
        request = row['request']
        entry = self._entry(request, q)
        try:
            self._protect(request, entry)
        except Blocked:
            row.update(status='REJECTED', reason='INVALID_PROTECTION_AT_FILL')
            return
        row.update(status='OPEN', entry=str(entry), entry_ms=q['timestamp_ms'])
        self._cash(-decimal(request['quantity'])*self.contract.commission_per_side)

    def _close(self, row, q, reason):
        r = row['request']; side = r['side']; qty = decimal(r['quantity'])
        price = decimal(q['bid'] if side == 1 else q['ask'])-side*self.contract.tick_size
        gross = side*(price-decimal(row['entry']))/self.contract.tick_size*self.contract.tick_value*qty
        fee = qty*self.contract.commission_per_side
        self._cash(gross-fee)
        row.update(status='CLOSED', exit=str(price), exit_ms=q['timestamp_ms'], reason=reason,
                   net_pnl=str(gross-2*fee))

    def on_quote(self, quote):
        self._available()
        previous = self.quote()
        if previous and quote['sequence'] <= previous['sequence']:
            if quote == previous:
                return  # replay recovery after control commit; no repeated fills
            raise Blocked('broker quote replay conflict')
        orders = self.orders()
        with self.store.db:
            self.store.put('quote', quote)
            for client_id, row in sorted(orders.items()):
                r = row['request']; side = r['side']; now = quote['timestamp_ms']
                if row['status'] == 'PENDING':
                    if now >= r['expires_ms']:
                        row.update(status='CANCELLED', reason='EXPIRED')
                    else:
                        trigger = decimal(quote['ask'] if side == 1 else quote['bid'])
                        distance = side*(trigger-decimal(r['price']))
                        if (r['kind'] == 'LIMIT' and distance <= 0) or (r['kind'] == 'STOP' and distance >= 0):
                            self._open(row, quote)
                if row['status'] == 'OPEN':
                    mark = decimal(quote['bid'] if side == 1 else quote['ask'])
                    if side*(mark-decimal(r['stop'])) <= 0:
                        self._close(row, quote, 'STOP')
                    elif side*(mark-decimal(r['target'])) >= 0:
                        self._close(row, quote, 'TARGET')
                    elif now-row['entry_ms'] >= 60000:
                        self._close(row, quote, 'MAX_HOLD')
            self.store.put('orders', orders)
            self.store.event('QUOTE_PROCESSED', {'quote': quote, 'orders': orders})

    def equity(self):
        equity = self.cash(); q = self.quote()
        for row in self.orders().values():
            if row['status'] == 'OPEN':
                r = row['request']; side = r['side']; qty = decimal(r['quantity'])
                mark = decimal(q['bid'] if side == 1 else q['ask'])-side*self.contract.tick_size
                equity += side*(mark-decimal(row['entry']))/self.contract.tick_size*self.contract.tick_value*qty
                equity -= qty*self.contract.commission_per_side
        return equity

    def reduce(self, client_id, reason):
        self._available()
        orders = self.orders(); row = orders[client_id]
        with self.store.db:
            if row['status'] == 'PENDING':
                row.update(status='CANCELLED', reason=reason)
            elif row['status'] == 'OPEN':
                self._close(row, self.quote(), reason)
            self.store.put('orders', orders)
            self.store.event('RISK_REDUCTION', {'client_id': client_id, 'row': row})

    def tighten(self, client_id, stop, target):
        self._available(); orders = self.orders(); row = orders[client_id]
        if row['status'] != 'OPEN':
            raise Blocked('no owned open position')
        r = dict(row['request']); side = r['side']
        if side*(positive(stop)-decimal(r['stop'])) < 0:
            raise Blocked('stop widening denied')
        r.update(stop=stop, target=target)
        q = self.quote(); mark = decimal(q['bid'] if side == 1 else q['ask'])
        self._protect(r, mark)
        with self.store.db:
            row['request'] = r
            self.store.put('orders', orders)
            self.store.event('PROTECTION_TIGHTENED', {'client_id': client_id, 'stop': stop, 'target': target})
        if self.lose_ack_next:
            self.lose_ack_next = False
            raise UnknownAcknowledgement('protection acknowledgement withheld')

    def close(self):
        self.store.close()


class Controller:
    """Synchronous fixture-only state machine; future durable-workflow boundary."""
    def __init__(self, path, broker, policy=Policy(), *, initialize=False):
        policy.validate()
        if type(broker) is not SimBroker:
            raise Blocked('only the in-process SimBroker is accepted')
        self.broker, self.policy = broker, policy
        self._account()
        self.store = Ledger(path, {'role': 'SIM_CONTROLLER', 'policy': json.loads(canonical(asdict(policy)))}, initialize)
        if self.store.was_new:
            with self.store.db:
                for k, v in {'orders': {}, 'halted': True, 'stopped': False, 'reason': 'STARTUP_UNRECONCILED',
                             'quote': None, 'clock': -1, 'day': None, 'day_start': None, 'last_equity': None}.items():
                    self.store.put(k, v)
        try:
            self.store.require(('orders','halted','stopped','reason','quote','clock','day','day_start','last_equity'))
            if type(self.store.get('orders')) is not dict or any(type(self.store.get(k)) is not bool for k in ('halted','stopped')):
                raise Blocked('corrupt controller state')
        except Exception:
            self.store.close()
            raise
        # Every process start requires explicit successful reconciliation.
        with self.store.db:
            self.store.put('halted', True)
            self.store.event('STARTUP_RECONCILIATION_REQUIRED', {})

    def _account(self):
        if self.broker.identity != self.policy.identity:
            raise Blocked('exact account/server/type/transport mismatch; no fallback')
        if self.broker.contract != fixture_contract():
            raise Blocked('fixture contract identity/specification changed')
        self.broker.contract.validate()

    def _clock(self, now):
        if type(now) is not int or now < 0 or now < self.store.get('clock'):
            raise Blocked('invalid/backward clock')
        self.store.put('clock', now)

    def _halt(self, reason):
        with self.store.db:
            self.store.put('halted', True); self.store.put('reason', reason)
            self.store.event('HALTED', {'reason': reason})

    def _fresh(self, now):
        q = self.store.get('quote')
        if q is None or not 0 <= now-q['timestamp_ms'] <= self.policy.max_age_ms:
            raise Blocked('missing/stale/future quote')
        return q

    def _sync(self):
        known = self.store.get('orders'); actual = self.broker.orders()
        if any(k not in known for k, v in actual.items() if v['status'] in ('OPEN', 'PENDING')):
            raise Blocked('unowned broker exposure; no automatic adoption/closure')
        for k, row in known.items():
            if k not in actual:
                if row['status'] not in ('LOCAL_REJECTED',):
                    raise Blocked('unresolved intent; never blindly resend')
                continue
            # Protection changes are journalled in both stores; quantity/side stay bound.
            if actual[k]['request'] != row['request']:
                raise Blocked('broker request/protection mismatch')
            row['status'] = actual[k]['status']
        self.store.put('orders', known)

    def _daily(self, now):
        equity = self.broker.equity(); day = now//86400000
        if self.store.get('day') != day:
            previous = self.store.get('last_equity')
            self.store.put('day', day)
            self.store.put('day_start', str(equity) if previous is None else previous)
        self.store.put('last_equity', str(equity))
        return decimal(self.store.get('day_start'))-equity >= decimal(self.policy.daily_loss)

    def on_quote(self, raw: bytes, now: int):
        try:
            return self._on_quote(raw, now)
        except ValueError as exc:
            self._halt('QUOTE_OR_RECONCILIATION_BLOCKED:'+str(exc))
            raise

    def _on_quote(self, raw: bytes, now: int):
        self._account()
        previous = self.store.get('quote')
        c = PassiveCollector('OFFLINE_FIXTURE', self.broker.contract.symbol,
                             str(self.broker.contract.tick_size), self.policy.max_spread, self.policy.max_age_ms)
        if previous:
            c.sequence, c.timestamp = previous['sequence'], previous['timestamp_ms']
        _, stamp, bid, ask, sequence = c.consume(raw, now)
        q = {'timestamp_ms': stamp, 'bid': bid, 'ask': ask, 'sequence': sequence}
        with self.store.db:
            self._clock(now); self.store.put('quote', q); self.store.event('QUOTE_ACCEPTED', q)
        try:
            if self.store.get('stopped'):
                self._cancel_pending()
            self.broker.on_quote(q)
            with self.store.db:
                self._sync(); breach = self._daily(now)
            if breach:
                self.emergency_stop('DAILY_LOSS', now)
            elif self._post_fill_risk_breach():
                self.emergency_stop('POST_FILL_RISK_BREACH', now)
            elif self.store.get('stopped'):
                self._flatten(now)
        except Blocked as exc:
            self._halt(str(exc)); raise

    def recover(self, now):
        self._account()
        try:
            with self.store.db:
                self._clock(now); q = self._fresh(now)
                if self.store.get('stopped'):
                    self._cancel_pending()
                self.broker.on_quote(q)
                modification = self.store.get('modification')
                if modification:
                    known = self.store.get('orders')
                    client_id = modification['client_id']
                    desired = {**known[client_id]['request'], 'stop': modification['stop'], 'target': modification['target']}
                    actual = self.broker.orders().get(client_id)
                    if actual is None or actual['request'] != desired:
                        raise Blocked('unresolved protection intent; no automatic retry')
                    known[client_id]['request'] = desired
                    self.store.put('orders', known); self.store.put('modification', None)
                    self.store.event('PROTECTION_RECOVERED', modification)
                self._sync(); breach = self._daily(now)
                self.store.verify(); self.broker.store.verify()
                self.store.put('halted', bool(self.store.get('stopped')))
                self.store.event('RECONCILED', {'stopped': self.store.get('stopped')})
            if breach:
                self.emergency_stop('DAILY_LOSS', now)
            elif self._post_fill_risk_breach():
                self.emergency_stop('POST_FILL_RISK_BREACH', now)
            elif self.store.get('stopped'):
                self._flatten(now)
        except Blocked as exc:
            self._halt(str(exc)); raise

    def _risk_per_lot(self, entry, stop, side):
        c = self.broker.contract
        return max(ZERO, side*(entry-decimal(stop))+c.tick_size)/c.tick_size*c.tick_value+2*c.commission_per_side

    def _post_fill_risk_breach(self):
        rows = [v for v in self.broker.orders().values() if v['status'] in ('OPEN', 'PENDING')]
        if len(rows) > self.policy.max_positions:
            return True
        risks = []
        for row in rows:
            r = row['request']
            basis = decimal(row['entry']) if row['entry'] else decimal(r['price'])+r['side']*self.broker.contract.tick_size
            risks.append(self._risk_per_lot(basis, r['stop'], r['side'])*decimal(r['quantity']))
        return any(r > decimal(self.policy.risk_per_trade) for r in risks) or sum(risks, ZERO) > decimal(self.policy.max_open_risk)

    def submit(self, signal: Signal, now: int):
        try:
            return self._submit(signal, now)
        except (ValueError, ArithmeticError) as exc:
            with self.store.db:
                self.store.event('LOCAL_ENTRY_BLOCKED', {'signal_id': str(getattr(signal,'signal_id','INVALID'))[:64], 'reason': str(exc)})
            if isinstance(exc, (Disconnected, UnknownAcknowledgement)):
                self._halt(str(exc))
            raise

    def _submit(self, signal: Signal, now: int):
        self._account()
        if type(signal) is not Signal or signal.label != LABEL:
            raise Blocked('execution-test signal required')
        if type(signal.signal_id) is not str or not signal.signal_id or len(signal.signal_id) > 64 or not signal.signal_id.isascii():
            raise Blocked('bounded signal identity')
        client_id = 'SIM-'+hashlib.sha256(signal.signal_id.encode()).hexdigest()[:24]
        fingerprint = canonical(asdict(signal))
        orders = self.store.get('orders')
        if client_id in orders:
            if orders[client_id]['fingerprint'] != fingerprint:
                self._halt('DUPLICATE_ID_PAYLOAD_CONFLICT'); raise Blocked('duplicate signal conflict')
            return orders[client_id]  # durable suppression, including rejected/unknown intents
        if self.store.get('halted') or self.store.get('stopped'):
            raise Blocked('halted/stopped')
        with self.store.db:
            self._clock(now); q = self._fresh(now)
            self._sync()
            breach = self._daily(now)
        if breach:
            self.emergency_stop('DAILY_LOSS', now); raise Blocked('daily loss')
        p = self.policy; c = self.broker.contract
        if type(signal.side) is not int or signal.side not in (-1, 1) or signal.kind not in ('MARKET', 'LIMIT', 'STOP'):
            raise Blocked('invalid side/order kind')
        if type(signal.expires_ms) is not int or not now < signal.expires_ms <= now+p.max_signal_life_ms:
            raise Blocked('expired/overlong signal')
        if (signal.kind == 'MARKET') != (signal.price is None):
            raise Blocked('pending price required, market price forbidden')
        for x in (signal.stop, signal.target):
            if positive(x) % c.tick_size:
                raise Blocked('off-grid protection')
        base = decimal(q['ask'] if signal.side == 1 else q['bid'])
        if signal.price is not None:
            base = positive(signal.price)
            if base % c.tick_size:
                raise Blocked('off-grid pending price')
            market = decimal(q['ask'] if signal.side == 1 else q['bid'])
            difference = signal.side*(base-market)
            if (signal.kind == 'LIMIT' and difference >= 0) or (signal.kind == 'STOP' and difference <= 0):
                raise Blocked('invalid pending side')
        entry = base+signal.side*c.tick_size
        self.broker._protect(asdict(signal), entry)
        active = [v for v in self.broker.orders().values() if v['status'] in ('OPEN', 'PENDING')]
        if len(active) >= p.max_positions:
            raise Blocked('position/pending reservation cap')
        risk = self._risk_per_lot(entry, signal.stop, signal.side)
        remaining_daily = decimal(p.daily_loss)-max(ZERO, decimal(self.store.get('day_start'))-self.broker.equity())
        budget = min(decimal(p.risk_per_trade), self.broker.equity(), remaining_daily)
        qty = (min(decimal(p.max_lot), budget/risk)/decimal(p.lot_step)).to_integral_value(rounding=ROUND_FLOOR)*decimal(p.lot_step)
        if p.minimal_size_only:
            qty = min(qty, decimal(p.min_lot))
        if qty < decimal(p.min_lot):
            raise Blocked('minimum lot exceeds risk budget')
        open_risk = ZERO
        for v in active:
            r = v['request']; basis = decimal(v['entry']) if v['entry'] else decimal(r['price'])+r['side']*c.tick_size
            open_risk += self._risk_per_lot(basis, r['stop'], r['side'])*decimal(r['quantity'])
        if open_risk+qty*risk > min(decimal(p.max_open_risk), remaining_daily):
            raise Blocked('aggregate open risk cap')
        request = {**asdict(signal), 'quantity': str(qty), 'label': LABEL}
        row = {'fingerprint': fingerprint, 'request': request, 'status': 'SUBMITTING'}
        with self.store.db:
            orders[client_id] = row; self.store.put('orders', orders)
            self.store.event('INTENT_DURABLE_BEFORE_DISPATCH', {'client_id': client_id, 'request': request})
        try:
            result = self.broker.submit(client_id, request)
        except Blocked as exc:
            self._halt('UNKNOWN_DISPATCH_RESULT:'+str(exc)); raise
        with self.store.db:
            row['status'] = result['status']; orders[client_id] = row
            self.store.put('orders', orders); self.store.event('ACKNOWLEDGED', {'client_id': client_id, 'status': result['status']})
        return row

    def _flatten(self, now):
        self._account(); self._fresh(now)
        known = self.store.get('orders')
        for client_id, row in self.broker.orders().items():
            if row['status'] in ('OPEN', 'PENDING'):
                if client_id not in known:
                    raise Blocked('foreign exposure requires manual reconciliation')
                self.broker.reduce(client_id, 'EMERGENCY_STOP')
        with self.store.db:
            self._sync(); self.store.event('OWNED_EXPOSURE_FLAT', {})

    def _cancel_pending(self):
        known = self.store.get('orders')
        for client_id, row in self.broker.orders().items():
            if row['status'] == 'PENDING':
                if client_id not in known:
                    raise Blocked('foreign pending exposure')
                self.broker.reduce(client_id, 'STOP_PENDING_CANCEL')

    def emergency_stop(self, reason, now):
        # Persist the latch before any attempt at risk reduction; never auto-reset.
        with self.store.db:
            self.store.put('stopped', True); self.store.put('halted', True); self.store.put('reason', reason)
            self.store.event('EMERGENCY_STOP_LATCHED', {'reason': reason})
        try:
            self._flatten(now)
        except Blocked:
            self._halt('STOP_LATCHED_EXPOSURE_UNRESOLVED')
            raise

    def tighten(self, client_id, stop, target, now):
        self._account(); self._fresh(now)
        if self.store.get('halted') or self.store.get('stopped'):
            raise Blocked('halted modification')
        known = self.store.get('orders')
        if client_id not in known:
            raise Blocked('unknown position')
        row = self.broker.orders().get(client_id)
        if row is None or row['status'] != 'OPEN':
            raise Blocked('no owned open position')
        r = row['request']
        if r['side']*(positive(stop)-decimal(r['stop'])) < 0:
            raise Blocked('stop widening denied')
        q = self.broker.quote()
        self.broker._protect({**r, 'stop': stop, 'target': target}, decimal(q['bid'] if r['side'] == 1 else q['ask']))
        with self.store.db:
            self.store.put('modification', {'client_id': client_id, 'stop': stop, 'target': target})
            self.store.event('PROTECTION_INTENT_DURABLE', {'client_id': client_id, 'stop': stop, 'target': target})
        try:
            self.broker.tighten(client_id, stop, target)
        except Blocked as exc:
            self._halt(str(exc)); raise
        known[client_id]['request'].update(stop=stop, target=target)
        with self.store.db:
            self.store.put('orders', known); self.store.put('modification', None)
            self.store.event('PROTECTION_ACKNOWLEDGED', {'client_id': client_id, 'stop': stop, 'target': target})

    def close(self):
        self.store.close()


def execution_test_signal(q: dict, run_id='ONE_SHOT'):
    """One reproducible minimum-size test intent. Repeated calls share the same ID."""
    ask = decimal(q['ask'])
    return Signal('NON_EDGE_EXECUTION_TEST:'+run_id, 1, 'MARKET',
                  str(ask-Decimal('0.10')), str(ask+Decimal('0.10')),
                  q['timestamp_ms']+10000)
