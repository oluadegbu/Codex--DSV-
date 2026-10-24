"""Offline CLI for an isolated, supplied export package. Never acquires data.
Package: manifest.json, quotes.csv, calendar.json, proofs/<role>.txt.
Trust registry is repository-owned; dataset content cannot replace it.
"""
import argparse,json
from pathlib import Path
from .certify import certify,PROOFS

REGISTRY=Path(__file__).with_name('reviewed_bundles.json')

def bounded(root,name,limit):
    root=Path(root).resolve();relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe package path')
    p=root/relative
    q=root
    for part in relative.parts:
        q=q/part
        if q.is_symlink():raise ValueError('package symlink denied')
    if not p.is_file() or p.stat().st_size>limit:raise ValueError('missing or oversized package member')
    return p.read_bytes()

def run(root,asof):
    manifest=json.loads(bounded(root,'manifest.json',65536))
    raw=bounded(root,'quotes.csv',128*1024*1024)
    calendar=bounded(root,'calendar.json',32*1024*1024)
    proofs={}
    for role in PROOFS:
        try:proofs[role]=bounded(root,'proofs/'+role+'.txt',65536)
        except ValueError:pass
    registry=json.loads(REGISTRY.read_text())['bundle_sha256']
    return certify(manifest,raw,calendar,proofs,registry,asof)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--asof',type=int,required=True)
    a=p.parse_args();r=run(a.package,a.asof);print(json.dumps(r,sort_keys=True,indent=2))
    if r['status']!='CERTIFIED_RESEARCH_DATA':raise SystemExit(2)
