"""Fixed Scheduled Task entry. No registration, elevation or external configuration discovery."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
VERSION = '0.2.0-review1'
HOST = 'WIN-HQAAFGGU1AM'
USER_SID = 'S-1-5-21-3675741470-1525898003-3877381073-1000'
NAMESPACE = 'DMBWindowsWorker-ops-0.2.0-review1'


def validate_grant(grant, manifest, manifest_digest, task_digest, now):
    fields = {'version','approval_reference','host','user_sid','source_commit','manifest_sha256',
              'task_xml_sha256','issued_at','expires_at','operation','relay_endpoint','worker_pairing_sha256',
              'isolation_manifest_sha256','Windows_acceptance_sha256'}
    if type(grant) is not dict or set(grant) != fields or grant['version'] != 1 or not isinstance(grant['approval_reference'],str) or not grant['approval_reference'].strip():
        raise PermissionError('Final explicitly approved deployment grant required')
    if grant['host'] != HOST or grant['user_sid'] != USER_SID or grant['source_commit'] != manifest['source_commit'] or grant['manifest_sha256'] != manifest_digest or grant['task_xml_sha256'] != task_digest or grant['operation'] != 'windows_codex_ping':
        raise PermissionError('Deployment grant does not bind exact reviewed package/task/identity')
    if type(grant['issued_at']) is not int or type(grant['expires_at']) is not int or not grant['issued_at'] <= now < grant['expires_at'] <= grant['issued_at']+3600:
        raise PermissionError('Deployment acceptance window expired or exceeds one hour')
    from dci.master.windows_protocol import endpoint
    endpoint(grant['relay_endpoint'])
    from urllib.parse import urlsplit
    import ipaddress
    name=urlsplit(grant['relay_endpoint']).hostname
    if name.casefold()=='localhost': raise PermissionError('Actual approved remote relay required; no loopback substitution')
    try:
        address=ipaddress.ip_address(name)
    except ValueError: address=None
    if address and (address.is_loopback or address.is_unspecified or address.is_link_local):
        raise PermissionError('Actual approved remote relay required')
    for field in ('worker_pairing_sha256','isolation_manifest_sha256','Windows_acceptance_sha256'):
        if type(grant[field]) is not str or len(grant[field]) != 64 or any(c not in '0123456789abcdef' for c in grant[field]):
            raise PermissionError('Exact pairing and real preactivation evidence digests required')
    return grant


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seconds',type=int,default=3600)
    parser.add_argument('--preflight',action='store_true');args=parser.parse_args()
    from dci.master.windows_native import require_identity,token_snapshot,local_appdata,private_root,dpapi
    identity=require_identity();token=token_snapshot()  # Before authentication or creating anything.
    if token['user_sid'] != USER_SID or identity['host'] != HOST:
        raise PermissionError('Exact approved local DirectiveCodex SID/host required')
    expected=local_appdata()/'Directive'/'DMB-OPS-0.2.0-review1'/'package'/'app'
    if ROOT != expected or not 1 <= args.seconds <= 3600:
        raise PermissionError('Exact isolated deployment path and bounded duration required')
    from windows_package_runtime import verify_package
    manifest=verify_package(ROOT,VERSION)
    if manifest is None: raise PermissionError('Self-contained reviewed package required')
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    task=ROOT/'deployment/phase10/Directive.DMB.ShadowWorker.Phase10.xml'
    private=private_root(NAMESPACE)
    approval=private/'activation.dpapi'
    if not approval.is_file(): raise PermissionError('Final approval/remote pairing absent; no worker started')
    grant=json.loads(dpapi(approval.read_bytes(),False))
    now=int(time.time())
    validate_grant(grant,manifest,sha(ROOT.parent/'PACKAGE_MANIFEST.json'),sha(task),now)
    pairing=private/'pairing.dpapi'
    if sha(pairing) != grant['worker_pairing_sha256']: raise PermissionError('Private worker pairing drift')
    cfg=json.loads(dpapi(pairing.read_bytes(),False))
    from dci.master.windows_worker import bridge_fingerprint
    if cfg.get('endpoint') != grant['relay_endpoint'] or cfg.get('bridge_sha256') != bridge_fingerprint() or cfg.get('expires',0) < grant['expires_at']:
        raise PermissionError('Approved remote pairing/source/expiry mismatch')
    isolation=private/'isolation-creator-manifest.json';acceptance=private/'WINDOWS_ACCEPTANCE.json'
    if sha(isolation) != grant['isolation_manifest_sha256'] or sha(acceptance) != grant['Windows_acceptance_sha256']:
        raise PermissionError('Preactivation evidence changed')
    evidence=json.loads(acceptance.read_text())
    if evidence.get('bridge_sha256') != bridge_fingerprint() or evidence.get('identity') != identity or any(evidence.get(k) != 'PASS' for k in ('genuine_task','cancellation','owned_worker_crash_recovery','OS_access_denial')):
        raise PermissionError('Actual Windows preactivation gates not all certified for this package')
    from dci.master.windows_isolation import probe
    if probe(isolation,NAMESPACE)['OS_canary_access_denial'] != 'PASS':
        raise PermissionError('Actual OS access denial no longer passes')
    if args.preflight:
        print(json.dumps({'mode':'SHADOW','preflight':'PASS','worker_started':False,'task_registered':False}));return
    from dci.master.windows_operations_worker import run
    # A fixed local STOP file drains this owner's current bounded task, then exits.
    # No mailbox-supplied path or command and no scheduled-task self-modification.
    remaining=min(args.seconds,grant['expires_at']-int(time.time()))
    if remaining <= 120: raise PermissionError('Approval expired before worker start')
    print(json.dumps(run(remaining-120,isolation,private/'STOP')))


if __name__=='__main__':
    try: main()
    except (PermissionError,FileNotFoundError,ValueError) as error:
        # A policy/approval block exits successfully so Task Scheduler does not
        # blindly retry. Print only fixed classification, never keys/raw errors.
        print(json.dumps({'mode':'SHADOW','state':'NEEDS_HUMAN','reason':type(error).__name__,
                          'worker_activation':'BLOCKED','automatic_retry':False,'journals_retained':True}))
