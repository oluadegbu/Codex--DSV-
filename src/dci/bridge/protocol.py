"""Version 1 contracts. Mailbox text never becomes a shell command."""
import json
import re
from uuid import uuid4

KINDS = ("TASK", "STATUS", "ACK", "RESULT", "EVENT", "APPROVAL_REQUEST")
ROUTES = {"TASK": {("brain", "runner")}, "STATUS": {("runner", "brain")},
          "ACK": {("runner", "brain")}, "RESULT": {("runner", "brain"), ("hands", "runner")},
          "EVENT": {("brain", "runner"), ("runner", "brain"), ("heg", "brain")},
          "APPROVAL_REQUEST": {("runner", "heg")}}
ACTIONS = {"synthetic_check", "core_tests", "fixture_replay", "codex_review", "gated_shadow_note"}
STATES = ("QUEUED", "RUNNING", "RETRY_WAIT", "SUCCEEDED", "FAILED", "EXPIRED", "NEEDS_HUMAN", "REJECTED", "HUMAN_TIMEOUT")
FIELDS = {"version", "kind", "message_id", "task_id", "correlation_id", "sender", "recipient", "sequence", "issued_at", "expires_at", "payload"}
IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class ProtocolError(ValueError):
    pass


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identifier(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ProtocolError("invalid identity")


def validate(message: dict, actor: str, now: int):
    if not isinstance(message, dict) or set(message) != FIELDS:
        raise ProtocolError("unknown/missing envelope fields")
    if type(message["version"]) is not int or message["version"] != 1 or message["kind"] not in KINDS:
        raise ProtocolError("unsupported version or kind")
    if message["sender"] != actor or (actor, message["recipient"]) not in ROUTES[message["kind"]]:
        raise ProtocolError("wrong route or writer")
    for key in ("message_id", "task_id", "correlation_id"):
        identifier(message[key])
    for key in ("sequence", "issued_at", "expires_at"):
        if type(message[key]) is not int:
            raise ProtocolError("integer times/sequence required")
    if message["sequence"] < 1 or message["issued_at"] < 0 or not message["issued_at"] <= now < message["expires_at"] or not 0 < message["expires_at"] - message["issued_at"] <= 86400:
        raise ProtocolError("expired/future envelope or invalid sequence")
    p = message["payload"]
    if not isinstance(p, dict) or len(canonical(message)) > 65536:
        raise ProtocolError("invalid or oversized payload")
    kind = message["kind"]
    if kind == "TASK":
        if set(p) != {"action", "parameters"} or p["action"] not in ACTIONS or p["parameters"] != {}:
            raise ProtocolError("operation not allowlisted; arbitrary parameters forbidden")
    elif kind == "EVENT":
        if actor == "brain":
            if set(p) != {"event"} or p["event"] not in ("PAUSE", "RESUME"):
                raise ProtocolError("unsupported control event")
        elif set(p) != {"event", "detail"} or not all(isinstance(v, str) for v in p.values()):
            raise ProtocolError("invalid event")
    elif kind == "STATUS":
        if set(p) != {"state", "detail"} or p["state"] not in STATES or not isinstance(p["detail"], str):
            raise ProtocolError("invalid status")
    elif kind == "ACK":
        if set(p) != {"accepted_message_id"}:
            raise ProtocolError("invalid ACK")
        identifier(p["accepted_message_id"])
    elif kind == "RESULT":
        if set(p) != {"state", "evidence"} or p["state"] not in ("SUCCEEDED", "FAILED") or not isinstance(p["evidence"], dict):
            raise ProtocolError("invalid result")
    elif kind == "APPROVAL_REQUEST":
        if set(p) != {"request_id", "scope_digest", "category", "summary"} or p["category"] not in ("APPROVAL", "CONTROL_PLANE_DEGRADED"):
            raise ProtocolError("invalid approval request")
        identifier(p["request_id"])
        if not isinstance(p["scope_digest"], str) or not re.fullmatch(r"[0-9a-f]{64}", p["scope_digest"]) or not isinstance(p["summary"], str):
            raise ProtocolError("invalid request scope")


def envelope(kind, sender, recipient, task_id, correlation_id, payload, sequence, now, ttl=3600):
    return {"version": 1, "kind": kind, "message_id": str(uuid4()), "task_id": task_id,
            "correlation_id": correlation_id, "sender": sender, "recipient": recipient,
            "sequence": sequence, "issued_at": now, "expires_at": now + ttl, "payload": payload}
