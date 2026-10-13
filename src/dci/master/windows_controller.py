"""Authenticated outbound-worker endpoint over the existing planner/BHB authority."""
from contextlib import contextmanager
from dataclasses import dataclass, replace
import hashlib
import json

from dci.bridge.store import BridgeStore
from dci.bridge.protocol import ProtocolError, canonical
from dci.bridge.runner import Runner
from .planner import Job
from .brain import MasterBrainTools
from .windows_protocol import WORKSPACE_ID, TEMPLATE, PROMPT, LIMITS, EXPECTED_ARTIFACT, route, sha, sign, verify


class AtomicPeerStore(BridgeStore):
    """Savepoints let existing planner transitions join one authenticated RPC commit."""
    def __init__(self, path):
        self._savepoint = 0
        super().__init__(path)

    @contextmanager
    def tx(self):
        if not self.db.in_transaction:
            with super().tx():
                yield
            return
        self._savepoint += 1
        name = "dmb_peer_" + str(self._savepoint)
        self.db.execute("SAVEPOINT " + name)
        try:
            yield
            self.db.execute("RELEASE SAVEPOINT " + name)
        except BaseException:
            self.db.execute("ROLLBACK TO SAVEPOINT " + name)
            self.db.execute("RELEASE SAVEPOINT " + name)
            raise


@dataclass(frozen=True)
class WindowsCodexJob(Job):
    operation: str = "windows_codex_ping"

    def validate(self):
        if self.operation != "windows_codex_ping" or self.project_id != "DCI":
            raise ProtocolError("only fixed Windows DCI connectivity task is enabled")
        Job.validate(replace(self, operation="codex_review"))


class WindowsController:
    def __init__(self, planner, key, expected_host, bridge_sha, fixture_mode=False):
        self.planner, self.store, self.key = planner, planner.store, key
        self.host, self.bridge_sha, self.fixture_mode = expected_host, bridge_sha, fixture_mode
        if not isinstance(self.store, AtomicPeerStore) or planner.config["max_parallel"] != 1 or len(planner.workers) != 1 or key.worker_id not in planner.workers:
            raise ProtocolError("dedicated atomic single-worker controller required")
        worker = planner.workers[key.worker_id]
        if (worker["max_seconds"], worker["memory_mb"], worker["cpu_seconds"], worker["max_output_bytes"]) != (20, 256, 10, 1048576):
            raise ProtocolError("Windows budget must match fixed signed limits")
        binding = sha({"worker": key.worker_id, "key_id": key.key_id, "key_fingerprint": hashlib.sha256(key.secret).hexdigest(),
                       "key_expires": key.expires, "host": expected_host, "bridge_sha": bridge_sha, "fixture": fixture_mode})
        with self.store.tx():
            row = self.store.db.execute("SELECT value FROM meta WHERE key='win_bridge_v1'").fetchone()
            if row is None:
                self.store.db.execute("CREATE TABLE win_requests(seq INTEGER PRIMARY KEY,id TEXT UNIQUE,digest TEXT,response TEXT)")
                self.store.db.execute("CREATE TABLE win_identity(worker TEXT PRIMARY KEY,body TEXT)")
                self.store.db.execute("CREATE TABLE win_offers(task TEXT PRIMARY KEY,fence INTEGER,body TEXT,state TEXT,cancel INTEGER DEFAULT 0,evidence TEXT)")
                self.store.db.execute("INSERT INTO meta VALUES ('win_bridge_v1',?)", (binding,))
            elif row[0] != binding:
                raise ProtocolError("pairing/context drift; preserve state, never silently re-pair")

    def submit(self, arguments, now):
        allowed = {"task_id", "correlation_id", "project_id", "priority", "dependencies", "ttl_seconds"}
        if type(arguments) is not dict or not {"task_id", "correlation_id", "project_id"} <= set(arguments) <= allowed:
            raise ProtocolError("fixed job intake only")
        if "dependencies" in arguments and type(arguments["dependencies"]) is not list:
            raise ProtocolError("dependency array required")
        return self.planner.submit(WindowsCodexJob(**{**arguments, "dependencies": tuple(arguments.get("dependencies", []))}), now)

    def _job(self, task):
        row = self.store.db.execute("SELECT * FROM master_jobs WHERE task=?", (task,)).fetchone()
        if row is None:
            raise ProtocolError("unknown Windows task")
        return {**dict(row), **self.store.task(task), "scope_digest": row["scope"]}

    def _identity(self, payload):
        fields = {"host", "user", "administrator", "integrity", "workspace_id", "scratch_manifest_sha256", "git_head", "bridge_sha256", "execution_kind", "codex_version"}
        if type(payload) is not dict or set(payload) != fields or payload["host"] != self.host or payload["user"] != self.host + "\\DirectiveCodex" or payload["administrator"] is not False or payload["integrity"] != "Medium":
            raise PermissionError("DirectiveCodex non-admin Medium token required")
        kind = "CONTRACT_FIXTURE" if self.fixture_mode else "WINDOWS_CODEX"
        if payload["execution_kind"] != kind or payload["bridge_sha256"] != self.bridge_sha or payload["workspace_id"] != WORKSPACE_ID or payload["codex_version"] != "0.162.1":
            raise PermissionError("unpaired runtime identity/version")
        from .windows_worker import scratch_manifest_digest
        if payload["scratch_manifest_sha256"] != scratch_manifest_digest() or not isinstance(payload["git_head"], str) or len(payload["git_head"]) != 40 or any(c not in "0123456789abcdef" for c in payload["git_head"]):
            raise PermissionError("unapproved scratch scope")
        return canonical(payload)

    def _offer(self, job):
        return {"task_id": job["id"], "correlation_id": job["correlation"], "scope_digest": job["scope_digest"],
                "fence": job["attempts"], "workspace_id": WORKSPACE_ID, "template": TEMPLATE,
                "template_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(), "bridge_sha256": self.bridge_sha,
                "lease": job["lease"], "task_expires": job["expires"], "limits": LIMITS}

    def _active(self, payload, now):
        if type(payload) is not dict or set(payload) != {"task_id", "correlation_id", "scope_digest", "fence", "workspace_id"}:
            raise ProtocolError("exact dispatch route required")
        row = self.store.db.execute("SELECT * FROM win_offers WHERE task=?", (payload["task_id"],)).fetchone()
        if row is None or route(json.loads(row["body"])) != payload:
            raise ProtocolError("dispatch route/fence mismatch")
        job = self._job(payload["task_id"])
        if job["state"] != "RUNNING" or job["lease"] <= now or job["expires"] <= now:
            raise ProtocolError("expired or terminal dispatch")
        return row, job

    def _handle(self, kind, payload, now):
        if kind == "HELLO":
            body = self._identity(payload)
            old = self.store.db.execute("SELECT body FROM win_identity WHERE worker=?", (self.key.worker_id,)).fetchone()
            if old and old[0] != body:
                raise PermissionError("worker identity/scratch changed; no silent rebinding")
            self.store.db.execute("INSERT OR IGNORE INTO win_identity VALUES (?,?)", (self.key.worker_id, body))
            return {"ready": True}
        identity = self.store.db.execute("SELECT body FROM win_identity WHERE worker=?", (self.key.worker_id,)).fetchone()
        if identity is None:
            raise PermissionError("authenticated HELLO required before dispatch")
        self.planner.recover(now)
        if kind == "POLL":
            if payload:
                raise ProtocolError("poll parameters forbidden")
            old = self.store.db.execute("SELECT * FROM win_offers WHERE state IN ('OFFERED','STARTED') ORDER BY rowid LIMIT 1").fetchone()
            if old:
                job = self._job(old["task"])
                return {"task": json.loads(old["body"])} if job["state"] == "RUNNING" else {"wait": True, "quarantined": True}
            jobs = self.planner.claim(now)
            if not jobs:
                return {"wait": True}
            job = jobs[0]
            if job["operation"] != "windows_codex_ping" or job["worker"] != self.key.worker_id:
                raise PermissionError("unsupported Windows route")
            offer = self._offer(job)
            self.store.db.execute("INSERT INTO win_offers(task,fence,body,state) VALUES (?,?,?,'OFFERED')", (job["id"], job["attempts"], canonical(offer)))
            return {"task": offer}
        if kind in {"START", "HEARTBEAT"}:
            row, job = self._active(payload, now)
            if kind == "START":
                self.store.db.execute("UPDATE win_offers SET state='STARTED' WHERE task=?", (job["id"],))
            self.store.db.execute("UPDATE master_heartbeats SET at=?,task=? WHERE worker=?", (now, job["id"], self.key.worker_id))
            return {"control": "CANCEL" if row["cancel"] else "CONTINUE"}
        if kind == "RESULT":
            if type(payload) is not dict or set(payload) != {"route", "report"} or type(payload["route"]) is not dict:
                raise ProtocolError("fixed result payload required")
            receipt = self.store.db.execute("SELECT * FROM win_offers WHERE task=?", (payload["route"].get("task_id"),)).fetchone()
            if receipt and receipt["state"] == "COMMITTED":
                if receipt["evidence"] != canonical(payload):
                    raise ProtocolError("conflicting result replay")
                return {"acknowledged": True, "task_id": receipt["task"], "receipt_sha256": sha(payload)}
            row, job = self._active(payload["route"], now)
            report = payload["report"]
            fields = {"status", "artifact", "artifact_sha256", "identity", "pid", "thread_id", "turn_id", "turn_status", "job_active_processes", "git_after", "transcript_sha256", "interrupt_acknowledged"}
            if type(report) is not dict or set(report) != fields or self._identity(report["identity"]) != identity[0]:
                raise PermissionError("worker receipt identity/Git scope mismatch")
            if report["status"] not in {"SUCCEEDED", "CANCELLED", "UNCERTAIN"}:
                raise ProtocolError("unknown worker result")
            if type(report["interrupt_acknowledged"]) is not bool:
                raise ProtocolError("typed interrupt acknowledgement required")
            if report["status"] != "UNCERTAIN" and report["git_after"] != report["identity"]["git_head"]:
                raise PermissionError("worker Git state changed")
            if report["status"] != "SUCCEEDED" and (report["artifact"] is not None or report["artifact_sha256"] is not None):
                raise ProtocolError("non-success cannot upload model text/artifacts")
            for name in ("thread_id", "turn_id"):
                if report[name] is not None and (not isinstance(report[name], str) or not 1 <= len(report[name]) <= 128):
                    raise ProtocolError("invalid app-server identity")
            if report["transcript_sha256"] is not None and (not isinstance(report["transcript_sha256"], str) or len(report["transcript_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in report["transcript_sha256"])):
                raise ProtocolError("invalid transcript digest")
            if report["status"] != "UNCERTAIN" and (type(report["pid"]) is not int or report["pid"] <= 0 or report["job_active_processes"] != 0 or type(report["job_active_processes"]) is not int):
                raise ProtocolError("owned process termination not verified")
            passed = report["status"] == "SUCCEEDED"
            if passed and (report["artifact"] != EXPECTED_ARTIFACT or report["artifact_sha256"] != sha(EXPECTED_ARTIFACT) or report["turn_status"] != "completed" or not report["thread_id"] or not report["turn_id"]):
                raise ProtocolError("no verified genuine turn/artifact")
            if report["status"] == "CANCELLED" and (not row["cancel"] or report["interrupt_acknowledged"] is not True or report["turn_status"] != "interrupted" or not report["thread_id"] or not report["turn_id"]):
                raise ProtocolError("cancellation needs actual Codex interrupt evidence")
            evidence = {"task_id": job["id"], "scope_digest": job["scope_digest"], "worker_id": job["worker"], "workspace": job["workspace"],
                        "outcome": "AMBIGUOUS" if report["status"] == "UNCERTAIN" else "COMPLETE", "passed": passed,
                        "remote_report": report, "receipt_sha256": sha(payload), "authentication": "scoped HMAC + verified HTTPS", "fixture": self.fixture_mode}
            self.planner.finish(job, evidence, now)
            self.store.db.execute("UPDATE win_offers SET state='COMMITTED',evidence=? WHERE task=?", (canonical(payload), job["id"]))
            return {"acknowledged": True, "task_id": job["id"], "receipt_sha256": sha(payload)}
        raise ProtocolError("unsupported bridge request")

    def receive(self, packet, now):
        body = verify(self.key, packet, "worker_to_controller", now)
        if packet["kind"] == "REPLY":
            raise ProtocolError("reflection rejected")
        digest = sha(body)
        with self.store.tx():
            previous = self.store.db.execute("SELECT * FROM win_requests WHERE seq=?", (packet["sequence"],)).fetchone()
            if previous:
                if previous["id"] != packet["message_id"] or previous["digest"] != digest:
                    raise ProtocolError("replay sequence/identity/payload conflict")
                response = json.loads(previous["response"])
            else:
                maximum = self.store.db.execute("SELECT coalesce(max(seq),0) FROM win_requests").fetchone()[0]
                if packet["sequence"] != maximum + 1:
                    raise ProtocolError("out-of-order peer sequence")
                response = self._handle(packet["kind"], packet["payload"], now)
                self.store.db.execute("INSERT INTO win_requests VALUES (?,?,?,?)", (packet["sequence"], packet["message_id"], digest, canonical(response)))
                self.store.audit("windows-peer", packet["kind"], {"sequence": packet["sequence"], "message_id": packet["message_id"], "body_sha256": digest, "reply_sha256": sha(response)}, now)
        # Reply creation follows the durable commit; duplicate response is freshly signed.
        return sign(self.key, "controller_to_worker", "REPLY", packet["sequence"],
                    {"request_id": packet["message_id"], "request_digest": digest, "data": response}, now, packet["message_id"])

    def cancel(self, task, now):
        with self.store.tx():
            row = self.store.db.execute("SELECT body FROM win_offers WHERE task=? AND state IN ('OFFERED','STARTED')", (task,)).fetchone()
            if row is None:
                raise ProtocolError("no active owned Windows offer")
            self._active(route(json.loads(row[0])), now)
            self.store.db.execute("UPDATE win_offers SET cancel=1 WHERE task=?", (task,))
            self.store.audit("brain", "windows_cancel_requested", {"task_id": task}, now)
        return {"task_id": task, "requested": True, "termination_certified": False}

    def report(self):
        return {**MasterBrainTools(self.planner).report(), "windows_bridge": {
            "transport": "authenticated HTTPS outbound poll", "fixture_mode": self.fixture_mode,
            "offers": [dict(row) for row in self.store.db.execute("SELECT task,fence,state,cancel FROM win_offers ORDER BY rowid DESC LIMIT 100")],
            "peer_bound": self.store.db.execute("SELECT count(*) FROM win_identity").fetchone()[0] == 1,
            "remote_OS_isolation_certified": False, "services_installed": False,
            "trust": "paired worker key and pinned bridge code; signed claims are not hardware attestation or human approval"}}
