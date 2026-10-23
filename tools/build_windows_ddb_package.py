"""Reproducible Windows DDB package from an existing hash-pinned runtime ZIP.

Offline: no downloads, installer, credential enrollment or native worker launch.
--source-only produces a review archive, explicitly NOT a runnable Windows ZIP.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '38b395f3609900d1c5423fc9ed4f02413397db8728c2c27d66ae576308ead5f6'
BASE_URL = 'https://github.com/oluadegbu/Codex--DSV-/releases/download/dmb-windows-v0.3.0-a46705985abd/DMB-Windows-0.3.0-a46705985abd-amd64.zip'
VERSION = '0.4.0-ddb-review1'


def sha(data): return hashlib.sha256(data).hexdigest()


def collect(source_only=False, base_zip=None):
    files = {}
    if not source_only:
        if base_zip is None or sha(Path(base_zip).read_bytes()) != BASE_SHA:
            raise PermissionError('Exact certified base runtime ZIP required')
        with zipfile.ZipFile(base_zip) as base:
            for item in base.infolist():
                p = PurePosixPath(item.filename)
                if (p.is_absolute() or '..' in p.parts or '\\' in item.filename or ':' in item.filename
                        or (item.external_attr >> 16) & 0o170000 == 0o120000):
                    raise PermissionError('Unsafe base archive member')
                if not item.is_dir() and item.filename.startswith('runtime/'):
                    files[item.filename] = base.read(item)
        if 'runtime/python/python.exe' not in files or 'runtime/git/cmd/git.exe' not in files:
            raise PermissionError('Pinned base runtime incomplete')
    # Tracked committed bytes only; runtime files, signing state and Git credentials
    # are excluded by construction. No mutable worktree files enter the archive.
    names = subprocess.check_output(['git','ls-files','src','schemas','portfolio/REGISTRY.v1.json',
             'CODEX.md','SUPERVISOR_POLICY.md','README.md','.gitignore',
             'tools/run_windows_ddb.py','tools/certify_ddb_foreground.py','deployment/ddb/windows-request-0011'],cwd=ROOT,text=True).splitlines()
    for name in names:
        files['app/'+name] = subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)
    source = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest = {'schema_version':1,'version':VERSION,'mode':'SHADOW','source_commit':source,
                'kind':'SOURCE_REVIEW_ONLY' if source_only else 'WINDOWS_FOREGROUND_REVIEW_PACKAGE',
                'base_zip_sha256':None if source_only else BASE_SHA,
                'dependencies':{'CPython':'3.12.10','MinGit':'2.51.0.windows.1',
                                'cryptography':'46.0.2','cffi':'2.0.0','pycparser':'2.23',
                                'Codex':'existing official 0.162.1; not bundled'},
                'authorization':'NO_DEPLOYMENT_ENROLLMENT_EXECUTION_OR_SCHEDULER_AUTHORITY',
                'files':{name:sha(value) for name,value in sorted(files.items())}}
    files['DDB_PACKAGE_MANIFEST.json'] = (json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    return files, manifest


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for name, value in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644 << 16
            out.writestr(info,value,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    return stream.getvalue()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-zip',type=Path)
    p.add_argument('--source-only',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();files,manifest=collect(a.source_only,a.base_zip)
    a.output.mkdir(parents=True,exist_ok=False)
    raw=archive(files);name='DMB-DDB-'+VERSION+'-'+manifest['source_commit'][:12]+('-source' if a.source_only else '-windows-amd64')+'.zip'
    (a.output/name).write_bytes(raw)
    record={'filename':name,'sha256':sha(raw),'bytes':len(raw),'manifest_sha256':sha(files['DDB_PACKAGE_MANIFEST.json']),
            'kind':manifest['kind'],'source_commit':manifest['source_commit'],'base_zip_sha256':manifest['base_zip_sha256']}
    (a.output/'RELEASE.json').write_text(json.dumps(record,indent=2)+'\n')
    (a.output/'SHA256SUMS.txt').write_text(record['sha256']+'  '+name+'\n')
    print(json.dumps(record))


if __name__=='__main__': main()
