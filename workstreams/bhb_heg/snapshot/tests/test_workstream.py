"""Bounded shadow BHB/HEG fault evidence against the supplied DCI snapshot."""
import os
import tempfile
import unittest
from pathlib import Path

from dci.bridge.brain import BrainTools
from dci.bridge.heg import HumanGateway, SimulatedNotifications, SimulationSession
from dci.bridge.protocol import ProtocolError, envelope
from dci.bridge.runner import DEGRADED, Runner
from dci.bridge.store import BridgeStore


WORKSPACE = Path(__file__).resolve().parents[1]


class WorkstreamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=WORKSPACE)
        self.path = Path(self.temp.name) / 'mailbox.db'
        self.store = BridgeStore(self.path)
        self.runner = Runner(self.store, WORKSPACE)
        self.brain = BrainTools(self.store)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def task(self, action='synthetic_check', ttl=3600):
        return self.store.create_task(action, 100, ttl, 'task-test', 'corr-test')

    def restart(self):
        self.store.close()
        self.store = BridgeStore(self.path)
        self.runner = Runner(self.store, WORKSPACE)
        self.brain = BrainTools(self.store)

    def executions(self):
        return self.store.db.execute('SELECT count(*) FROM executions').fetchone()[0]

    def test_non_admin_workspace_identity(self):
        self.assertNotEqual(os.geteuid(), 0)
        self.assertNotIn(0, os.getgroups())
        self.assertEqual(self.runner.workspace, WORKSPACE)

    def test_expired_task_never_executes(self):
        self.task(ttl=2)
        self.assertIsNone(self.runner.tick(102))
        self.assertEqual(self.store.task('task-test')['state'], 'EXPIRED')
        self.assertEqual(self.executions(), 0)

    def test_correlated_result_survives_restart(self):
        self.task()
        self.assertEqual(self.runner.tick(101)['state'], 'SUCCEEDED')
        self.restart()
        report = self.brain.get_status('task-test')
        self.assertEqual(report['correlation_id'], 'corr-test')
        self.assertTrue(report['result']['passed'])
        self.assertTrue(all(m['correlation_id'] == 'corr-test' for m in report['messages']))
        self.assertEqual(len([m for m in report['messages'] if m['kind'] == 'RESULT']), 1)
        self.assertEqual(self.executions(), 1)
        self.store.verify_audit()

    def test_simulated_denial_blocks_execution(self):
        self.task('gated_shadow_note')
        self.assertIsNone(self.runner.tick(101))
        request = dict(self.store.db.execute('SELECT * FROM escalations').fetchone())
        gateway = HumanGateway(self.store)
        gateway.tick(102)
        self.assertEqual(self.store.task('task-test')['state'], 'NEEDS_HUMAN')
        gateway.decide(SimulationSession('synthetic-supervisor', True), request['id'], request['scope'], 'REJECT', 103)
        self.assertIsNone(self.runner.tick(104))
        self.assertEqual(self.store.task('task-test')['state'], 'REJECTED')
        self.assertEqual(self.executions(), 0)
        with self.assertRaises(ProtocolError):
            gateway.decide(SimulationSession('synthetic-supervisor', True), request['id'], request['scope'], 'APPROVE', 105)

    def test_claimed_task_restart_requires_reconciliation(self):
        self.task()
        claimed = self.runner.claim(101)
        self.assertEqual(claimed['state'], 'RUNNING')
        self.restart()
        self.assertIsNone(self.runner.tick(131))
        self.assertEqual(self.store.task('task-test')['state'], 'NEEDS_HUMAN')
        request = dict(self.store.db.execute('SELECT * FROM escalations').fetchone())
        self.assertEqual(request['category'], 'CONTROL_PLANE_DEGRADED')
        self.assertTrue(request['summary'].startswith(DEGRADED))
        with self.assertRaises(ProtocolError):
            HumanGateway(self.store).decide(SimulationSession('synthetic-supervisor', True), request['id'], request['scope'], 'APPROVE', 132)
        self.assertEqual(self.executions(), 0)

    def test_exact_replay_is_idempotent_changed_replay_rejected(self):
        message = self.task()
        self.assertFalse(self.store.submit('brain', message, 101))
        changed = dict(message, correlation_id='other-correlation')
        with self.assertRaises(ProtocolError):
            self.store.submit('brain', changed, 101)
        self.runner.tick(102)
        self.assertIsNone(self.runner.tick(103))
        self.assertEqual(self.executions(), 1)

    def test_wrong_route_and_out_of_order_are_atomic_rejections(self):
        message = envelope('TASK', 'brain', 'heg', 'task-test', 'corr-test', {'action': 'synthetic_check', 'parameters': {}}, 1, 100)
        with self.assertRaises(ProtocolError):
            self.store.submit('brain', message, 100)
        message['recipient'] = 'runner'
        message['sequence'] = 2
        with self.assertRaises(ProtocolError):
            self.store.submit('brain', message, 100)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0], 0)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM messages').fetchone()[0], 0)
        self.task()
        self.assertEqual(self.runner.tick(101)['state'], 'SUCCEEDED')

    def test_pause_persists_across_restart(self):
        self.task()
        self.brain.control('PAUSE', 101)
        self.restart()
        self.assertIsNone(self.runner.tick(102))
        self.assertEqual(self.store.task('task-test')['state'], 'QUEUED')
        self.brain.control('RESUME', 103)
        self.assertEqual(self.runner.tick(104)['state'], 'SUCCEEDED')

    def test_whatsapp_failure_independent_simulated_email_is_not_approval(self):
        self.task('gated_shadow_note')
        self.runner.tick(101)
        gateway = HumanGateway(self.store, SimulatedNotifications(whatsapp=False, email=True))
        gateway.tick(102)
        channels = {r['channel']: dict(r) for r in self.store.db.execute('SELECT * FROM deliveries')}
        self.assertEqual(channels['whatsapp']['state'], 'RETRY_WAIT')
        self.assertEqual(channels['email']['state'], 'ACKNOWLEDGED')
        gateway.tick(103)
        self.assertEqual(self.store.db.execute('SELECT sum(attempts) FROM deliveries').fetchone()[0], 2)
        self.assertEqual(self.store.task('task-test')['state'], 'NEEDS_HUMAN')
        self.assertIsNone(self.runner.tick(104))
        self.assertEqual(self.executions(), 0)

    def test_unavailable_notifications_timeout_keeps_task_non_executable(self):
        self.task('gated_shadow_note')
        self.runner.tick(101)
        gateway = HumanGateway(self.store, SimulatedNotifications(whatsapp=False, email=False))
        for now in (102, 104, 108, 116):
            gateway.tick(now)
        deliveries = list(self.store.db.execute('SELECT * FROM deliveries'))
        self.assertEqual(len(deliveries), 2)
        self.assertTrue(all(r['attempts'] == 3 and r['state'] == 'FAILED' for r in deliveries))
        gateway.tick(401)
        self.assertEqual(self.store.task('task-test')['state'], 'HUMAN_TIMEOUT')
        self.assertIsNone(self.runner.tick(402))
        self.assertEqual(self.executions(), 0)
        self.store.verify_audit()


if __name__ == '__main__':
    unittest.main()
