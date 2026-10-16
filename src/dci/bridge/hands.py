"""Bounded fixed task templates using supported Codex exec; never mailbox prompts."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from .identity import require_non_admin
from .runner import BeforeStartUnavailable

REVIEW_PROMPT = ('Review only src/dci/models.py and src/dci/scoring.py in this DCI repository. '
                 'Do not modify files, access credentials, access the network, submit transactions, '
                 'or execute trading operations. Give a short safety review. This is a bounded read-only certification task.')


class HandsAdapter:
    def __init__(self, codex=None):
        self.codex = codex or shutil.which('codex')

    def execute(self, action, workspace):
        root = require_non_admin(workspace)
        templates = {
            'core_tests': [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
            'fixture_replay': [sys.executable, '-m', 'dci', 'tests/fixtures/synthetic.json']
        }
        if action == 'codex_review':
            if not self.codex:
                raise BeforeStartUnavailable('Codex CLI absent; no process started')
            argv = [self.codex, 'exec', '--sandbox', 'read-only', '--json', '--ephemeral', '-C', str(root), '-']
            prompt = REVIEW_PROMPT
            timeout = 20
        elif action in templates:
            argv, prompt, timeout = templates[action], None, 20
        else:
            raise PermissionError('Hands operation outside fixed allowlist')
        # Fixed actions run only trusted reviewed code. No shell interpolation and
        # no caller arguments/environment overrides. Preserve inherited platform
        # proxy/auth protections for Codex; never inspect credential files.
        env = os.environ.copy()
        env['PYTHONPATH'] = str(root / 'src')
        evidence_dir = root / 'artifacts' / 'hands' / str(uuid4())
        evidence_dir.mkdir(parents=True, exist_ok=False)
        before = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        diff_before = subprocess.run(['git', 'diff', '--binary', 'HEAD'], cwd=root, capture_output=True, timeout=5, check=True).stdout
        status_before = subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, timeout=5, check=True).stdout
        started = time.monotonic()
        try:
            # Output is captured to files to bound parent memory. Raw logs are
            # local-only and excluded from Git; do not publish unreviewed logs.
            with (evidence_dir / 'stdout.log').open('w') as out, (evidence_dir / 'stderr.log').open('w') as err:
                proc = subprocess.run(argv, input=prompt, text=True, cwd=root, env=env, stdout=out, stderr=err, timeout=timeout, shell=False)
        except FileNotFoundError as exc:
            raise BeforeStartUnavailable('Executable unavailable; no process started') from exc
        # Timeout/partial external outcome raises; Runner moves to NEEDS_HUMAN.
        # No automatic retry of a process that may already have run.
        completed = True
        if action == 'codex_review':
            completed = False
            with (evidence_dir / 'stdout.log').open() as stream:
                for line in stream:
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get('type') == 'turn.completed':
                        completed = True
                    if event.get('type') in ('turn.failed', 'error'):
                        completed = False
        after = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        diff_after = subprocess.run(['git', 'diff', '--binary', 'HEAD'], cwd=root, capture_output=True, timeout=5, check=True).stdout
        status_after = subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, timeout=5, check=True).stdout
        unchanged = before == after and diff_before == diff_after and status_before == status_after
        evidence = {'passed': proc.returncode == 0 and completed and unchanged,
                    'operation': action, 'exit_code': proc.returncode, 'interface': 'codex exec' if action == 'codex_review' else 'fixed subprocess argv',
                    'sandbox': 'read-only' if action == 'codex_review' else 'non-admin fixed local verification',
                    'git_before': before, 'git_after': after, 'git_worktree_unchanged': unchanged,
                    'diff_before_sha256': hashlib.sha256(diff_before).hexdigest(), 'diff_after_sha256': hashlib.sha256(diff_after).hexdigest(), 'duration_seconds': round(time.monotonic()-started, 3),
                    'artifacts': str(evidence_dir.relative_to(root)), 'stdout_sha256': hashlib.sha256((evidence_dir / 'stdout.log').read_bytes()).hexdigest(),
                    'stderr_sha256': hashlib.sha256((evidence_dir / 'stderr.log').read_bytes()).hexdigest(),
                    'turn_completed': completed, 'synthetic': False}
        (evidence_dir / 'report.json').write_text(json.dumps(evidence, indent=2)+'\n')
        return evidence
