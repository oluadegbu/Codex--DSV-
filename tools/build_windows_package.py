"""Build a version-pinned offline Windows ZIP, never an installer."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch(url, destination, expected=None):
    if not url.startswith('https://'):
        raise PermissionError('HTTPS dependency origin required')
    with urllib.request.urlopen(url, timeout=60) as response, Path(destination).open('xb') as stream:
        shutil.copyfileobj(response, stream)
    value = digest(destination)
    if expected and value != expected:
        raise PermissionError('Pinned dependency digest mismatch')
    return value


def unpack(archive, destination):
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            name = PurePosixPath(item.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in item.filename or ':' in item.filename:
                raise PermissionError('Archive boundary violation')
        bundle.extractall(destination)


def build(output):
    if os.name != 'nt' or sys.version_info[:3] != (3, 12, 10):
        raise PermissionError('Windows AMD64 builder with pinned Python3.12.10 required')
    inputs = json.loads((ROOT / 'packaging/WINDOWS_INPUTS.json').read_text())
    if output.exists(): raise PermissionError('Fresh output required; no release overwrite')
    output.mkdir(parents=True)
    downloads = output / 'inputs'; downloads.mkdir()
    package = output / 'DMB-Windows-0.1.0-amd64'; package.mkdir()
    runtime = package / 'runtime'; runtime.mkdir()
    python_zip, git_zip = downloads / 'python.zip', downloads / 'mingit.zip'
    python_hash = fetch(inputs['python_url'], python_zip)
    fetch(inputs['git_url'], git_zip, inputs['git_sha256'])
    unpack(python_zip, runtime / 'python'); unpack(git_zip, runtime / 'git')
    (runtime / 'python/python312._pth').write_bytes(b'python312.zip\n.\n../../app/src\n../../app/tools\nimport site\n')
    subprocess.run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', '--no-deps',
                    '--dest', str(downloads / 'wheels'), '-r', str(ROOT / 'packaging/windows-build-requirements.txt')], check=True, timeout=120)
    wheel_inputs = []
    for wheel in sorted((downloads / 'wheels').glob('*.whl')):
        name, version = wheel.name.split('-')[:2]
        with urllib.request.urlopen('https://pypi.org/pypi/' + name + '/' + version + '/json', timeout=30) as response:
            metadata = json.load(response)
        expected = next(p['digests']['sha256'] for p in metadata['urls'] if p['filename'] == wheel.name)
        if digest(wheel) != expected: raise PermissionError('Official PyPI wheel digest mismatch')
        unpack(wheel, runtime / 'python')
        wheel_inputs.append({'name': wheel.name, 'sha256': expected, 'origin': 'https://pypi.org/pypi/' + name + '/' + version + '/json'})
    if len(wheel_inputs) != 3: raise PermissionError('Exact three bundled wheel dependencies required')
    # Export committed bytes, not platform-converted checkouts or runtime artifacts.
    names = subprocess.check_output(['git', 'ls-files', 'src', 'schemas', 'portfolio/REGISTRY.v1.json', 'CODEX.md',
                                     'SUPERVISOR_POLICY.md', 'README.md', '.gitignore', 'tools/run_windows_shadow_bridge.py',
                                     'tools/windows_package_runtime.py'], cwd=ROOT, text=True).splitlines()
    for name in names:
        target = package / 'app' / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT))
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest = {**inputs, 'source_commit': source, 'python_archive_sha256': python_hash, 'wheel_inputs': wheel_inputs,
                'files': {p.relative_to(package).as_posix(): digest(p) for p in sorted(package.rglob('*')) if p.is_file()},
                'execution': 'existing DirectiveCodex Medium non-admin only; foreground loopback, no installer',
                'upstream_source': 'https://github.com/git-for-windows/git/tree/v2.51.0.windows.1',
                'runtime_license_notice': 'CPython LICENSE.txt and wheel dist-info licenses included; MinGit licenses retained from upstream ZIP. Git corresponding source/build records are linked above.'}
    (package / 'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    subprocess.run([sys.executable, str(ROOT / 'tools/check_windows_package.py'), '--package', str(package),
                    '--output', str(output / 'PACKAGE_SMOKE.json')], check=True, timeout=60)
    archive = output / ('DMB-Windows-0.1.0-' + source[:12] + '-amd64.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(package.rglob('*')):
            if path.is_file(): bundle.write(path, path.relative_to(package).as_posix())
    release = {'schema_version': 1, 'mode': 'SHADOW', 'version': '0.1.0', 'tag': 'dmb-windows-v0.1.0-' + source[:12],
               'source_commit': source, 'filename': archive.name, 'sha256': digest(archive), 'bytes': archive.stat().st_size,
               'package_manifest_sha256': digest(package / 'PACKAGE_MANIFEST.json'), 'smoke_evidence_sha256': digest(output / 'PACKAGE_SMOKE.json'),
               'Windows_genuine_task': 'NOT TESTED; requires existing DirectiveCodex foreground session',
               'signature': 'SHA-256 verified release ZIP; CPython executable Authenticode checked in CI; DCI ZIP not Authenticode signed'}
    (output / 'RELEASE.json').write_text(json.dumps(release, indent=2) + '\n')
    (output / 'SHA256SUMS.txt').write_text(release['sha256'] + '  ' + archive.name + '\n')
    print(json.dumps(release, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output.resolve())
