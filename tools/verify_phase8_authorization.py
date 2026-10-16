"""Verify preserved Phase8 plus additive offline policy fixtures; no external calls."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output).resolve();old=ROOT/'docs/evidence/phase8'
    if out==old or old in out.parents:raise PermissionError('prior certificate directory is immutable')
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((old/'ARTIFACT_MANIFEST.json').read_text())
    for rel,item in manifest['artifacts'].items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('prior artifact changed: '+rel)
    original=json.loads((ROOT/'docs/evidence/DMB_CERTIFICATION.json').read_text())
    for rel,expected in original['source_sha256'].items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:raise RuntimeError('original certified source changed: '+rel)
    prior=json.loads((old/'SOURCE_CERTIFICATION.json').read_text())
    for rel,expected in prior['new_sources_sha256'].items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:raise RuntimeError('prior Phase8 code changed: '+rel)
    # Verify prior bundle integrity where the preserved workspace bundles exist.
    bundles=[]
    for name in ('/workspace/dci-dmb-shadow.bundle','/workspace/dci-dmb-phase8.bundle'):
        bundle=Path(name)
        subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,capture_output=True,check=True,timeout=5)
        bundles.append({'path':name,'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'git_verify':'PASS'})
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(ROOT/'src')}
    suites={}
    for folder,count,label in [('tests',100,'PRESERVED_TESTS'),('certification_tests',17,'AUTHORIZATION_TESTS')]:
        argv=[sys.executable,'-m','unittest','discover','-s',folder,'-v']
        checked=subprocess.run(argv,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20,check=True)
        observed=int(re.search(rb'Ran (\d+) tests?',checked.stdout).group(1))
        if observed!=count:raise RuntimeError('unexpected suite count; update provenance review')
        logfile=out/(label+'.log');logfile.write_bytes(checked.stdout)
        suites[folder]={'command':argv,'passed':observed,'failures':0,'log_sha256':hashlib.sha256(checked.stdout).hexdigest()}
    # Probe only synthetic files in freshly allocated roots, not real projects.
    with tempfile.TemporaryDirectory(prefix='dmb-denial-') as directory:
        base=Path(directory);a=base/'A';b=base/'B';a.mkdir();b.mkdir();canary=b/'synthetic-canary';canary.write_bytes(b'synthetic-data-only')
        probes={}
        for op,code in [('read','from pathlib import Path; import sys; Path(sys.argv[1]).read_bytes()'),('write','from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(b"synthetic-updated")')]:
            proc=subprocess.run([sys.executable,'-I','-c',code,str(canary)],cwd=a,env={'PATH':'/usr/bin:/bin'},capture_output=True,timeout=3)
            probes[op]={'exit_code':proc.returncode,'access_denied':proc.returncode!=0 and b'PermissionError' in proc.stderr}
        isolation={'status':'PASS' if all(p['access_denied'] for p in probes.values()) else 'BLOCKED','scope':'same-UID synthetic cross-root negative read/write probe; not a Codex sandbox test','uid':os.geteuid(),'distinct_roots':True,'probes':probes,'real_or_secret_data_accessed':False}
    sources=('src/dci/master/authorization_contract.py','certification_tests/test_authorization_contract.py','tools/verify_phase8_authorization.py')
    result={'schema_version':1,'captured_at':datetime.now(timezone.utc).isoformat(),'outcome':'DMB LOCAL SHADOW PASS / FULL CERTIFICATION BLOCKED','suite_results':suites,'total_tests_passed':sum(s['passed'] for s in suites.values()),'previous_artifacts_verified':len(manifest['artifacts']),'previous_source_files_unchanged':len(original['source_sha256'])+len(prior['new_sources_sha256']),'preserved_historical_cycles':100,'preserved_historical_worker_test_executions':1099,'bundles':bundles,'os_isolation_probe':isolation,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'live_oauth_verified':False,'actual_bearer_tokens_used':False,'auth_services_installed':False,'external_messages_sent':False,'classification':'New policy tests are fixture-only authorization rules; they do not verify token signatures, OAuth flow, external identity or human approval','observed_git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()}
    (out/'LOCAL_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'preserved_tests_passed':suites['tests']['passed'],'new_fixture_tests_passed':suites['certification_tests']['passed'],'original_artifacts_unchanged':len(manifest['artifacts']),'os_isolation_gate':isolation['status'],'full_certification':'BLOCKED'}))


if __name__=='__main__':main()
