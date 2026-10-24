"""Deterministic synthetic execution mechanics, never market/edge evidence."""
import ast
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from phase7.simulator import (Controller, SimBroker, Policy, Identity, Signal,
                             LABEL, Blocked, Disconnected, UnknownAcknowledgement,
                             execution_test_signal, canonical)

T = 1735776000000  # Synthetic clock, 2025-01-02 UTC; no historical quotes.


def raw_quote(seq=1, ms=T, bid='100.00', ask='100.02', **changes):
    row = dict(schema='MT5_QUOTES_V1', source_id='OFFLINE_FIXTURE', symbol='TESTCFD',
               sequence=seq, timestamp_ms=ms, bid=bid, ask=ask)
    row.update(changes)
    return canonical(row).encode()


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.policy = Policy()
        self.b = SimBroker(self.root/'broker.sqlite', initialize=True)
        self.e = Controller(self.root/'control.sqlite', self.b, self.policy, initialize=True)
        self.e.on_quote(raw_quote(), T)
        self.e.recover(T)

    def tearDown(self):
        self.e.close(); self.b.close(); self.tmp.cleanup()

    def signal(self, name='TEST', side=1, kind='MARKET', price=None, stop=None, target=None):
        return Signal(name, side, kind, stop or ('99.92' if side == 1 else '100.10'),
                      target or ('100.12' if side == 1 else '99.90'), T+10000, price)

    def restart(self, policy=None):
        self.e.close(); self.b.close()
        self.b = SimBroker(self.root/'broker.sqlite')
        self.e = Controller(self.root/'control.sqlite', self.b, policy or self.policy)

    def sole(self):
        return next(iter(self.b.orders().values()))

    def test_market_buy_attached_protection_and_costed_target(self):
        r = self.e.submit(self.signal(), T)
        self.assertEqual(r['status'], 'OPEN')
        self.assertEqual(self.sole()['entry'], '100.03')
        self.assertEqual(r['request']['quantity'], '0.01')
        self.e.on_quote(raw_quote(2, T+1000, '100.12', '100.14'), T+1000)
        p = self.sole()
        self.assertEqual((p['status'], p['reason'], p['exit']), ('CLOSED', 'TARGET', '100.11'))
        self.assertEqual(Decimal(p['net_pnl']), Decimal('0.07'))
        self.assertEqual(self.b.cash(), Decimal('1000.07'))

    def test_market_sell_ask_side_stop(self):
        self.e.submit(self.signal(side=-1), T)
        self.assertEqual(self.sole()['entry'], '99.99')
        self.e.on_quote(raw_quote(2, T+1000, '100.09', '100.11'), T+1000)
        self.assertEqual(self.sole()['reason'], 'STOP')
        self.assertEqual(self.sole()['exit'], '100.12')

    def test_pending_four_directions(self):
        cases = [(1,'LIMIT','99.98','99.88','100.20','99.95','99.97'),
                 (-1,'LIMIT','100.04','100.14','99.80','100.05','100.07'),
                 (1,'STOP','100.04','99.94','100.30','100.04','100.06'),
                 (-1,'STOP','99.98','100.08','99.70','99.96','99.98')]
        for side,kind,price,stop,target,bid,ask in cases:
            with self.subTest(side=side,kind=kind):
                with tempfile.TemporaryDirectory() as d:
                    b=SimBroker(Path(d)/'b',initialize=True);e=Controller(Path(d)/'e',b,initialize=True)
                    try:
                        e.on_quote(raw_quote(),T);e.recover(T)
                        s=Signal('PENDING',side,kind,stop,target,T+10000,price)
                        self.assertEqual(e.submit(s,T)['status'],'PENDING')
                        e.on_quote(raw_quote(2,T+1000,bid,ask),T+1000)
                        self.assertEqual(next(iter(b.orders().values()))['status'],'OPEN')
                    finally:e.close();b.close()

    def test_pending_limit_never_worse_than_limit(self):
        self.e.submit(self.signal(kind='LIMIT',price='99.98',stop='99.80',target='100.20'), T)
        self.e.on_quote(raw_quote(2,T+1000,'99.95','99.97'),T+1000)
        self.assertLessEqual(Decimal(self.sole()['entry']),Decimal('99.98'))

    def test_pending_expiry(self):
        self.e.submit(self.signal(kind='LIMIT',price='99.98'),T)
        self.e.on_quote(raw_quote(2,T+10000),T+10000)
        self.assertEqual(self.sole()['status'],'CANCELLED')
        self.assertEqual(self.b.cash(),Decimal('1000'))

    def test_invalid_protection_grid_and_direction(self):
        for s in [self.signal(stop='100.04'),self.signal(target='100.02'),
                  self.signal(stop='99.921'),self.signal(stop='NaN'),
                  self.signal(target='0')]:
            with self.subTest(s=s), self.assertRaises(ValueError): self.e.submit(s,T)
        self.assertEqual(self.b.orders(),{})

    def test_wrong_pending_side_rejected(self):
        for kind,price in [('LIMIT','100.10'),('STOP','99.90')]:
            with self.subTest(kind=kind),self.assertRaises(Blocked):
                self.e.submit(self.signal(kind=kind,price=price),T)

    def test_expired_and_overlong_signal(self):
        for expiry in (T,T-1,T+30001,True):
            with self.subTest(expiry=expiry),self.assertRaises(Blocked):
                self.e.submit(replace(self.signal(),expires_ms=expiry),T)

    def test_position_cap_counts_pending(self):
        self.e.submit(self.signal(kind='LIMIT',price='99.98'),T)
        with self.assertRaises(Blocked): self.e.submit(self.signal('SECOND'),T)
        self.assertEqual(len(self.b.orders()),1)

    def test_minimum_lot_can_be_unaffordable(self):
        self.e.close()
        self.policy=replace(self.policy,risk_per_trade='0.001')
        self.e=Controller(self.root/'tiny',self.b,self.policy,initialize=True)
        self.e.on_quote(raw_quote(2,T+1),T+1);self.e.recover(T+1)
        with self.assertRaises(Blocked): self.e.submit(self.signal(),T+1)
        self.assertEqual(self.b.orders(),{})

    def test_sizing_floors_to_step_and_includes_costs(self):
        self.e.close();self.policy=replace(self.policy,minimal_size_only=False)
        self.e=Controller(self.root/'sizer',self.b,self.policy,initialize=True)
        self.e.on_quote(raw_quote(2,T+1),T+1);self.e.recover(T+1)
        self.assertEqual(self.e.submit(self.signal(),T+1)['request']['quantity'],'0.07')

    def test_daily_budget_caps_minimum_lot(self):
        self.e.close();self.policy=replace(self.policy,daily_loss='0.01')
        self.e=Controller(self.root/'daily',self.b,self.policy,initialize=True)
        self.e.on_quote(raw_quote(2,T+1),T+1);self.e.recover(T+1)
        with self.assertRaises(Blocked):self.e.submit(self.signal(),T+1)

    def test_duplicate_signal_survives_restart(self):
        s=self.signal();self.e.submit(s,T);cash=self.b.cash()
        self.restart();self.e.recover(T)
        self.assertEqual(self.e.submit(s,T)['status'],'OPEN')
        self.assertEqual((len(self.b.orders()),self.b.cash()),(1,cash))

    def test_duplicate_id_changed_payload_halts(self):
        s=self.signal();self.e.submit(s,T)
        with self.assertRaises(Blocked):self.e.submit(replace(s,target='100.30'),T)
        self.assertTrue(self.e.store.get('halted'))

    def test_broker_rejection_is_terminal_not_retried(self):
        self.b.reject_next=True;s=self.signal()
        self.assertEqual(self.e.submit(s,T)['status'],'REJECTED')
        self.assertEqual(self.e.submit(s,T)['status'],'REJECTED')
        self.assertEqual((len(self.b.orders()),self.b.cash()),(1,Decimal('1000')))

    def test_disconnect_blocks_new_intent(self):
        self.b.available=False
        with self.assertRaises(Disconnected):self.e.submit(self.signal(),T)
        self.assertTrue(self.e.store.get('halted'))
        self.assertEqual(self.e.store.get('orders'),{})
        self.b.available=True;self.e.recover(T)
        self.assertFalse(self.e.store.get('halted'))

    def test_lost_ack_reconciles_without_resubmit(self):
        self.b.lose_ack_next=True;s=self.signal()
        with self.assertRaises(UnknownAcknowledgement):self.e.submit(s,T)
        cash=self.b.cash();self.restart()
        with self.assertRaises(Blocked):self.e.submit(self.signal('NEW'),T)
        self.e.recover(T)
        self.assertEqual(self.e.submit(s,T)['status'],'OPEN')
        self.assertEqual((len(self.b.orders()),self.b.cash()),(1,cash))

    def test_unresolved_pre_dispatch_intent_never_blindly_retries(self):
        s=self.signal()
        with patch.object(self.b,'submit',side_effect=UnknownAcknowledgement('pre-dispatch crash')):
            with self.assertRaises(UnknownAcknowledgement):self.e.submit(s,T)
        with self.assertRaises(Blocked):self.e.recover(T)
        self.assertEqual(self.b.orders(),{})
        self.assertTrue(self.e.store.get('halted'))

    def test_quote_committed_before_broker_recovery_is_idempotent(self):
        self.e.submit(self.signal(),T)
        with patch.object(self.b,'on_quote',side_effect=UnknownAcknowledgement('quote processing crash')):
            with self.assertRaises(UnknownAcknowledgement):self.e.on_quote(raw_quote(2,T+1000,'100.12','100.14'),T+1000)
        self.restart();self.e.recover(T+1000);cash=self.b.cash()
        self.e.recover(T+1000)
        self.assertEqual(self.sole()['status'],'CLOSED');self.assertEqual(self.b.cash(),cash)

    def test_stale_future_crossed_off_grid_replay_quotes_halt(self):
        values=[(raw_quote(2,T+1),T+6000),(raw_quote(2,T+2),T+1),
                (raw_quote(2,T+1,'100.03','100.02'),T+1),
                (raw_quote(2,T+1,'100.001','100.02'),T+1),
                (raw_quote(),T),(raw_quote(2,T+1,source_id='WRONG'),T+1)]
        for raw,now in values:
            with self.subTest(raw=raw),self.assertRaises(ValueError):self.e.on_quote(raw,now)
        self.assertEqual(self.e.store.get('quote')['sequence'],1)
        self.assertTrue(self.e.store.get('halted'))

    def test_stale_entry_is_blocked(self):
        with self.assertRaises(Blocked):self.e.submit(self.signal(),T+5001)
        self.assertEqual(self.b.orders(),{})

    def test_emergency_stop_closes_owned_and_persists_across_restart(self):
        self.e.submit(self.signal(),T);self.e.emergency_stop('OPERATOR',T)
        self.assertEqual(self.sole()['status'],'CLOSED');self.restart();self.e.recover(T)
        self.assertTrue(self.e.store.get('stopped'))
        with self.assertRaises(Blocked):self.e.submit(self.signal('AFTER_STOP'),T)

    def test_stop_disconnected_retains_latch_and_flattens_later(self):
        self.e.submit(self.signal(),T);self.b.available=False
        with self.assertRaises(Disconnected):self.e.emergency_stop('OPERATOR',T)
        self.assertTrue(self.e.store.get('stopped'))
        self.b.available=True;self.e.on_quote(raw_quote(2,T+1),T+1)
        self.assertEqual(self.sole()['status'],'CLOSED')

    def test_stop_stale_quote_does_not_invent_exit_price(self):
        self.e.submit(self.signal(),T)
        with self.assertRaises(Blocked):self.e.emergency_stop('OPERATOR',T+6000)
        self.assertEqual(self.sole()['status'],'OPEN')
        self.e.on_quote(raw_quote(2,T+6001),T+6001)
        self.assertEqual(self.sole()['status'],'CLOSED')

    def test_stop_cancels_pending_without_entry(self):
        self.e.submit(self.signal(kind='LIMIT',price='99.98'),T)
        self.e.emergency_stop('OPERATOR',T)
        self.assertEqual(self.sole()['status'],'CANCELLED')
        self.assertEqual(self.b.cash(),Decimal('1000'))

    def test_gap_loss_breaches_daily_cap_and_latches_stop(self):
        self.e.submit(self.signal(),T)
        self.e.on_quote(raw_quote(2,T+1000,'98.90','98.92'),T+1000)
        self.assertLess(Decimal(self.sole()['net_pnl']),Decimal('-1'))
        self.assertTrue(self.e.store.get('stopped'))
        self.assertEqual(self.e.store.get('reason'),'DAILY_LOSS')
        self.e.on_quote(raw_quote(3,T+86400000,'100.00','100.02'),T+86400000)
        self.assertTrue(self.e.store.get('stopped'))

    def test_pending_fill_risk_breach_forces_owned_flat(self):
        self.e.submit(self.signal(kind='STOP',price='100.04',stop='99.94',target='102.00'),T)
        self.e.on_quote(raw_quote(2,T+1000,'101.10','101.12'),T+1000)
        self.assertTrue(self.e.store.get('stopped'))
        self.assertEqual(self.e.store.get('reason'),'POST_FILL_RISK_BREACH')
        self.assertEqual(self.sole()['status'],'CLOSED')

    def test_tighten_stop_and_reject_widen(self):
        self.e.submit(self.signal(),T);client=next(iter(self.b.orders()))
        self.e.tighten(client,'99.95','100.20',T)
        self.assertEqual(self.sole()['request']['stop'],'99.95')
        with self.assertRaises(Blocked):self.e.tighten(client,'99.90','100.20',T)
        self.restart();self.e.recover(T)

    def test_protection_lost_ack_recovers_exact_intent(self):
        self.e.submit(self.signal(),T);client=next(iter(self.b.orders()));self.b.lose_ack_next=True
        with self.assertRaises(UnknownAcknowledgement):self.e.tighten(client,'99.95','100.20',T)
        self.restart();self.e.recover(T)
        self.assertFalse(self.e.store.get('halted'))
        self.assertEqual(self.e.store.get('orders')[client]['request']['stop'],'99.95')

    def test_unowned_exposure_is_not_adopted_or_closed(self):
        request={**self.signal().__dict__,'quantity':'0.01'}
        self.b.submit('FOREIGN_FIXTURE',request)
        with self.assertRaises(Blocked):self.e.recover(T)
        with self.assertRaises(Blocked):self.e.emergency_stop('OPERATOR',T)
        self.assertEqual(self.b.orders()['FOREIGN_FIXTURE']['status'],'OPEN')

    def test_account_change_blocks_routing(self):
        self.b.identity=replace(self.b.identity,account='FIXTURE-DEMO-OTHER')
        with self.assertRaises(Blocked):self.e.submit(self.signal(),T)
        self.assertEqual(self.b.orders(),{})

    def test_contract_mutation_blocks_entry(self):
        self.b.contract=replace(self.b.contract,tick_value=Decimal('2'))
        with self.assertRaises(Blocked):self.e.submit(self.signal(),T)
        self.assertEqual(self.b.orders(),{})

    def test_backwards_clock_after_valid_tick_is_rejected(self):
        self.e.on_quote(raw_quote(2,T+1000),T+1000)
        with self.assertRaises(Blocked):self.e.submit(self.signal(),T+500)
        self.assertEqual(self.b.orders(),{})

    def test_oversized_spread_rejected(self):
        with self.assertRaises(ValueError):self.e.on_quote(raw_quote(2,T+1,'100.00','100.06'),T+1)
        self.assertTrue(self.e.store.get('halted'))

    def test_kill_cancels_disconnected_pending_before_next_trigger(self):
        self.e.submit(self.signal(kind='LIMIT',price='99.98',stop='99.80',target='100.20'),T)
        self.b.available=False
        with self.assertRaises(Disconnected):self.e.emergency_stop('OPERATOR',T)
        self.b.available=True
        self.e.on_quote(raw_quote(2,T+1,'99.95','99.97'),T+1)
        self.assertEqual(self.sole()['status'],'CANCELLED')
        self.assertEqual(self.b.cash(),Decimal('1000'))

    def test_pending_gap_past_target_is_rejected_without_naked_position(self):
        self.e.submit(self.signal(kind='STOP',price='100.04',stop='99.94',target='100.30'),T)
        self.e.on_quote(raw_quote(2,T+1,'100.40','100.42'),T+1)
        self.assertEqual(self.sole()['status'],'REJECTED')
        self.assertEqual(self.b.cash(),Decimal('1000'))

    def test_signal_identity_type_is_checked(self):
        with self.assertRaises(Blocked):self.e.submit(replace(self.signal(),signal_id=123),T)

    def test_invalid_policy_numbers_are_rejected(self):
        for policy in (replace(Policy(),daily_loss='NaN'),replace(Policy(),risk_per_trade='-1'),
                       replace(Policy(),lot_step='0'),replace(Policy(),max_positions=True),
                       replace(Policy(),max_age_ms=6000),replace(Policy(),min_lot='0.015')):
            with self.subTest(policy=policy),self.assertRaises(ValueError):policy.validate()

    def test_aggregate_risk_caps_multiple_reservations(self):
        self.e.close();self.policy=replace(self.policy,max_positions=2,max_open_risk='0.20')
        self.e=Controller(self.root/'aggregate',self.b,self.policy,initialize=True)
        self.e.on_quote(raw_quote(2,T+1),T+1);self.e.recover(T+1)
        self.e.submit(self.signal('FIRST'),T+1)
        with self.assertRaises(Blocked):self.e.submit(self.signal('SECOND',side=-1),T+1)
        self.assertEqual(len(self.b.orders()),1)

    def test_unresolved_protection_change_is_not_retried(self):
        self.e.submit(self.signal(),T);client=next(iter(self.b.orders()))
        with patch.object(self.b,'tighten',side_effect=UnknownAcknowledgement('before protection dispatch')):
            with self.assertRaises(UnknownAcknowledgement):self.e.tighten(client,'99.95','100.20',T)
        with self.assertRaises(Blocked):self.e.recover(T)
        self.assertEqual(self.sole()['request']['stop'],'99.92')

    def test_unexpected_broker_protection_change_halts_recovery(self):
        self.e.submit(self.signal(),T);client=next(iter(self.b.orders()))
        self.b.tighten(client,'99.95','100.20')
        with self.assertRaises(Blocked):self.e.recover(T)
        self.assertTrue(self.e.store.get('halted'))

    def test_missing_broker_cash_is_corruption_not_initialization(self):
        with self.b.store.db:self.b.store.db.execute("DELETE FROM state WHERE k='cash'")
        with self.assertRaises(Blocked):SimBroker(self.root/'broker.sqlite',initialize=True)
        self.assertIsNone(self.b.store.get('cash'))

    def test_missing_controller_orders_not_silently_reinitialized(self):
        with self.e.store.db:self.e.store.db.execute("DELETE FROM state WHERE k='orders'")
        with self.assertRaises(Blocked):Controller(self.root/'control.sqlite',self.b,initialize=True)

    def test_current_policy_never_allows_zero_or_unbounded_quantity(self):
        self.e.submit(self.signal(),T)
        q=Decimal(self.sole()['request']['quantity'])
        self.assertGreaterEqual(q,Decimal(self.policy.min_lot))
        self.assertLessEqual(q,Decimal(self.policy.max_lot))
        self.assertEqual(q % Decimal(self.policy.lot_step),0)

    def test_local_rejection_recorded_in_audit(self):
        with self.assertRaises(Blocked):self.e.submit(self.signal(stop='100.04'),T)
        payloads=[json.loads(r[0]) for r in self.e.store.db.execute('SELECT payload FROM events')]
        self.assertTrue(any(p['kind']=='LOCAL_ENTRY_BLOCKED' for p in payloads))

    def test_exit_ack_loss_recovers_flat_without_double_close_fee(self):
        self.e.submit(self.signal(),T)
        reduce=self.b.reduce
        def effect_then_lost_ack(client,reason):
            reduce(client,reason)
            raise UnknownAcknowledgement('close acknowledgement lost')
        with patch.object(self.b,'reduce',side_effect=effect_then_lost_ack):
            with self.assertRaises(UnknownAcknowledgement):self.e.emergency_stop('OPERATOR',T)
        cash=self.b.cash();self.restart();self.e.recover(T)
        self.assertEqual(self.sole()['status'],'CLOSED')
        self.assertEqual(self.b.cash(),cash)

    def test_wrong_account_modes_are_rejected(self):
        bad=[replace(Identity(),kind='REAL'),replace(Identity(),kind='UNKNOWN'),
             replace(Identity(),transport='MT5'),replace(Identity(),server='UNVERIFIED'),
             replace(Identity(),account='123456'),replace(Identity(),currency='EUR')]
        for identity in bad:
            with self.subTest(identity=identity),self.assertRaises(Blocked):Policy(identity=identity).validate()

    def test_non_fixture_adapter_rejected(self):
        with self.assertRaises(Blocked):Controller(self.root/'adapter',object(),initialize=True)

    def test_missing_ledger_not_silently_reset(self):
        with self.assertRaises(Blocked):SimBroker(self.root/'missing')

    def test_policy_change_on_restart_fails_closed(self):
        with self.assertRaises(Blocked):Controller(self.root/'control.sqlite',self.b,replace(self.policy,daily_loss='2'))

    def test_audit_edit_detected(self):
        self.e.store.db.execute("UPDATE events SET payload='{}' WHERE n=1");self.e.store.db.commit()
        with self.assertRaises(Blocked):self.e.store.verify()

    def test_max_holding_time(self):
        self.e.submit(self.signal(),T)
        self.e.on_quote(raw_quote(2,T+60000),T+60000)
        self.assertEqual(self.sole()['reason'],'MAX_HOLD')

    def test_one_shot_strategy_is_deduplicated(self):
        q=self.e.store.get('quote');s=execution_test_signal(q)
        self.assertIn('NON_EDGE_EXECUTION_TEST',s.signal_id)
        self.e.submit(s,T);self.e.submit(execution_test_signal(q),T)
        self.assertEqual(len(self.b.orders()),1)

    def test_offline_runtime_has_no_network_or_process_calls(self):
        with patch('socket.socket',side_effect=AssertionError('network forbidden')),patch('subprocess.Popen',side_effect=AssertionError('process forbidden')):
            self.e.submit(self.signal(),T);self.e.emergency_stop('TEST',T)


class Determinism(unittest.TestCase):
    def test_identical_fixture_runs_have_identical_event_chains(self):
        results=[]
        for _ in range(2):
            with tempfile.TemporaryDirectory() as d:
                b=SimBroker(Path(d)/'b',initialize=True);e=Controller(Path(d)/'e',b,initialize=True)
                try:
                    e.on_quote(raw_quote(),T);e.recover(T)
                    e.submit(execution_test_signal(e.store.get('quote')),T)
                    e.on_quote(raw_quote(2,T+1000,'100.12','100.14'),T+1000)
                    results.append((e.store.verify(),b.store.verify(),str(b.cash())))
                finally:e.close();b.close()
        self.assertEqual(results[0],results[1])

    def test_module_imports_are_offline_allowlist(self):
        source=(Path(__file__).parent/'simulator.py').read_text();tree=ast.parse(source)
        allowed={'__future__','dataclasses','decimal','hashlib','json','pathlib','sqlite3','phase4','phase6_2'}
        imports=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):imports += [x.name.split('.')[0] for x in n.names]
            elif isinstance(n,ast.ImportFrom):imports.append(n.module.split('.')[0])
        self.assertLessEqual(set(imports),allowed)


if __name__=='__main__':unittest.main()
