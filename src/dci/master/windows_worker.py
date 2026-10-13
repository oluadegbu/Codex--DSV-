"""Foreground outbound-only Windows worker, with persistent no-rerun checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from uuid import uuid4

from dci.bridge.store import BridgeStore
from dci.bridge.protocol import ProtocolError, canonical
from .control_plane import atomic_json
from .windows_protocol import (MAX_BYTES, WORKSPACE_ID, PROMPT, EXPECTED_ARTIFACT, OUTPUT_SCHEMA,
                               endpoint, sha, sign, verify, semantic, route, validate_task)

SCRATCH_FILES = {
    "README.md": "Dedicated DMB shadow scratch. No production access or trading.\n",
    "WORKER_SCOPE.json": canonical({"mode": "SHADOW", "workspace_id": WORKSPACE_ID, "owner": "DirectiveCodex"}) + "\n",
}


def scratch_manifest_digest():
    return sha({name: hashlib.sha256(data.encode()).hexdigest() for name, data in SCRATCH_FILES.items()})


def bridge_fingerprint():
    root = Path(__file__).parent
    return sha({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                ("windows_protocol.py", "windows_worker.py", "windows_native.py", "windows_bridge_cli.py")})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise PermissionError("bridge redirects forbidden")


class HttpsTransport:
    def __init__(self, url, ca_file=None):
        self.url = endpoint(url)
        context = ssl.create_default_context()
        if ca_file:
            context.load_verify_locations(cafile=ca_file)
        # Preserve normal proxy/CA protections; never disable TLS/hostname checks.
        self.opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))

    def __call__(self, packet):
        body = canonical(packet).encode()
        request = urllib.request.Request(self.url, body, {"Content-Type": "application/json"}, method="POST")
        with self.opener.open(request, timeout=1) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ProtocolError("oversized bridge reply")
            return json.loads(raw)


class WorkerJournal(BridgeStore):
    def __init__(self, path, binding):
        super().__init__(path)
        with self.tx():
            prior = self.db.execute("SELECT value FROM meta WHERE key='win_worker_v1'").fetchone()
            if prior is None:
                self.db.execute("CREATE TABLE win_outbox(seq INTEGER PRIMARY KEY,id TEXT,kind TEXT,payload TEXT,ack INTEGER DEFAULT 0)")
                self.db.execute("CREATE TABLE win_local_jobs(task TEXT PRIMARY KEY,body TEXT,state TEXT,report TEXT)")
                self.db.execute("INSERT INTO meta VALUES ('win_worker_v1',?)", (binding,))
            elif prior[0] != binding:
                raise PermissionError("worker pairing/context drift; no checkpoint reset")


class OutboundWorker:
    def __init__(self, journal, key, identity, transport, executor, bridge_sha):
        self.store, self.key, self.identity, self.transport, self.executor, self.bridge_sha = journal, key, identity, transport, executor, bridge_sha

    def _send(self, row):
        payload = json.loads(row["payload"])
        last_error = None
        for attempt in range(3):
            now = int(time.time())
            packet = sign(self.key, "worker_to_controller", row["kind"], row["seq"], payload, now, row["id"])
            try:
                response = self.transport(packet)
                verify(self.key, response, "controller_to_worker", int(time.time()))
                expected = {"request_id": row["id"], "request_digest": sha(semantic(packet))}
                data = response["payload"]
                if response["kind"] != "REPLY" or response["sequence"] != row["seq"] or type(data) is not dict or set(data) != {"request_id", "request_digest", "data"} or any(data.get(k) != v for k, v in expected.items()) or type(data["data"]) is not dict:
                    raise ProtocolError("reply route/request mismatch")
                result = data["data"]
                with self.store.tx():
                    self._apply(row["kind"], payload, result)
                    self.store.db.execute("UPDATE win_outbox SET ack=1 WHERE seq=?", (row["seq"],))
                    self.store.audit("windows-worker", "reply_committed", {"sequence": row["seq"], "request_id": row["id"], "reply_sha256": sha(result)}, int(time.time()))
                return result
            except (PermissionError, ProtocolError, ssl.SSLCertVerificationError):
                raise
            except urllib.error.HTTPError as exc:
                if exc.code not in {408, 429} and exc.code < 500:
                    raise PermissionError("bridge rejected authorization/request; no retry") from exc
                last_error = exc
                if attempt < 2:
                    time.sleep(.1 * (2 ** attempt))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(.1 * (2 ** attempt))
        raise RuntimeError("bounded transport retries exhausted; pending message preserved") from last_error

    def _apply(self, kind, payload, data):
        if kind == "POLL" and "task" in data:
            task = validate_task(data["task"], self.bridge_sha, int(time.time()))
            previous = self.store.db.execute("SELECT body FROM win_local_jobs WHERE task=?", (task["task_id"],)).fetchone()
            if previous and previous[0] != canonical(task):
                raise ProtocolError("task identity rebound")
            self.store.db.execute("INSERT OR IGNORE INTO win_local_jobs VALUES (?,?,'OFFERED',NULL)", (task["task_id"], canonical(task)))
        elif kind == "START":
            if data not in ({"control": "CONTINUE"}, {"control": "CANCEL"}):
                raise ProtocolError("invalid start control")
            row = self.store.db.execute("SELECT body,state FROM win_local_jobs WHERE task=?", (payload["task_id"],)).fetchone()
            if row is None or route(json.loads(row[0])) != payload or row[1] != "OFFERED":
                raise ProtocolError("start checkpoint mismatch")
            self.store.db.execute("UPDATE win_local_jobs SET state=? WHERE task=?", ("START_ACK_CANCEL" if data["control"] == "CANCEL" else "START_ACK", payload["task_id"]))
        elif kind == "RESULT":
            if data != {"acknowledged": True, "task_id": payload["route"]["task_id"], "receipt_sha256": sha(payload)}:
                raise ProtocolError("result receipt mismatch")
            self.store.db.execute("UPDATE win_local_jobs SET state='ACKED' WHERE task=?", (payload["route"]["task_id"],))
        elif kind == "HELLO" and data != {"ready": True}:
            raise ProtocolError("pairing hello rejected")
        elif kind == "HEARTBEAT" and data not in ({"control": "CONTINUE"}, {"control": "CANCEL"}):
            raise ProtocolError("invalid heartbeat control")

    def rpc(self, kind, payload):
        pending = self.store.db.execute("SELECT * FROM win_outbox WHERE ack=0").fetchone()
        if pending:
            if pending["kind"] != kind or pending["payload"] != canonical(payload):
                raise ProtocolError("recover pending request before creating another")
            return self._send(pending)
        with self.store.tx():
            sequence = self.store.db.execute("SELECT coalesce(max(seq),0)+1 FROM win_outbox").fetchone()[0]
            self.store.db.execute("INSERT INTO win_outbox(seq,id,kind,payload) VALUES (?,?,?,?)", (sequence, str(uuid4()), kind, canonical(payload)))
        return self._send(self.store.db.execute("SELECT * FROM win_outbox WHERE seq=?", (sequence,)).fetchone())

    def recover(self):
        pending = self.store.db.execute("SELECT * FROM win_outbox WHERE ack=0").fetchone()
        if pending:
            self._send(pending)
        for row in list(self.store.db.execute("SELECT * FROM win_local_jobs WHERE state='EXECUTING'")):
            # Kill-on-close job handles close if this foreground worker crashes.
            # Absence of a durable completion is still uncertain, never rerun.
            report = {"status": "UNCERTAIN", "artifact": None, "artifact_sha256": None, "identity": self.identity,
                      "pid": None, "thread_id": None, "turn_id": None, "turn_status": None, "job_active_processes": None,
                      "git_after": self.identity["git_head"], "transcript_sha256": None, "interrupt_acknowledged": False}
            with self.store.tx():
                self.store.db.execute("UPDATE win_local_jobs SET state='DONE',report=? WHERE task=?", (canonical(report), row["task"]))
                self.store.audit("windows-worker", "uncertain_restart", {"task_id": row["task"]}, int(time.time()))
        for row in list(self.store.db.execute("SELECT * FROM win_local_jobs WHERE state='DONE'")):
            self.rpc("RESULT", {"route": route(json.loads(row["body"])), "report": json.loads(row["report"])})

    def step(self):
        self.recover()
        self.rpc("HELLO", self.identity)
        self.rpc("POLL", {})
        row = self.store.db.execute("SELECT * FROM win_local_jobs WHERE state IN ('OFFERED','START_ACK','START_ACK_CANCEL') ORDER BY rowid LIMIT 1").fetchone()
        if row is None:
            return {"idle": True}
        task = validate_task(json.loads(row["body"]), self.bridge_sha, int(time.time()))
        if row["state"] == "OFFERED":
            self.rpc("START", route(task))
        with self.store.tx():
            self.store.db.execute("UPDATE win_local_jobs SET state='EXECUTING' WHERE task=?", (task["task_id"],))
            self.store.audit("windows-worker", "execution_intent", {**route(task), "template": task["template"]}, int(time.time()))
        # Only this compiled executor can launch; no prompt/argv/path comes from task text.
        report = self.executor(task, lambda: self.rpc("HEARTBEAT", route(task))["control"] == "CANCEL")
        with self.store.tx():
            self.store.db.execute("UPDATE win_local_jobs SET state='DONE',report=? WHERE task=?", (canonical(report), task["task_id"]))
            self.store.audit("windows-worker", "completion_sealed", {"task_id": task["task_id"], "report_sha256": sha(report)}, int(time.time()))
        self.rpc("RESULT", {"route": route(task), "report": report})
        return {"task_id": task["task_id"], "status": report["status"], "durable": True}


class AppServerMachine:
    """Fixed official stdio lifecycle; reject tools/approval requests and route drift."""
    def __init__(self, cwd):
        self.cwd, self.thread_id, self.turn_id = str(cwd), None, None
        self.artifact, self.status = None, None
        self.cancel_requested, self.interrupt_sent, self.interrupt_acked, self.blocked = False, False, False, False

    def initial(self):
        return {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "dmb-shadow-worker", "version": "1.0.0"}, "capabilities": {}}}

    def interrupt(self):
        self.cancel_requested = True
        if self.thread_id and self.turn_id and not self.interrupt_sent and not self.status:
            self.interrupt_sent = True
            return [{"id": 4, "method": "turn/interrupt", "params": {"threadId": self.thread_id, "turnId": self.turn_id}}]
        return []

    def receive(self, event):
        if type(event) is not dict:
            raise ProtocolError("invalid app-server frame")
        if "error" in event:
            raise ProtocolError("app-server error; do not bypass authentication or policy")
        if "method" in event and "id" in event:
            self.blocked = True
            return [{"id": event["id"], "error": {"code": -32601, "message": "Tools/approvals forbidden by this task template"}}, *self.interrupt()]
        if "id" in event:
            result = event.get("result", {})
            if event["id"] == 1:
                return [{"method": "initialized"}, {"id": 2, "method": "thread/start", "params":
                        {"cwd": self.cwd, "approvalPolicy": "never", "sandbox": "read-only", "ephemeral": True}}]
            if event["id"] == 2:
                if result.get("cwd") != self.cwd or result.get("approvalPolicy") != "never" or result.get("sandbox", {}).get("type") != "readOnly" or result.get("sandbox", {}).get("networkAccess", False) is not False:
                    raise PermissionError("effective cwd/sandbox/approval policy differs")
                self.thread_id = result["thread"]["id"]
                return [{"id": 3, "method": "turn/start", "params": {"threadId": self.thread_id,
                         "input": [{"type": "text", "text": PROMPT}], "cwd": self.cwd, "approvalPolicy": "never",
                         "sandboxPolicy": {"type": "readOnly", "networkAccess": False}, "outputSchema": OUTPUT_SCHEMA}}]
            if event["id"] == 3:
                turn = result["turn"]["id"]
                if self.turn_id and self.turn_id != turn:
                    raise ProtocolError("turn identity changed")
                self.turn_id = turn
                return self.interrupt() if self.cancel_requested else []
            if event["id"] == 4 and self.interrupt_sent and result == {}:
                self.interrupt_acked = True
                return []
            raise ProtocolError("unexpected app-server response identity")
        method, params = event.get("method"), event.get("params", {})
        if isinstance(method, str) and method.startswith("item/") and method not in {"item/started", "item/completed"} and not method.startswith(("item/agentMessage/", "item/reasoning/")):
            self.blocked = True
            return self.interrupt()
        if method in {"item/started", "item/completed", "turn/started", "turn/completed"}:
            if params.get("threadId") != self.thread_id:
                raise ProtocolError("app-server thread route mismatch")
            turn = params.get("turn", {}).get("id") if method.startswith("turn/") else params.get("turnId")
            if not isinstance(turn, str) or (self.turn_id and turn != self.turn_id):
                raise ProtocolError("app-server turn route mismatch")
            self.turn_id = turn
            if method.startswith("item/"):
                item = params["item"]
                if item.get("type") not in {"agentMessage", "userMessage", "reasoning"}:
                    self.blocked = True
                    return self.interrupt()
                if method == "item/completed" and item.get("type") == "agentMessage":
                    self.artifact = json.loads(item["text"])
                    if self.artifact != EXPECTED_ARTIFACT:
                        raise ProtocolError("unexpected artifact; never upload arbitrary model text")
            if method == "turn/completed":
                self.status = params["turn"]["status"]
        return []


class NativeCodexExecutor:
    def __init__(self, scratch, state, executable, identity):
        self.scratch, self.state, self.executable, self.identity = Path(scratch), Path(state), Path(executable), identity

    def __call__(self, task, cancel_check):
        from .windows_native import require_identity, WindowsJobProcess
        token = require_identity()
        if any(self.identity[k] != token[k] for k in token):
            raise PermissionError("execution token changed")
        validate_task(task, bridge_fingerprint(), int(time.time()))
        head = lambda: subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.scratch, text=True, timeout=3).strip()
        clean = lambda: not subprocess.check_output(["git", "status", "--porcelain"], cwd=self.scratch, timeout=3).strip()
        if head() != self.identity["git_head"] or not clean():
            raise PermissionError("scratch Git state changed")
        directory = self.state / "attempts" / str(uuid4()); directory.mkdir(parents=True)
        machine, proc = AppServerMachine(self.scratch), None
        active, pid = None, None
        deadline = time.monotonic() + min(20, task["lease"] - int(time.time()) - 3)
        offset, pending, next_heartbeat = 0, b"", time.monotonic()
        try:
            # Narrow this task's external tool surface using supported config
            # flags. Managed requirements still apply; no ignore/bypass flags.
            proc = WindowsJobProcess(self.executable, ["-c", "mcp_servers={}", "-c", 'web_search="disabled"',
                                                      "app-server", "--listen", "stdio://"], self.scratch, directory)
            pid = proc.pid
            proc.send(machine.initial())
            while not machine.status and time.monotonic() < deadline:
                if sum(p.stat().st_size for p in directory.glob("*.log")) > 1048576:
                    raise ProtocolError("bounded output exceeded")
                if time.monotonic() >= next_heartbeat:
                    if cancel_check():
                        for request in machine.interrupt(): proc.send(request)
                    next_heartbeat = time.monotonic() + 1
                with (directory / "stdout.log").open("rb") as stream:
                    stream.seek(offset); data = stream.read(65536); offset += len(data)
                pending += data
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    if line:
                        for request in machine.receive(json.loads(line)): proc.send(request)
                if not proc.active() and not machine.status:
                    raise ProtocolError("app-server stopped without terminal turn")
                time.sleep(.02)
        except Exception:
            machine.blocked = True
        finally:
            if proc:
                try:
                    active = proc.terminate()
                finally:
                    proc.close()
        status = "UNCERTAIN"
        if not machine.blocked and active == 0 and clean() and head() == self.identity["git_head"]:
            if machine.status == "completed" and machine.artifact == EXPECTED_ARTIFACT:
                status = "SUCCEEDED"
            elif machine.status == "interrupted" and machine.interrupt_acked and machine.cancel_requested:
                status = "CANCELLED"
        artifact = machine.artifact if status == "SUCCEEDED" else None
        transcript = directory / "stdout.log"
        report = {"status": status, "artifact": artifact, "artifact_sha256": sha(artifact) if artifact else None,
                  "identity": self.identity, "pid": pid, "thread_id": machine.thread_id, "turn_id": machine.turn_id,
                  "turn_status": machine.status, "job_active_processes": active, "git_after": head(),
                  "transcript_sha256": hashlib.sha256(transcript.read_bytes()).hexdigest() if transcript.exists() else None,
                  "interrupt_acknowledged": machine.interrupt_acked}
        atomic_json(directory / "receipt.json", report)
        return report
