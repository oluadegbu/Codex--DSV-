"""Offline helpers for the hash-verified package; no installs or authentication changes."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
from datetime import datetime, timedelta, timezone


def verify_package(app_root):
    root = Path(app_root).parent.resolve(strict=True)
    manifest_path = root / 'PACKAGE_MANIFEST.json'
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('schema_version') != 1 or manifest.get('mode') != 'SHADOW' or manifest.get('package_version') != '0.1.0' or manifest.get('architecture') != 'windows-amd64':
        raise PermissionError('Unexpected versioned shadow package')
    files = manifest.get('files')
    source = manifest.get('source_commit')
    if not isinstance(source, str) or len(source) != 40 or any(c not in '0123456789abcdef' for c in source):
        raise PermissionError('Pinned upstream source commit required')
    if not isinstance(files, dict) or not 1 <= len(files) <= 5000:
        raise PermissionError('Bounded package file manifest required')
    for name, digest in files.items():
        part = PurePosixPath(name)
        if part.is_absolute() or '..' in part.parts or '\\' in name or ':' in name:
            raise PermissionError('Unsafe package file route')
        path = root / name
        if path.is_symlink() or not path.is_file() or root not in path.resolve(strict=True).parents or path.stat().st_size > 300 * 1048576:
            raise PermissionError('Package boundary or resource violation')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise PermissionError('Package integrity mismatch: ' + name)
    git = root / 'runtime/git/cmd/git.exe'
    if 'runtime/git/cmd/git.exe' not in files or not git.is_file():
        raise PermissionError('Pinned portable Git missing')
    # Only this process and its children use portable tools. No machine/user PATH changes.
    os.environ['PATH'] = str(git.parent) + os.pathsep + os.environ.get('PATH', '')
    return manifest


def initialize_package_git(app_root, manifest):
    root = Path(app_root)
    if (root / '.git').exists():
        return
    source_names = [name[4:] for name in manifest['files'] if name.startswith('app/')]
    if not source_names or 'CODEX.md' not in source_names:
        raise PermissionError('Reviewed application markers missing')
    subprocess.run(['git', 'init', '--quiet', str(root)], check=True, timeout=5)
    subprocess.run(['git', '-c', 'core.autocrlf=false', 'add', '--', *source_names], cwd=root, check=True, timeout=5)
    subprocess.run(['git', '-c', 'user.name=DCI Shadow Package', '-c', 'user.email=shadow@example.invalid', 'commit', '--quiet', '-m',
                    'Bind hash-verified package source ' + manifest['source_commit']], cwd=root, check=True, timeout=5)


def create_tls_certificate(certificate, private_key):
    """Generate private loopback TLS files. No OS trust store or external provider."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
            .sign(key, hashes.SHA256()))
    with Path(private_key).open('xb') as stream:
        stream.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        stream.flush(); os.fsync(stream.fileno())
    with Path(certificate).open('xb') as stream:
        stream.write(cert.public_bytes(serialization.Encoding.PEM)); stream.flush(); os.fsync(stream.fileno())
