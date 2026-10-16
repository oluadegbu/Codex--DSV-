"""Integration checks execute actual deterministic workers, never mock Codex certification."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from dci.bridge.store import BridgeStore
from dci.bridge.protocol import ProtocolError
from dci.master.planner import PortfolioPlanner
from dci.master.registry import PortfolioRegistry
from dci.master.control_plane import ShadowControlPlane, atomic_json
from dci.master.runtime_cli import RuntimeMcp

ROOT = Path(__file__).resolve().parents[1]


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="dmb-runtime-tests-")
        cls.base = Path(cls.directory.name)
        cls.manifest = cls.base / "workers.json"
        subprocess.run([sys.executable, str(ROOT / "tools/prepare_shadow_research_worker.py"),
                        "--destination", str(cls.base / "worker"), "--manifest", str(cls.manifest)], check=True, capture_output=True, timeout=20)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.base)
        self.db = Path(self.temp.name) / "state.sqlite"
        self.open()

    def open(self):
        self.store = BridgeStore(self.db)
        self.planner = PortfolioPlanner(self.store, PortfolioRegistry(ROOT / "portfolio/REGISTRY.v1.json"), self.manifest, ROOT)
        self.runtime = ShadowControlPlane(self.planner)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def submit(self, task="one", **extras):
        return self.runtime.submit({"task_id": task, "correlation_id": "corr-" + task, "project_id": "DCI", **extras}, int(time.time()))

    def dispatch(self):
        job = self.planner.claim(int(time.time()))[0]
        evidence = self.runtime.dispatch(job)
        self.assertEqual(evidence["outcome"], "COMPLETE", evidence)
        return job, evidence

    def test_real_pipeline_dependency_and_duplicate_intake(self):
        self.submit(); self.submit("dependent", dependencies=["one"])
        first = self.runtime.tick(); self.runtime.tick()
        self.assertEqual(self.store.task("dependent")["state"], "SUCCEEDED")
        result = json.loads((Path(first["executed"][0]["artifact"]) / "result.json").read_text())
        self.assertEqual([e["type"] for e in result["audit"]], ["paper_entry", "paper_mark", "paper_exit"])
        self.assertTrue(first["executed"][0]["process_group_terminated"])
        self.submit(); self.assertEqual(self.runtime.tick()["executed"], [])
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM executions").fetchone()[0], 2)
        self.store.verify_audit()

    def test_restart_recovers_receipt_without_launching_again(self):
        self.submit(); job, evidence = self.dispatch()
        self.store.close(); self.open()
        with patch.object(self.runtime, "dispatch", side_effect=AssertionError("worker reexecution forbidden")):
            recovered = self.runtime.tick()
        self.assertEqual(recovered["recovered_without_reexecution"], ["one"])
        self.assertEqual(recovered["executed"], [])
        self.assertEqual(self.store.task("one")["state"], "SUCCEEDED")
        self.assertEqual(self.store.task("one")["attempts"], job["attempts"])
        self.assertFalse(self.runtime.report()["held_resources"])

    def test_terminal_commit_gap_recovery_does_not_emit_duplicate_result(self):
        self.submit(); job, evidence = self.dispatch()
        self.planner.finish(job, evidence, int(time.time()))
        before = self.store.db.execute("SELECT count(*) FROM messages WHERE kind='RESULT'").fetchone()[0]
        self.store.close(); self.open(); self.runtime.recover(int(time.time()))
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM messages WHERE kind='RESULT'").fetchone()[0], before)
        self.assertEqual(self.runtime.report()["control_plane"]["dispatches"][0]["state"], "COMMITTED")

    def test_corrupt_receipt_and_output_quarantine_keep_reservation(self):
        self.submit(); job, evidence = self.dispatch()
        (Path(evidence["artifact"]) / "result.json").write_text("{}")
        self.assertEqual(self.runtime.recover(int(time.time())), [])
        self.assertEqual(self.store.task("one")["state"], "NEEDS_HUMAN")
        self.assertTrue(self.runtime.report()["held_resources"])
        self.assertFalse(self.planner.claim(int(time.time())))

    def test_valid_receipt_cannot_revive_expired_lease(self):
        self.submit(); job, evidence = self.dispatch()
        self.assertEqual(self.runtime.recover(job["lease"]), [])
        self.assertEqual(self.store.task("one")["state"], "NEEDS_HUMAN")
        self.assertTrue(self.runtime.report()["held_resources"])

    def test_unknown_started_process_is_never_retried(self):
        self.submit(); job, evidence = self.dispatch()
        (Path(evidence["artifact"]) / "receipt.json").unlink()
        self.store.close(); self.open()
        self.runtime.recover(job["lease"])
        self.assertEqual(self.store.task("one")["state"], "NEEDS_HUMAN")
        self.assertEqual(self.planner.claim(job["lease"] + 1), [])
        self.assertEqual(self.store.task("one")["attempts"], 1)

    def test_wrong_route_receipt_rejected(self):
        self.submit(); job, evidence = self.dispatch()
        receipt = Path(evidence["artifact"]) / "receipt.json"
        value = json.loads(receipt.read_text()); value["correlation_id"] = "wrong"
        atomic_json(receipt, value)
        self.runtime.recover(int(time.time()))
        self.assertEqual(self.store.task("one")["state"], "NEEDS_HUMAN")

    def test_intake_and_local_mcp_reject_commands_and_uncertified_codex(self):
        for extra in ({"command": "whoami"}, {"operation": "codex_review"}, {"project_id": "DAT_MT5"}, {"dependencies": "one"}):
            with self.assertRaises(ProtocolError): self.submit(**extra)
        server = RuntimeMcp(self.runtime)
        server.request({"method": "initialize"}, int(time.time()))
        server.request({"method": "notifications/initialized"}, int(time.time()))
        result = server.request({"method": "tools/call", "params": {"name": "dmb_submit_job", "arguments":
                                {"task_id": "mcp", "correlation_id": "corr-mcp", "project_id": "DCI"}}}, int(time.time()))
        self.assertEqual(result["structuredContent"]["state"], "QUEUED")
        self.runtime.tick()
        self.assertEqual(self.store.task("mcp")["state"], "SUCCEEDED")

    def test_actual_owned_process_cancellation(self):
        self.submit()
        original = subprocess.Popen
        signal_sent = threading.Event()
        errors = []
        def start(argv, **kwargs):
            proc = original(argv, **kwargs)
            if len(argv) > 2 and str(argv[2]).endswith("shadow_research_entry.py"):
                # Fault injection stops only this newly-created test worker, so
                # the normal cancel endpoint has time to observe it running.
                os.kill(proc.pid, signal.SIGSTOP)
                def cancel():
                    try:
                        args = [sys.executable, "-m", "dci.master.runtime_cli", "--workspace", str(ROOT),
                                "--database", str(self.db), "--workers", str(self.manifest), "cancel", "--task-id", "one"]
                        env = os.environ.copy(); env["PYTHONPATH"] = str(ROOT / "src")
                        child = original(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = child.communicate(timeout=5)
                        if child.returncode: raise RuntimeError(stderr.decode())
                        self.assertTrue(json.loads(stdout)["requested"])
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        signal_sent.set()
                threading.Thread(target=cancel, daemon=True).start()
            return proc
        with patch("dci.master.control_plane.subprocess.Popen", side_effect=start):
            result = self.runtime.tick()
        self.assertTrue(signal_sent.wait(5)); self.assertFalse(errors, errors)
        evidence = result["executed"][0]
        self.assertTrue(evidence["cancelled"]); self.assertTrue(evidence["process_group_terminated"])
        self.assertEqual(self.store.task("one")["state"], "FAILED")
        self.assertFalse(self.runtime.report()["held_resources"])
        self.assertEqual(self.runtime.tick()["executed"], [])


if __name__ == "__main__":
    unittest.main()
