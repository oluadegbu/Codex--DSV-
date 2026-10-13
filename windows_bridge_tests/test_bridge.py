"""Authenticated transport/controller tests and official protocol fixtures.

No fixture here claims a genuine Windows Codex turn or OS Job Object proof.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import ssl
import subprocess
import tempfile
import threading
import time
import unittest

from dci.bridge.protocol import ProtocolError, canonical
from dci.master.planner import PortfolioPlanner
from dci.master.registry import PortfolioRegistry
from dci.master.windows_protocol import PeerKey, EXPECTED_ARTIFACT, WORKSPACE_ID, route, sha, sign, verify, endpoint
from dci.master.windows_controller import AtomicPeerStore, WindowsController
from dci.master.windows_worker import (WorkerJournal, OutboundWorker, AppServerMachine, HttpsTransport,
                                      bridge_fingerprint, scratch_manifest_digest)
from dci.master.windows_bridge_cli import handler_factory

ROOT = Path(__file__).resolve().parents[1]


class Harness:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.key = PeerKey("windows_codex_shadow", "synthetic-pair", int(time.time()) + 3600, os.urandom(32))
        self.fingerprint = bridge_fingerprint()
        workspace = self.directory / "route"; workspace.mkdir()
        self.config = {"schema_version": 1, "mode": "SHADOW", "max_parallel": 1, "max_memory_mb": 256,
                       "workers": [{"worker_id": self.key.worker_id, "project_ids": ["DCI"], "workspace": str(workspace),
                                    "expected_commit": "a" * 40, "source_sha256": {}, "max_seconds": 20,
                                    "memory_mb": 256, "cpu_seconds": 10, "max_output_bytes": 1048576}]}
        self.identity = {"host": "FIXTURE-WINDOWS", "user": "FIXTURE-WINDOWS\\DirectiveCodex", "administrator": False,
                         "integrity": "Medium", "workspace_id": WORKSPACE_ID, "scratch_manifest_sha256": scratch_manifest_digest(),
                         "git_head": "b" * 40, "bridge_sha256": self.fingerprint, "execution_kind": "CONTRACT_FIXTURE", "codex_version": "0.162.1"}
        self.executions = 0
        self.open_controller()
        self.open_worker()

    def open_controller(self):
        self.server_store = AtomicPeerStore(self.directory / "controller.sqlite")
        planner = PortfolioPlanner(self.server_store, PortfolioRegistry(ROOT / "portfolio/REGISTRY.v1.json"), self.config, ROOT)
        self.controller = WindowsController(planner, self.key, "FIXTURE-WINDOWS", self.fingerprint, fixture_mode=True)

    def open_worker(self, transport=None):
        self.worker_store = WorkerJournal(self.directory / "worker.sqlite", sha(self.identity))
        self.worker = OutboundWorker(self.worker_store, self.key, self.identity, transport or self.transport, self.execute, self.fingerprint)

    def close(self):
        self.server_store.close(); self.worker_store.close()

    def submit(self, task="one"):
        self.controller.submit({"task_id": task, "correlation_id": "corr-" + task, "project_id": "DCI"}, int(time.time()))

    def transport(self, packet):
        return self.controller.receive(packet, int(time.time()))

    def report(self, status="SUCCEEDED"):
        return {"status": status, "artifact": copy.deepcopy(EXPECTED_ARTIFACT) if status == "SUCCEEDED" else None,
                "artifact_sha256": sha(EXPECTED_ARTIFACT) if status == "SUCCEEDED" else None, "identity": self.identity,
                "pid": 1234, "thread_id": "synthetic-thread", "turn_id": "synthetic-turn",
                "turn_status": "completed" if status == "SUCCEEDED" else "interrupted", "job_active_processes": 0,
                "git_after": self.identity["git_head"], "transcript_sha256": "c" * 64,
                "interrupt_acknowledged": status == "CANCELLED"}

    def execute(self, task, cancelled):
        self.executions += 1
        return self.report("CANCELLED" if cancelled() else "SUCCEEDED")


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dmb-windows-bridge-test-")
        self.h = Harness(self.temp.name)

    def tearDown(self):
        self.h.close(); self.temp.cleanup()

    def test_authenticated_dispatch_result_and_duplicate_poll(self):
        self.h.submit(); self.h.worker.step(); self.h.worker.step()
        self.assertEqual(self.h.executions, 1)
        self.assertEqual(self.h.server_store.task("one")["state"], "SUCCEEDED")
        self.assertEqual(self.h.server_store.db.execute("SELECT count(*) FROM executions").fetchone()[0], 1)
        self.h.server_store.verify_audit(); self.h.worker_store.verify_audit()
        self.assertTrue(self.h.controller.report()["windows_bridge"]["fixture_mode"])

    def test_lost_offer_reply_does_not_claim_twice(self):
        self.h.submit(); lost = []
        def transport(packet):
            answer = self.h.transport(packet)
            if packet["kind"] == "POLL" and not lost:
                lost.append(True); raise OSError("synthetic lost reply after commit")
            return answer
        self.h.worker.transport = transport
        self.h.worker.step()
        self.assertEqual(self.h.executions, 1)
        self.assertEqual(self.h.server_store.task("one")["attempts"], 1)
        self.assertEqual(self.h.server_store.db.execute("SELECT count(*) FROM win_offers").fetchone()[0], 1)

    def test_worker_restart_resends_result_without_reexecution(self):
        self.h.submit()
        def offline_result(packet):
            if packet["kind"] == "RESULT": raise OSError("synthetic offline")
            return self.h.transport(packet)
        self.h.worker.transport = offline_result
        with self.assertRaises(RuntimeError): self.h.worker.step()
        self.assertEqual(self.h.executions, 1)
        self.h.worker_store.close(); self.h.open_worker()
        self.h.worker.recover()
        self.assertEqual(self.h.executions, 1)
        self.assertEqual(self.h.server_store.task("one")["state"], "SUCCEEDED")
        self.assertEqual(self.h.worker_store.db.execute("SELECT state FROM win_local_jobs").fetchone()[0], "ACKED")

    def test_controller_restart_and_lost_completion_ack(self):
        self.h.submit(); lost = []
        def transport(packet):
            answer = self.h.transport(packet)
            if packet["kind"] == "RESULT" and not lost:
                lost.append(True); self.h.server_store.close(); self.h.open_controller()
                raise OSError("synthetic controller stopped after commit")
            return answer
        self.h.worker.transport = transport; self.h.worker.step()
        self.assertEqual(self.h.executions, 1)
        self.assertEqual(self.h.server_store.db.execute("SELECT count(*) FROM executions").fetchone()[0], 1)
        self.assertEqual(self.h.server_store.db.execute("SELECT count(*) FROM messages WHERE kind='RESULT'").fetchone()[0], 1)

    def test_unknown_started_worker_restart_quarantines_and_never_runs(self):
        self.h.submit(); self.h.worker.rpc("HELLO", self.h.identity); data = self.h.worker.rpc("POLL", {})
        task = data["task"]; self.h.worker.rpc("START", route(task))
        with self.h.worker_store.tx(): self.h.worker_store.db.execute("UPDATE win_local_jobs SET state='EXECUTING'")
        self.h.worker_store.close(); self.h.open_worker(); self.h.worker.recover()
        self.assertEqual(self.h.executions, 0)
        self.assertEqual(self.h.server_store.task("one")["state"], "NEEDS_HUMAN")
        self.assertTrue(self.h.controller.report()["held_resources"])
        self.assertEqual(self.h.controller.planner.claim(int(time.time())), [])

    def test_wrong_key_tampering_reflection_and_stale_packets(self):
        packet = sign(self.h.key, "worker_to_controller", "HELLO", 1, self.h.identity, int(time.time()))
        for field, value in (("worker_id", "other"), ("direction", "controller_to_worker"), ("mac", "é"), ("payload", {})):
            bad = copy.deepcopy(packet); bad[field] = value
            with self.assertRaises((PermissionError, ProtocolError)): self.h.transport(bad)
        with self.assertRaises(PermissionError): self.h.controller.receive(packet, int(time.time()) + 61)
        wrong = PeerKey(self.h.key.worker_id, self.h.key.key_id, self.h.key.expires, os.urandom(32))
        with self.assertRaises(PermissionError): verify(wrong, packet, "worker_to_controller", int(time.time()))
        self.assertEqual(self.h.server_store.db.execute("SELECT count(*) FROM win_requests").fetchone()[0], 0)

    def test_replay_conflict_and_out_of_order_rejection(self):
        packet = sign(self.h.key, "worker_to_controller", "HELLO", 1, self.h.identity, int(time.time()))
        self.h.transport(packet); self.h.transport(packet)
        duplicate = sign(self.h.key, "worker_to_controller", "HELLO", 1, self.h.identity, int(time.time()))
        with self.assertRaises(ProtocolError): self.h.transport(duplicate)
        out_of_order = sign(self.h.key, "worker_to_controller", "POLL", 3, {}, int(time.time()))
        with self.assertRaises(ProtocolError): self.h.transport(out_of_order)

    def test_atomic_failed_result_does_not_consume_sequence_or_unlock(self):
        self.h.submit(); self.h.worker.rpc("HELLO", self.h.identity); task = self.h.worker.rpc("POLL", {})["task"]
        self.h.worker.rpc("START", route(task)); report = self.h.report(); report["artifact"]["answer"] = "WRONG"
        payload = {"route": route(task), "report": report}
        packet = sign(self.h.key, "worker_to_controller", "RESULT", 4, payload, int(time.time()))
        with self.assertRaises(ProtocolError): self.h.transport(packet)
        self.assertEqual(self.h.server_store.task("one")["state"], "RUNNING")
        self.assertEqual(self.h.server_store.db.execute("SELECT max(seq) FROM win_requests").fetchone()[0], 3)
        self.assertTrue(self.h.controller.report()["held_resources"])

    def test_production_controller_rejects_fixture_identity_and_admin(self):
        with self.assertRaises(PermissionError):
            self.h.controller.fixture_mode = False
            self.h.worker.rpc("HELLO", self.h.identity)
        self.h.controller.fixture_mode = True
        for alteration in ({"administrator": True}, {"integrity": "High"}, {"bridge_sha256": "0" * 64}, {"workspace_id": "DAT"}):
            value = {**self.h.identity, **alteration}
            with self.assertRaises(PermissionError): self.h.controller._identity(value)

    def test_cancel_requires_interrupt_receipt_and_retains_exact_route(self):
        self.h.submit(); self.h.worker.rpc("HELLO", self.h.identity); task = self.h.worker.rpc("POLL", {})["task"]
        self.h.controller.cancel("one", int(time.time()))
        self.h.worker.step()
        self.assertEqual(self.h.server_store.task("one")["state"], "FAILED")
        self.assertFalse(self.h.controller.report()["held_resources"])

    def test_expired_dispatch_is_not_revived(self):
        self.h.submit(); self.h.worker.rpc("HELLO", self.h.identity); task = self.h.worker.rpc("POLL", {})["task"]
        self.h.controller.planner.recover(task["lease"])
        packet = sign(self.h.key, "worker_to_controller", "RESULT", 3,
                      {"route": route(task), "report": self.h.report()}, task["lease"])
        with self.assertRaises(ProtocolError): self.h.controller.receive(packet, task["lease"])
        self.assertEqual(self.h.server_store.task("one")["state"], "NEEDS_HUMAN")
        self.assertTrue(self.h.controller.report()["held_resources"])

    def test_cancellation_without_interrupt_ack_cannot_release_resources(self):
        self.h.submit(); self.h.worker.rpc("HELLO", self.h.identity)
        task = self.h.worker.rpc("POLL", {})["task"]; self.h.worker.rpc("START", route(task))
        self.h.controller.cancel("one", int(time.time()))
        report = self.h.report("CANCELLED"); report["interrupt_acknowledged"] = False
        with self.assertRaises(ProtocolError): self.h.worker.rpc("RESULT", {"route": route(task), "report": report})
        self.assertEqual(self.h.server_store.task("one")["state"], "RUNNING")
        self.assertTrue(self.h.controller.report()["held_resources"])

    def test_authentication_failure_not_retried_and_outbox_preserved(self):
        attempts = []
        def denied(packet):
            attempts.append(packet); raise PermissionError("synthetic revoked pairing")
        self.h.worker.transport = denied
        with self.assertRaises(PermissionError): self.h.worker.rpc("HELLO", self.h.identity)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(self.h.worker_store.db.execute("SELECT count(*) FROM win_outbox WHERE ack=0").fetchone()[0], 1)

    def test_general_shell_task_fields_and_endpoint_redirects_forbidden(self):
        with self.assertRaises(ProtocolError): self.h.controller.submit({"task_id": "one", "correlation_id": "corr", "project_id": "DCI", "command": "powershell"}, int(time.time()))
        for url in ("http://example.invalid/v1/dmb/windows", "https://user:pass@example.invalid/v1/dmb/windows", "https://example.invalid/v1/dmb/windows?key=x"):
            with self.assertRaises(PermissionError): endpoint(url)


class AppServerTests(unittest.TestCase):
    def ready(self):
        machine = AppServerMachine("C:\\scratch")
        machine.receive({"id": 1, "result": {}})
        machine.receive({"id": 2, "result": {"cwd": "C:\\scratch", "approvalPolicy": "never", "sandbox": {"type": "readOnly"}, "thread": {"id": "thread"}}})
        machine.receive({"id": 3, "result": {"turn": {"id": "turn"}}})
        return machine

    def test_supported_completed_turn_and_artifact(self):
        machine = self.ready()
        machine.receive({"method": "item/completed", "params": {"threadId": "thread", "turnId": "turn", "item": {"type": "agentMessage", "text": canonical(EXPECTED_ARTIFACT)}}})
        machine.receive({"method": "turn/completed", "params": {"threadId": "thread", "turn": {"id": "turn", "status": "completed"}}})
        self.assertEqual(machine.status, "completed"); self.assertEqual(machine.artifact, EXPECTED_ARTIFACT)

    def test_interrupt_ack_and_terminal_status_are_separate(self):
        machine = self.ready(); request = machine.interrupt()[0]
        self.assertEqual(request["method"], "turn/interrupt"); self.assertIsNone(machine.status)
        machine.receive({"id": 4, "result": {}}); self.assertTrue(machine.interrupt_acked); self.assertIsNone(machine.status)
        machine.receive({"method": "turn/completed", "params": {"threadId": "thread", "turn": {"id": "turn", "status": "interrupted"}}})
        self.assertEqual(machine.status, "interrupted")

    def test_tools_approvals_policy_drift_and_wrong_route_fail_closed(self):
        machine = self.ready()
        machine.receive({"method": "item/started", "params": {"threadId": "thread", "turnId": "turn", "item": {"type": "commandExecution"}}})
        self.assertTrue(machine.blocked); self.assertTrue(machine.interrupt_sent)
        machine = self.ready(); replies = machine.receive({"id": 99, "method": "item/commandExecution/requestApproval", "params": {}})
        self.assertIn("error", replies[0]); self.assertTrue(machine.blocked)
        with self.assertRaises(ProtocolError): self.ready().receive({"method": "turn/completed", "params": {"threadId": "other", "turn": {"id": "turn", "status": "completed"}}})
        with self.assertRaises(PermissionError): AppServerMachine("C:\\scratch").receive({"id": 2, "result": {"cwd": "C:\\production", "approvalPolicy": "never", "sandbox": {"type": "readOnly"}, "thread": {"id": "x"}}})

    def test_real_windows_primitives_refuse_linux(self):
        if os.name != "nt":
            from dci.master.windows_native import require_identity, dpapi
            with self.assertRaises(PermissionError): require_identity()
            with self.assertRaises(PermissionError): dpapi(b"synthetic")


class HttpsTests(unittest.TestCase):
    def test_real_tls_poll_dispatch_result_and_restart_fixture(self):
        with tempfile.TemporaryDirectory(prefix="dmb-windows-tls-") as directory:
            base = Path(directory); h = Harness(base)
            h.submit(); h.server_store.close()
            certificate, private_key = base / "certificate.pem", base / "private.key"
            subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(private_key), "-out", str(certificate),
                            "-days", "1", "-subj", "/CN=localhost", "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost"], capture_output=True, check=True, timeout=10)
            ready, stop = threading.Event(), threading.Event(); shared, errors = {}, []
            def serve():
                try:
                    h.open_controller()
                    from http.server import HTTPServer
                    server = HTTPServer(("127.0.0.1", 0), handler_factory(h.controller)); server.timeout = .05
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(certificate, private_key)
                    server.socket = context.wrap_socket(server.socket, server_side=True)
                    shared["port"] = server.server_port; ready.set()
                    while not stop.is_set(): server.handle_request()
                    server.server_close(); shared["state"] = h.server_store.task("one")["state"]
                    h.server_store.verify_audit(); h.server_store.close()
                except BaseException as exc:
                    errors.append(exc); ready.set()
            thread = threading.Thread(target=serve); thread.start()
            try:
                self.assertTrue(ready.wait(5)); self.assertFalse(errors, errors)
                transport = HttpsTransport("https://127.0.0.1:" + str(shared["port"]) + "/v1/dmb/windows", str(certificate))
                h.worker.transport = transport; outcome = h.worker.step()
                self.assertEqual(outcome["status"], "SUCCEEDED"); self.assertEqual(h.executions, 1)
            finally:
                stop.set(); thread.join(5); h.worker_store.close()
            self.assertFalse(thread.is_alive()); self.assertFalse(errors, errors)
            self.assertEqual(shared["state"], "SUCCEEDED")


if __name__ == "__main__":
    unittest.main()
