"""Scoped HMAC/TLS bridge protocol. No commands, prompts or paths in task messages."""
from dataclasses import dataclass, field
import hashlib
import hmac
import json
from urllib.parse import urlsplit
from uuid import uuid4

from dci.bridge.protocol import ProtocolError, canonical, identifier

MAX_BYTES = 131072
WORKSPACE_ID = "DCI_WINDOWS_SCRATCH_V1"
TEMPLATE = "codex_shadow_ping_v1"
PROMPT = 'Return only this JSON object: {"mode":"SHADOW","answer":"DCI_SHADOW_OK"}. Do not use any tools, inspect files, execute commands, access credentials or external data, or perform trading. This is a bounded non-trading connectivity task.'
EXPECTED_ARTIFACT = {"mode": "SHADOW", "answer": "DCI_SHADOW_OK"}
OUTPUT_SCHEMA = {"type": "object", "properties": {"mode": {"type": "string", "const": "SHADOW"},
                 "answer": {"type": "string", "const": "DCI_SHADOW_OK"}}, "required": ["mode", "answer"], "additionalProperties": False}
LIMITS = {"wall_seconds": 20, "memory_mb": 256, "cpu_seconds": 10, "max_output_bytes": 1048576}
KINDS = {"HELLO", "POLL", "START", "HEARTBEAT", "RESULT", "REPLY"}


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def endpoint(value):
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path != "/v1/dmb/windows":
        raise PermissionError("exact HTTPS bridge endpoint required")
    return value


@dataclass(frozen=True)
class PeerKey:
    worker_id: str
    key_id: str
    expires: int
    secret: bytes = field(repr=False)

    def check(self, now):
        identifier(self.worker_id); identifier(self.key_id)
        if type(self.secret) is not bytes or len(self.secret) != 32 or type(self.expires) is not int or type(now) is not int or now >= self.expires:
            raise PermissionError("expired or invalid scoped pairing")


def semantic(packet):
    return {k: v for k, v in packet.items() if k not in {"sent_at", "expires_at", "mac"}}


def sign(key, direction, kind, sequence, payload, now, message_id=None):
    key.check(now)
    packet = {"version": 1, "worker_id": key.worker_id, "key_id": key.key_id, "direction": direction,
              "kind": kind, "sequence": sequence, "message_id": message_id or str(uuid4()),
              "sent_at": now, "expires_at": min(now + 60, key.expires), "payload": payload}
    packet["mac"] = hmac.digest(key.secret, b"DMB-WINDOWS-BRIDGE-v1\n" + canonical(packet).encode(), "sha256").hex()
    verify(key, packet, direction, now)
    return packet


def verify(key, packet, direction, now):
    key.check(now)
    required = {"version", "worker_id", "key_id", "direction", "kind", "sequence", "message_id", "sent_at", "expires_at", "payload", "mac"}
    if type(packet) is not dict or set(packet) != required or len(canonical(packet).encode()) > MAX_BYTES:
        raise ProtocolError("invalid bounded bridge packet")
    if packet["version"] != 1 or type(packet["version"]) is not int or packet["worker_id"] != key.worker_id or packet["key_id"] != key.key_id or packet["direction"] != direction or direction not in {"worker_to_controller", "controller_to_worker"}:
        raise PermissionError("wrong bridge version, identity or direction")
    identifier(packet["message_id"])
    if packet["kind"] not in KINDS or type(packet["payload"]) is not dict or type(packet["sequence"]) is not int or not 1 <= packet["sequence"] <= 2147483647:
        raise ProtocolError("invalid bridge kind, payload or sequence")
    sent, expires = packet["sent_at"], packet["expires_at"]
    if type(sent) is not int or type(expires) is not int or abs(now - sent) > 30 or not sent < expires <= min(sent + 60, key.expires) or expires <= now:
        raise PermissionError("expired/future packet or unsynchronized clock")
    mac = packet["mac"]
    unsigned = {k: v for k, v in packet.items() if k != "mac"}
    expected = hmac.digest(key.secret, b"DMB-WINDOWS-BRIDGE-v1\n" + canonical(unsigned).encode(), "sha256").hex()
    if not isinstance(mac, str) or len(mac) != 64 or any(c not in "0123456789abcdef" for c in mac) or not hmac.compare_digest(mac, expected):
        raise PermissionError("bridge signature mismatch")
    return semantic(packet)


def route(task):
    return {k: task[k] for k in ("task_id", "correlation_id", "scope_digest", "fence", "workspace_id")}


def validate_task(task, bridge_sha, now):
    fields = {"task_id", "correlation_id", "scope_digest", "fence", "workspace_id", "template", "template_sha256",
              "bridge_sha256", "lease", "task_expires", "limits"}
    if type(task) is not dict or set(task) != fields:
        raise ProtocolError("fixed task fields required; no remote command/prompt/path")
    identifier(task["task_id"]); identifier(task["correlation_id"])
    if task["workspace_id"] != WORKSPACE_ID or task["template"] != TEMPLATE or task["template_sha256"] != hashlib.sha256(PROMPT.encode()).hexdigest() or task["bridge_sha256"] != bridge_sha or task["limits"] != LIMITS:
        raise PermissionError("unapproved task template/workspace/runtime/budget")
    if type(task["fence"]) is not int or task["fence"] < 1 or not isinstance(task["scope_digest"], str) or len(task["scope_digest"]) != 64 or any(c not in "0123456789abcdef" for c in task["scope_digest"]):
        raise ProtocolError("invalid task fence or scope")
    if type(task["lease"]) is not int or type(task["task_expires"]) is not int or not now < task["lease"] <= now + 30 or task["task_expires"] <= now:
        raise PermissionError("expired or unbounded dispatch lease")
    return task
