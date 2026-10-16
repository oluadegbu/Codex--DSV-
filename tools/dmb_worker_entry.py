"""Fixed trusted-code verifier. Invoked with -I; no shell or mailbox prompt."""
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import unittest


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, timeout=3).decode().strip()


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    root = Path(request['workspace']).resolve(strict=True)
    artifact = Path(sys.argv[1]).resolve().parent
    if os.name != 'posix' or os.geteuid() == 0 or 0 in os.getgroups():
        raise PermissionError('certified Linux non-admin resource enforcement required')
    resource.setrlimit(resource.RLIMIT_AS, (request['memory_mb']*1048576,)*2)
    resource.setrlimit(resource.RLIMIT_CPU, (request['cpu_seconds'],)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (request['max_output_bytes'],)*2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (64,64))
    marker = json.loads((root/'WORKER_SCOPE.json').read_text())
    if marker['mode'] != 'SHADOW' or marker['worker_id'] != request['worker_id'] or Path(marker['workspace']).resolve() != root:
        raise PermissionError('wrong workspace marker')
    if request['operation'] != 'verify_lab':
        raise PermissionError('worker supports only fixed trusted tests')
    if any(p.is_symlink() for p in root.rglob('*') if '.git' not in p.parts):
        raise PermissionError('workspace symlinks rejected')
    head = git(root, 'rev-parse','HEAD')
    if head != request['expected_commit'] or git(root,'status','--porcelain'):
        raise PermissionError('unreviewed Git state')
    sources = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src','tests') for p in sorted((root/folder).rglob('*.py'))}
    if sources != request['source_sha256']:
        raise PermissionError('source inventory differs from reviewed pinned manifest')
    started = time.monotonic()
    if request.get('barrier'):
        barrier=Path(request['barrier'])
        (barrier/('ready-'+request['worker_id'])).write_text(str(os.getpid()))
        deadline=time.monotonic()+3
        while not (barrier/'GO').exists():
            if time.monotonic()>=deadline:
                raise TimeoutError('concurrent start barrier missing')
            time.sleep(.005)
    sys.path.insert(0,str(root/'src'))
    os.chdir(root)
    output = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_workstream.py')
    result = unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
    log=output.getvalue().encode()
    if len(log)>request['max_output_bytes']:
        raise RuntimeError('test output resource limit exceeded')
    (artifact/'tests.log').write_bytes(log)
    unchanged=head==git(root,'rev-parse','HEAD') and not git(root,'status','--porcelain')
    report={k:request[k] for k in ('task_id','scope_digest','workspace','worker_id')}
    report.update(outcome='COMPLETE',passed=result.wasSuccessful() and result.testsRun>0 and unchanged,
                  tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                  pid=os.getpid(),uid=os.geteuid(),groups=os.getgroups(),non_admin=True,
                  started_monotonic=started,finished_monotonic=time.monotonic(),git_before=head,git_after=git(root,'rev-parse','HEAD'),
                  git_worktree_unchanged=unchanged,sources_sha256=sources,tests_log_sha256=hashlib.sha256(log).hexdigest(),
                  resource_limits={k:request[k] for k in ('memory_mb','cpu_seconds','max_output_bytes')},
                  sandbox='trusted fixed-code logical workspace isolation; not hostile-code OS confinement')
    (artifact/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
