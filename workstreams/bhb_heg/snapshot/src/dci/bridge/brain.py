"""Local authenticated-process Brain tool facade and MCP stdio prototype.

No ordinary ChatGPT conversation polling or self-waking is assumed. No network
server is exposed; remote OAuth/mTLS and ChatGPT connection remain gated.
"""
import argparse
import json
import sys
import time
from uuid import uuid4
from .identity import require_non_admin
from .protocol import ProtocolError, envelope
from .store import BridgeStore


class BrainTools:
    def __init__(self, store):
        self.store = store

    def submit_task(self, action, task_id, correlation_id, now, ttl=3600):
        m = self.store.create_task(action, now, ttl, task_id, correlation_id)
        return {'task_id': m['task_id'], 'correlation_id': m['correlation_id'], 'message_id': m['message_id']}

    def get_status(self, task_id):
        t = self.store.task(task_id)
        return {'task_id': t['id'], 'correlation_id': t['correlation'], 'state': t['state'], 'result': json.loads(t['result']) if t['result'] else None,
                'messages': [m for m in self.store.status_messages('brain') if m['task_id'] == task_id]}

    def control(self, event, now):
        with self.store.tx():
            m = envelope('EVENT', 'brain', 'runner', str(uuid4()), str(uuid4()), {'event': event}, self.store._next('brain', 'runner'), now)
        self.store.submit('brain', m, now)
        return {'accepted': True, 'event': event}


TOOLS = [
    {'name': 'dci_submit_task', 'description': 'Submit one fixed shadow operation; no free-form execution',
     'inputSchema': {'type': 'object', 'properties': {'action': {'enum': ['synthetic_check', 'core_tests', 'fixture_replay', 'codex_review', 'gated_shadow_note']}, 'task_id': {'type': 'string'}, 'correlation_id': {'type': 'string'}}, 'required': ['action', 'task_id', 'correlation_id'], 'additionalProperties': False}},
    {'name': 'dci_get_status', 'description': 'Return durable task state and result to Brain',
     'inputSchema': {'type': 'object', 'properties': {'task_id': {'type': 'string'}}, 'required': ['task_id'], 'additionalProperties': False}},
    {'name': 'dci_control', 'description': 'Pause/resume future task dispatch',
     'inputSchema': {'type': 'object', 'properties': {'event': {'enum': ['PAUSE', 'RESUME']}}, 'required': ['event'], 'additionalProperties': False}}
]


class LocalMcpPrototype:
    def __init__(self, tools):
        self.tools = tools
        self.initialized = False
        self.ready = False

    def request(self, request, now):
        method = request.get('method')
        params = request.get('params', {})
        if method == 'initialize':
            self.initialized = True
            return {'protocolVersion': '2025-03-26', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'dci-bhb-shadow', 'version': '1.0.0'}}
        if method == 'notifications/initialized' and self.initialized:
            self.ready = True
            return None
        if not self.ready:
            raise ProtocolError('MCP initialization required')
        if method == 'tools/list':
            return {'tools': TOOLS}
        if method != 'tools/call' or set(params) != {'name', 'arguments'}:
            raise ProtocolError('unsupported MCP request')
        args = params['arguments']
        name = params['name']
        if not isinstance(args, dict):
            raise ProtocolError('arguments must be an object')
        if name == 'dci_submit_task' and set(args) == {'action', 'task_id', 'correlation_id'}:
            result = self.tools.submit_task(args['action'], args['task_id'], args['correlation_id'], now)
        elif name == 'dci_get_status' and set(args) == {'task_id'}:
            result = self.tools.get_status(args['task_id'])
        elif name == 'dci_control' and set(args) == {'event'}:
            result = self.tools.control(args['event'], now)
        else:
            raise ProtocolError('unsupported tool or arguments')
        return {'content': [{'type': 'text', 'text': json.dumps(result)}], 'structuredContent': result, 'isError': False}


def main():
    parser = argparse.ArgumentParser(description='Local stdio Brain MCP shadow prototype; no external auth/provider')
    parser.add_argument('--database', required=True)
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    require_non_admin(args.workspace)
    store = BridgeStore(args.database)
    server = LocalMcpPrototype(BrainTools(store))
    try:
        for line in sys.stdin:
            request = {}
            try:
                if len(line) > 65536:
                    raise ProtocolError('oversized MCP request')
                request = json.loads(line)
                if request.get('jsonrpc') != '2.0':
                    raise ProtocolError('JSON-RPC 2.0 required')
                result = server.request(request, int(time.time()))
                response = {'jsonrpc': '2.0', 'id': request.get('id'), 'result': result}
            except (ValueError, KeyError, TypeError, PermissionError) as exc:
                response = {'jsonrpc': '2.0', 'id': request.get('id'), 'error': {'code': -32602, 'message': str(exc)}}
            if 'id' in request:
                print(json.dumps(response), flush=True)
    finally:
        store.close()


if __name__ == '__main__':
    main()
