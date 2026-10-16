"""Mount existing DMB handlers in an approved HTTPS host. Opens no listener.

The controller's existing atomic database IS the durable inbox/outbox; this
adapter adds no intermediary queue or new authentication protocol. Activation,
TLS termination, host ownership and persistence require separate approval.
"""
from contextlib import contextmanager
import json
import time
from urllib.parse import urlsplit

from dci.bridge.protocol import ProtocolError, canonical
from .operations import Operations
from .windows_controller import WindowsController
from .windows_protocol import MAX_BYTES


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError('Duplicate JSON member')
        result[key] = value
    return result


class DMBHTTPSApplication:
    """WSGI callable only. Factory creates a dedicated connection per request.

    The serving host must supply trustworthy wsgi.url_scheme after its approved
    TLS termination. Forwarded headers from requests are never trusted here.
    A configuration hostname is NOT ownership or deployment certification.
    """
    def __init__(self, controller_factory, approved_origin):
        if not callable(controller_factory) or type(approved_origin) is not str:
            raise PermissionError('Operator-configured factory and HTTPS origin required')
        p = urlsplit(approved_origin)
        if (p.scheme != 'https' or not p.hostname or p.username or p.password
                or p.query or p.fragment or p.path or p.port not in (None, 443)):
            raise PermissionError('Exact HTTPS origin, no credentials, port override or path')
        self.authorities = {p.hostname.casefold(), p.hostname.casefold()+':443'}
        self.factory = controller_factory

    def __call__(self, environ, start_response):
        status = '403 Forbidden'
        result = {'mode': 'SHADOW', 'error': 'request_rejected'}
        try:
            # A caller header cannot assert TLS or choose another tenant/host.
            if (environ.get('wsgi.url_scheme') != 'https'
                    or environ.get('HTTP_HOST', '').casefold() not in self.authorities
                    or environ.get('QUERY_STRING', '') or environ.get('SCRIPT_NAME', '')):
                raise PermissionError('Wrong transport/origin')
            path = environ.get('PATH_INFO')
            if path not in ('/v1/dmb/operations', '/v1/dmb/windows'):
                status = '404 Not Found'
            elif environ.get('REQUEST_METHOD') != 'POST':
                status = '405 Method Not Allowed'
            elif environ.get('CONTENT_TYPE') != 'application/json':
                status = '415 Unsupported Media Type'
            else:
                length = environ.get('CONTENT_LENGTH', '')
                if (type(length) is not str or not length.isascii() or not length.isdigit()
                        or not 1 <= len(length) <= 6 or not 1 <= int(length) <= MAX_BYTES):
                    status = '413 Payload Too Large'
                else:
                    # The approved serving host must bound body-read time; this
                    # adapter never reads beyond the declared bounded body.
                    raw = environ['wsgi.input'].read(int(length))
                    if type(raw) is not bytes or len(raw) != int(length):
                        raise ProtocolError('Truncated body')
                    packet = json.loads(raw, object_pairs_hook=_unique_object)
                    with self.factory() as (controller, operations):
                        if (not isinstance(controller, WindowsController) or controller.fixture_mode
                                or not isinstance(operations, Operations)
                                or operations.controller is not controller
                                or operations.store is not controller.store):
                            raise PermissionError('Dedicated production-mode atomic controller required')
                        now = int(time.time())
                        result = (operations.handle(packet, now) if path == '/v1/dmb/operations'
                                  else controller.receive(packet, now))
                        controller.store.verify_audit()
                    # Existing handlers durably commit BEFORE signed ACK creation.
                    status = '200 OK'
        except (PermissionError, ProtocolError, ValueError, TypeError, KeyError, RecursionError):
            status = '403 Forbidden'
            result = {'mode': 'SHADOW', 'error': 'request_rejected'}
        except Exception:
            # No raw exceptions, credentials, payload logging or false ACK on
            # storage/backend failure. Clients keep the same durable message ID.
            status = '503 Service Unavailable'
            result = {'mode': 'SHADOW', 'error': 'controller_unavailable'}
        body = canonical(result).encode()
        if len(body) > MAX_BYTES:
            status = '503 Service Unavailable'
            body = b'{"error":"response_limit","mode":"SHADOW"}'
        start_response(status, [('Content-Type', 'application/json'),
                                ('Content-Length', str(len(body))), ('Cache-Control', 'no-store')])
        return [body]


def configured_factory(workspace, database, workers, brain_identity_file, worker_pairing_file):
    """Private operator configuration only; never populated from HTTP/mailbox text.

    Caller approves existing hosting first. This function installs nothing and
    reads no unrelated project credentials. Connections close on every outcome.
    """
    @contextmanager
    def factory():
        from dci.bridge.identity import require_non_admin
        from .operations_cli import load_identity, load_private_json
        from .windows_bridge_cli import key_from_config
        from .windows_controller import AtomicPeerStore
        from .planner import PortfolioPlanner
        from .registry import PortfolioRegistry
        root = require_non_admin(workspace)
        identity = load_identity(brain_identity_file)
        pairing = load_private_json(worker_pairing_file)
        store = AtomicPeerStore(database)
        try:
            planner = PortfolioPlanner(store, PortfolioRegistry(root/'portfolio/REGISTRY.v1.json'), workers, root)
            controller = WindowsController(planner, key_from_config(pairing),
                                           pairing['expected_host'], pairing['bridge_sha256'])
            yield controller, Operations(controller, identity)
        finally:
            store.close()
    return factory
