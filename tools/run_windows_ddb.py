"""Approved foreground only. No enrollment or unattended activation path."""
import hashlib
import json
import os
from pathlib import Path
import sys


def verify(root):
    if os.name != 'nt': raise PermissionError('Native Windows required')
    # Import only after package integrity is verified below.
    manifest = json.loads((root/'DDB_PACKAGE_MANIFEST.json').read_text())
    if manifest.get('version') != '0.4.0-ddb-review1' or manifest.get('kind') != 'WINDOWS_FOREGROUND_REVIEW_PACKAGE':
        raise PermissionError('Runnable hash-pinned Windows DDB package required')
    for name, expected in manifest['files'].items():
        from pathlib import PurePosixPath
        parts=PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or '\\' in name or ':' in name:
            raise PermissionError('Package route rejected')
        path=root/name
        for component in (path,*path.parents):
            if component.is_symlink() or (component.exists() and getattr(component.lstat(),'st_file_attributes',0)&0x400):
                raise PermissionError('Package reparse boundary rejected')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise PermissionError('Package content changed')
    # Reject unmanifested executable/import sources, including injected .pyc/.pyd.
    actual={p.relative_to(root).as_posix() for folder in ('app','runtime') for p in (root/folder).rglob('*') if p.is_file()}
    if actual != set(manifest['files']):raise PermissionError('Unexpected package files')
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(root/'app/src'))
    from dci.master.windows_native import require_identity
    require_identity()
    return manifest


def main():
    root=Path(__file__).resolve().parents[2]
    verify(root)
    if '--foreground-certification' not in sys.argv:
        raise PermissionError('Only separately approved bounded foreground mode permitted')
    if '--certify-cycle' in sys.argv:
        sys.argv.remove('--certify-cycle');sys.argv.remove('--foreground-certification')
        from certify_ddb_foreground import main as certify
        certify()
    else:
        from dci.master.document_cli import main as cli
        cli()


if __name__=='__main__':
    try: main()
    except Exception as error:
        # No private configuration, response bodies, model text or raw exceptions.
        print(json.dumps({'status':'BLOCKED_PRESERVED_FAIL_CLOSED','category':type(error).__name__}),file=sys.stderr)
        raise SystemExit(1)
