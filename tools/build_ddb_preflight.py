"""Offline reproducible test-only addon. Does not rebuild/install worker/runtime."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile
ROOT=Path(__file__).resolve().parents[1]
INPUTS={
 'probe.py':'preflight/ddb-10.5A/probe.py',
 'contracts.py':'preflight/ddb-10.5A/contracts.py',
 'README.md':'preflight/ddb-10.5A/README.md',
 **{'tests/'+n:'ddb_tests/'+n for n in ('test_document_bridge.py','test_windows_adapter.py','test_windows_process_fixture.py')},
}


def assemble():
 source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 files={out:subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT) for out,name in INPUTS.items()}
 manifest={'schema_version':1,'kind':'TEST_ADDON_NOT_WORKER','source_commit':source,
 'worker_package_sha256':'06a5eded7bcfc3ad2cbecf9140e47b88f6a65848c6929847f1de7dd8281791e0',
 'contains_credentials':False,'native_tests_executed':False,'activation_authority':False,
 'files':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}}
 files['ADDON_MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 data=io.BytesIO()
 with zipfile.ZipFile(data,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
   out.writestr(info,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
 return data.getvalue(),manifest,files['ADDON_MANIFEST.json']


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 raw,manifest,m=assemble();a.output.mkdir(parents=True,exist_ok=False)
 name='DDB-Preflight-10.5A-'+manifest['source_commit'][:12]+'.zip';(a.output/name).write_bytes(raw)
 record={'filename':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'manifest_sha256':hashlib.sha256(m).hexdigest(),'source_commit':manifest['source_commit'],'kind':manifest['kind']}
 (a.output/'ADDON_RELEASE.json').write_text(json.dumps(record,indent=2)+'\n');(a.output/'ADDON_MANIFEST.json').write_bytes(m)
 print(json.dumps(record))


if __name__=='__main__':main()
