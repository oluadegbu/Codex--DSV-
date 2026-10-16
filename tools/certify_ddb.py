"""Offline DDB certification with retained paper-process evidence; activates nothing."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args(); out=Path(args.output).resolve()
    if out.exists() or ROOT in out.parents:raise PermissionError('Fresh external evidence directory required')
    out.mkdir(parents=True)
    env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'src');env['DDB_EVIDENCE_DIR']=str(out)
    proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','ddb_tests','-v'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
    (out/'TESTS.log').write_text(proc.stdout+proc.stderr)
    files=[*sorted((ROOT/'src/dci/master').glob('document_*.py')),ROOT/'ddb_tests/test_document_bridge.py']
    tests=__import__('re').search(r'Ran (\d+) tests',proc.stderr)
    evidence={'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'mode':'SHADOW',
              'status':'OFFLINE_PASS_ACTIVATION_BLOCKED' if proc.returncode==0 else 'FAIL',
              'tests_run':int(tests.group(1)) if tests else 0,'exit_code':proc.returncode,
              'source_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)),
              'observed_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              'gates':{'offline_document_handoff':'PASS' if proc.returncode==0 else 'FAIL','real_local_paper_recovery':'PASS' if (out/'REAL_PAPER_RECOVERY.json').exists() and proc.returncode==0 else 'FAIL',
                       'real_github_document_exchange':'NOT_TESTED','native_codex_ddb_backend':'BLOCKED_DISABLED','signer_and_github_credential_enrollment':'BLOCKED_APPROVAL_REQUIRED','human_policy_pin':'BLOCKED_NOT_APPROVED','scheduler_activation':'WITHHELD'},
              'persistent_processes_installed':False,'external_notifications':False,'trading_authority':False}
    (out/'CERTIFICATION.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:evidence[k] for k in ('status','tests_run','exit_code')}))
    raise SystemExit(proc.returncode)


if __name__=='__main__':main()
