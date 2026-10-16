import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dci.bridge.brain import BrainTools, LocalMcpPrototype
from dci.bridge.heg import HumanGateway, SimulatedNotifications, SimulationSession
from dci.bridge.hands import HandsAdapter
from dci.bridge.protocol import ProtocolError, envelope, validate
from dci.bridge.runner import Runner, DEGRADED
from dci.bridge.store import BridgeStore

ROOT = Path(__file__).parents[1]


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'bridge.sqlite'
        self.store = BridgeStore(self.path)
        self.brain = BrainTools(self.store)
        self.runner = Runner(self.store, ROOT)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def task(self, action='synthetic_check', now=1000, ttl=3600):
        return self.store.create_task(action, now, ttl)

    def request(self):
        t = self.task('gated_shadow_note')
        self.runner.tick(1001)
        request = dict(self.store.db.execute('SELECT * FROM escalations WHERE task=?', (t['task_id'],)).fetchone())
        return t, request

    def test_100_cycles_zero_lost_or_duplicate_executions(self):
        for i in range(100):
            t = self.task(now=1000+i)
            self.assertFalse(self.store.submit('brain', t, 1000+i))
            result = self.runner.tick(1000+i)
            self.assertEqual(result['state'], 'SUCCEEDED')
            self.assertEqual(result['attempts'], 1)
            returned = self.brain.get_status(t['task_id'])
            self.assertEqual(returned['correlation_id'], t['correlation_id'])
            self.assertTrue(returned['result']['passed'])
        self.assertIsNone(self.runner.tick(1200))
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM executions').fetchone()[0], 100)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM tasks WHERE state='SUCCEEDED'").fetchone()[0], 100)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM messages WHERE kind='RESULT'").fetchone()[0], 100)
        self.store.verify_audit()

    def test_wrong_route_writer_and_operation_rejected(self):
        for change in ({'recipient': 'hands'}, {'sender': 'hands'}, {'payload': {'action': 'rm -rf /', 'parameters': {}}}, {'payload': {'action': 'synthetic_check', 'parameters': {'shell': 'whoami'}}}, {'version': 2}):
            m = envelope('TASK', 'brain', 'runner', 'task', 'correlation', {'action': 'synthetic_check', 'parameters': {}}, 1, 1000)
            m.update(change)
            with self.assertRaises(ProtocolError):
                self.store.submit('brain', m, 1000)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0], 0)

    def test_replay_conflict_out_of_order_and_task_reuse(self):
        m = self.task()
        altered = {**m, 'payload': {'action': 'fixture_replay', 'parameters': {}}}
        with self.assertRaises(ProtocolError):
            self.store.submit('brain', altered, 1000)
        for seq in (1, 3):
            bad = envelope('TASK', 'brain', 'runner', 'other', 'corr', {'action': 'synthetic_check', 'parameters': {}}, seq, 1000)
            with self.assertRaises(ProtocolError):
                self.store.submit('brain', bad, 1000)
        with self.assertRaises(ProtocolError):
            self.store.create_task('synthetic_check', 1000, task_id=m['task_id'])
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0], 1)

    def test_brain_response_loss_retry_preserves_task_and_correlation(self):
        first = self.brain.submit_task('synthetic_check', 'stable-task', 'stable-corr', 1000)
        retried = self.brain.submit_task('synthetic_check', 'stable-task', 'stable-corr', 1001)
        self.assertEqual(first, retried)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0], 1)
        with self.assertRaises(ProtocolError):
            self.brain.submit_task('fixture_replay', 'stable-task', 'stable-corr', 1002)
        with self.assertRaises(ProtocolError):
            self.brain.submit_task('synthetic_check', 'stable-task', 'wrong-corr', 1002)
        self.assertEqual(self.runner.tick(1002)['state'], 'SUCCEEDED')

    def test_pause_resume_and_task_timeout(self):
        t = self.task(ttl=10)
        self.brain.control('PAUSE', 1001)
        self.assertIsNone(self.runner.tick(1002))
        self.assertEqual(self.store.task(t['task_id'])['state'], 'QUEUED')
        self.brain.control('RESUME', 1003)
        self.assertEqual(self.runner.tick(1003)['state'], 'SUCCEEDED')
        expired = self.task(now=1010, ttl=1)
        self.runner.tick(1011)
        self.assertEqual(self.store.task(expired['task_id'])['state'], 'EXPIRED')

    def test_envelope_expiry_and_boolean_sequence_rejected(self):
        m = envelope('TASK', 'brain', 'runner', 'task', 'corr', {'action': 'synthetic_check', 'parameters': {}}, 1, 1000, ttl=1)
        for now in (999, 1001):
            with self.assertRaises(ProtocolError):
                self.store.submit('brain', m, now)
        m['sequence'] = True
        with self.assertRaises(ProtocolError):
            self.store.submit('brain', m, 1000)

    def test_prestart_retry_is_bounded_and_audited(self):
        t = self.task('codex_review')
        self.runner.tick(1000)
        self.assertEqual(self.store.task(t['task_id'])['state'], 'RETRY_WAIT')
        self.assertIsNone(self.runner.tick(1001))
        self.runner.tick(1002)
        self.runner.tick(1006)
        state = self.store.task(t['task_id'])
        self.assertEqual(state['attempts'], 3)
        self.assertEqual(state['state'], 'NEEDS_HUMAN')
        summary = self.store.db.execute('SELECT summary FROM escalations').fetchone()[0]
        self.assertTrue(summary.startswith(DEGRADED))

    def test_crash_restart_recovery_and_stale_completion_fence(self):
        t = self.task()
        claimed = self.runner.claim(1001)
        self.store.close()
        self.store = BridgeStore(self.path)
        self.runner = Runner(self.store, ROOT)
        self.runner.recover(1031)
        self.assertEqual(self.store.task(t['task_id'])['state'], 'NEEDS_HUMAN')
        with self.assertRaises(RuntimeError):
            self.runner.finish(claimed, 1032, {'passed': True})
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM executions').fetchone()[0], 0)

    def test_ambiguous_external_outcome_not_retried(self):
        class UncertainHands:
            calls = 0
            def execute(self, action, workspace):
                self.calls += 1
                raise TimeoutError('process may have completed')
        hands = UncertainHands()
        t = self.task('codex_review')
        runner = Runner(self.store, ROOT, hands)
        runner.tick(1000)
        runner.tick(2000)
        self.assertEqual(hands.calls, 1)
        self.assertEqual(self.store.task(t['task_id'])['state'], 'NEEDS_HUMAN')

    def test_codex_runtime_fault_is_control_degradation_not_routine_failure(self):
        class BlockedCodex:
            def execute(self, action, workspace):
                return {'passed': False, 'turn_completed': False, 'exit_code': 1}
        t = self.task('codex_review')
        state = Runner(self.store, ROOT, BlockedCodex()).tick(1000)
        self.assertEqual(state['state'], 'NEEDS_HUMAN')
        self.assertIn('turn_completed', state['result'])
        self.assertEqual(self.store.db.execute('SELECT category FROM escalations').fetchone()[0], 'CONTROL_PLANE_DEGRADED')

    def test_expired_execution_fails_closed(self):
        t = self.task(ttl=2)
        claimed = self.runner.claim(1000)
        with self.assertRaises(RuntimeError):
            self.runner.finish(claimed, 1003, {'passed': True})
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM executions').fetchone()[0], 0)

    def test_human_approval_exact_identity_scope_expiry_and_replay(self):
        t, request = self.request()
        gateway = HumanGateway(self.store)
        for session in (SimulationSession('attacker', True), SimulationSession('synthetic-supervisor', False)):
            with self.assertRaises(PermissionError):
                gateway.decide(session, request['id'], request['scope'], 'APPROVE', 1002)
        with self.assertRaises(ProtocolError):
            gateway.decide(SimulationSession('synthetic-supervisor', True), request['id'], '0'*64, 'APPROVE', 1002)
        gateway.decide(SimulationSession('synthetic-supervisor', True), request['id'], request['scope'], 'APPROVE', 1002)
        with self.assertRaises(ProtocolError):
            gateway.decide(SimulationSession('synthetic-supervisor', True), request['id'], request['scope'], 'APPROVE', 1003)
        self.assertEqual(self.runner.tick(1003)['state'], 'SUCCEEDED')

    def test_human_rejection_and_timeout(self):
        t, request = self.request()
        g = HumanGateway(self.store)
        g.decide(SimulationSession('synthetic-supervisor', True), request['id'], request['scope'], 'REJECT', 1002)
        self.assertEqual(self.store.task(t['task_id'])['state'], 'REJECTED')
        t2, r2 = self.request()
        g.tick(r2['expires'])
        self.assertEqual(self.store.task(t2['task_id'])['state'], 'HUMAN_TIMEOUT')
        with self.assertRaises(ProtocolError):
            g.decide(SimulationSession('synthetic-supervisor', True), r2['id'], r2['scope'], 'APPROVE', r2['expires'])

    def test_whatsapp_failure_independent_email_ack_is_not_approval(self):
        t, request = self.request()
        g = HumanGateway(self.store, SimulatedNotifications(whatsapp=False, email=True))
        g.tick(1002)
        g.tick(1003)
        g.tick(1008)
        rows = {row['channel']: dict(row) for row in self.store.db.execute('SELECT * FROM deliveries')}
        self.assertEqual(rows['email']['state'], 'ACKNOWLEDGED')
        self.assertEqual(rows['email']['attempts'], 1)
        self.assertEqual(rows['whatsapp']['state'], 'RETRY_WAIT')
        self.assertEqual(rows['whatsapp']['attempts'], 1)
        self.assertEqual(self.store.task(t['task_id'])['state'], 'NEEDS_HUMAN')
        self.assertIsNone(self.store.db.execute('SELECT decision FROM escalations').fetchone()[0])

    def test_both_notifications_fail_keep_task_blocked_unrelated_proceeds(self):
        t, request = self.request()
        g = HumanGateway(self.store, SimulatedNotifications(False, False))
        for now in (1002, 1004, 1008, 1016):
            g.tick(now)
        self.assertTrue(all(row['state'] == 'FAILED' and row['attempts'] == 3 for row in self.store.db.execute('SELECT * FROM deliveries')))
        self.assertEqual(self.store.task(t['task_id'])['state'], 'NEEDS_HUMAN')
        other = self.task(now=1020)
        self.assertEqual(self.runner.tick(1020)['id'], other['task_id'])

    def test_control_degradation_cannot_be_blindly_approved(self):
        t = self.task('codex_review')
        for now in (1000, 1002, 1006):
            self.runner.tick(now)
        r = dict(self.store.db.execute('SELECT * FROM escalations').fetchone())
        with self.assertRaises(ProtocolError):
            HumanGateway(self.store).decide(SimulationSession('synthetic-supervisor', True), r['id'], r['scope'], 'APPROVE', 1007)

    def test_external_provider_activation_rejected(self):
        with self.assertRaises(PermissionError):
            HumanGateway(self.store, object())

    def test_mcp_brain_task_and_result_roundtrip(self):
        server = LocalMcpPrototype(self.brain)
        with self.assertRaises(ProtocolError):
            server.request({'method': 'tools/list'}, 1000)
        server.request({'method': 'initialize'}, 1000)
        server.request({'method': 'notifications/initialized'}, 1000)
        submitted = server.request({'method': 'tools/call', 'params': {'name': 'dci_submit_task', 'arguments': {'action': 'synthetic_check', 'task_id': 'mcp-task', 'correlation_id': 'mcp-corr'}}}, 1000)['structuredContent']
        self.runner.tick(1001)
        response = server.request({'method': 'tools/call', 'params': {'name': 'dci_get_status', 'arguments': {'task_id': submitted['task_id']}}}, 1002)
        self.assertEqual(response['structuredContent']['state'], 'SUCCEEDED')
        self.assertTrue(response['structuredContent']['result']['passed'])
        with self.assertRaises(ProtocolError):
            server.request({'method': 'tools/call', 'params': {'name': 'dci_submit_task', 'arguments': {'action': 'synthetic_check', 'prompt': 'send funds'}}}, 1002)

    def test_unrelated_database_and_corrupt_audit_rejected(self):
        self.task()
        self.store.db.execute("UPDATE audit SET body='{}' WHERE seq=1")
        with self.assertRaises(ProtocolError):
            self.store.verify_audit()
        unrelated = Path(self.tmp.name) / 'other.sqlite'
        with sqlite3.connect(unrelated) as db:
            db.execute('CREATE TABLE dat (id INTEGER)')
        with self.assertRaises(ProtocolError):
            BridgeStore(unrelated)

    def test_non_admin_and_workspace_guard(self):
        with patch('dci.bridge.identity.os.geteuid', return_value=0):
            with self.assertRaises(PermissionError):
                Runner(self.store, ROOT)
        with self.assertRaises(PermissionError):
            Runner(self.store, self.tmp.name)

    def test_standalone_runner_without_conversational_control_plane(self):
        t = self.task()
        result = subprocess.run([sys.executable, '-m', 'dci.bridge', '--database', str(self.path), '--workspace', str(ROOT), '--now', '1001'], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['task']['state'], 'SUCCEEDED')
        self.assertEqual(self.store.task(t['task_id'])['state'], 'SUCCEEDED')

    def test_real_process_crash_after_claim_is_not_reexecuted(self):
        t = self.task()
        code = "import os,sys;from dci.bridge.store import BridgeStore;from dci.bridge.runner import Runner;s=BridgeStore(sys.argv[1]);Runner(s,sys.argv[2]).claim(1001);os._exit(0)"
        result = subprocess.run([sys.executable, '-c', code, str(self.path), str(ROOT)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.runner.tick(1031)
        self.assertEqual(self.store.task(t['task_id'])['state'], 'NEEDS_HUMAN')
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM executions').fetchone()[0], 0)

    def test_mailbox_atomicity_and_single_execution_across_connections(self):
        t = self.task()
        other = BridgeStore(self.path)
        try:
            first_claim = self.runner.claim(1001)
            self.assertIsNotNone(first_claim)
            self.assertIsNone(Runner(other, ROOT).claim(1001))
            self.runner.finish(first_claim, 1002, {'passed': True})
            self.assertEqual(other.task(t['task_id'])['state'], 'SUCCEEDED')
            with self.assertRaises(RuntimeError):
                Runner(other, ROOT).finish(first_claim, 1003, {'passed': True})
            self.assertEqual(other.db.execute('SELECT COUNT(*) FROM executions').fetchone()[0], 1)
        finally:
            other.close()

    def test_simulated_provider_ack_dedup_survives_restart(self):
        t, request = self.request()
        HumanGateway(self.store).tick(1002)
        self.store.close()
        self.store = BridgeStore(self.path)
        HumanGateway(self.store).tick(1003)
        row = self.store.db.execute('SELECT * FROM deliveries').fetchone()
        self.assertEqual(row['attempts'], 1)
        self.assertEqual(self.store.task(t['task_id'])['state'], 'NEEDS_HUMAN')

    def test_all_six_schemas_are_versioned_and_match_runtime_envelope(self):
        from dci.bridge.protocol import FIELDS, KINDS
        for kind in KINDS:
            schema = json.loads((ROOT / 'schemas' / 'bridge' / (kind.lower() + '.v1.schema.json')).read_text())
            self.assertEqual(set(schema['required']), FIELDS)
            self.assertFalse(schema['additionalProperties'])
            self.assertEqual(schema['properties']['kind']['const'], kind)
            self.assertEqual(schema['properties']['version']['const'], 1)

    def test_every_internal_emission_validates_against_protocol(self):
        t, request = self.request()
        HumanGateway(self.store).tick(1002)
        self.store.create_task('synthetic_check', 1002)
        self.runner.tick(1003)
        for row in self.store.db.execute('SELECT body FROM messages'):
            message = json.loads(row[0])
            validate(message, message['sender'], message['issued_at'])

    def test_unknown_database_schema_rejected(self):
        path = Path(self.tmp.name) / 'new-schema.sqlite'
        with sqlite3.connect(path) as db:
            db.execute('PRAGMA user_version=102')
        with self.assertRaises(ProtocolError):
            BridgeStore(path)

    def test_standalone_mcp_protocol_roundtrip(self):
        requests = [
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'dci_submit_task', 'arguments': {'action': 'synthetic_check', 'task_id': 'mcp-task', 'correlation_id': 'mcp-corr'}}}
        ]
        process = subprocess.run([sys.executable, '-m', 'dci.bridge.brain', '--database', str(self.path), '--workspace', str(ROOT)],
                                 input='\n'.join(json.dumps(r) for r in requests)+'\n', capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(responses), 2)
        self.assertIn('task_id', responses[1]['result']['structuredContent'])
        import time
        self.assertEqual(self.runner.tick(int(time.time()))['state'], 'SUCCEEDED')

    def test_hands_fixed_fixture_task_and_no_arbitrary_commands(self):
        evidence = HandsAdapter().execute('fixture_replay', ROOT)
        self.assertTrue(evidence['passed'])
        self.assertEqual(evidence['git_before'], evidence['git_after'])
        with self.assertRaises(PermissionError):
            HandsAdapter().execute('shell:whoami', ROOT)


if __name__ == '__main__':
    unittest.main()
