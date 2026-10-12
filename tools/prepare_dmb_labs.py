"""Recreate reviewed isolated labs from pinned Git bundles. No remote access."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import os


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--destination',required=True);parser.add_argument('--manifest',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if os.name!='posix' or os.geteuid()==0 or 0 in os.getgroups():
        raise PermissionError('non-admin Linux lab certification required')
    destination=Path(args.destination).resolve()
    if root==destination or root in destination.parents or destination in root.parents:
        raise PermissionError('labs must be outside master workspace')
    config=json.loads((root/'portfolio/WORKERS.v1.json').read_text())
    for worker in config['workers']:
        bundle=root/worker['bundle']
        if hashlib.sha256(bundle.read_bytes()).hexdigest()!=worker['bundle_sha256']:
            raise ValueError('bundle digest mismatch')
        target=destination/worker['worker_id']
        if target.exists():
            raise FileExistsError('refusing to overwrite existing lab')
        subprocess.run(['git','clone','--quiet',str(bundle),str(target)],check=True)
        subprocess.run(['git','checkout','--quiet',worker['expected_commit']],cwd=target,check=True)
        # Relocation changes one tracked marker: review+commit this explicit scope.
        marker=json.loads((target/'WORKER_SCOPE.json').read_text());marker['workspace']=str(target)
        (target/'WORKER_SCOPE.json').write_text(json.dumps(marker,indent=2)+'\n')
        subprocess.run(['git','-c','user.name=DCI Shadow Worker','-c','user.email=shadow@example.invalid','add','WORKER_SCOPE.json'],cwd=target,check=True)
        subprocess.run(['git','-c','user.name=DCI Shadow Worker','-c','user.email=shadow@example.invalid','commit','--quiet','-m','Bind reviewed shadow lab to relocated workspace'],cwd=target,check=True)
        worker['workspace']=str(target)
        worker['expected_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=target).decode().strip()
    path=Path(args.manifest);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(config,indent=2)+'\n')


if __name__=='__main__':main()
