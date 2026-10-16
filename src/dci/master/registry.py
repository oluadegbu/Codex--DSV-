import json
from pathlib import Path
from dci.bridge.protocol import ProtocolError, identifier

STATES = {'VERIFIED_LOCAL_SHADOW','VERIFIED_LOCAL_SIMULATION','UNVERIFIED','INTERFACE_ONLY','PLANNED_UNVERIFIED','GATED_NOT_AUTHORIZED','IN_DEVELOPMENT_LOCAL_SHADOW'}
FIELDS = {'project_id','name','verified_state','verified_scope','objectives','dependencies','blockers','approval_gates','workspace','git_repository','assigned_worker','next_safe_action','evidence'}


class PortfolioRegistry:
    def __init__(self, path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text())
        if type(self.data.get('schema_version')) is not int or self.data.get('schema_version') != 1 or self.data.get('mode') != 'SHADOW':
            raise ProtocolError('unsupported portfolio registry')
        identifier(self.data['registry_version'])
        self.projects = {}
        for project in self.data['projects']:
            if set(project) != FIELDS or project['project_id'] in self.projects or project['verified_state'] not in STATES:
                raise ProtocolError('malformed/duplicate project record')
            if project['verified_state'].startswith('VERIFIED_') and not project['evidence']:
                raise ProtocolError('verified state needs evidence references')
            identifier(project['project_id'])
            for dep in project['dependencies']:
                if set(dep) != {'project_id','kind','blocks_shadow_lab'} or type(dep['blocks_shadow_lab']) is not bool:
                    raise ProtocolError('invalid dependency semantics')
                identifier(dep['project_id'])
            self.projects[project['project_id']] = project
        self._check_dag()

    def _check_dag(self):
        visiting, done = set(), set()
        def visit(key):
            if key in visiting:
                raise ProtocolError('project dependency cycle')
            if key in done:
                return
            if key not in self.projects:
                raise ProtocolError('unknown project dependency')
            visiting.add(key)
            for dependency in self.projects[key]['dependencies']:
                visit(dependency['project_id'])
            visiting.remove(key)
            done.add(key)
        for key in self.projects:
            visit(key)

    def graph(self):
        return {'registry_version':self.data['registry_version'], 'nodes':list(self.projects),
                'edges':[{'from':p['project_id'],'requires':d['project_id'],'kind':d['kind'],'blocks_shadow_lab':d['blocks_shadow_lab']} for p in self.projects.values() for d in p['dependencies']]}

    def get(self, key):
        if key not in self.projects:
            raise ProtocolError('unregistered project')
        return self.projects[key]
