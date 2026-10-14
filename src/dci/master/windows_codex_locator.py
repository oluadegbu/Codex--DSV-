"""Fixed official Codex162.1 discovery and content verification; never execute PATH candidates."""
import hashlib
from pathlib import Path
import platform
import subprocess

# Authenticated OpenAI GitHub release metadata, rust-v0.162.1, raw exe assets.
OFFICIAL_CODEX = {
    'x86_64': (333479728, 'dd13bdb162a184fa04039488b234a8258ef9b76f84e926c505d5742b19249a6a'),
    'aarch64': (282434864, '3afc6a5195ce3fc08ee69b99521773b1542f129ee5b68dd4f0bb10cf7930c6ef'),
}


def architecture():
    value = platform.machine().casefold()
    if value in {'amd64', 'x86_64'}: return 'x86_64'
    if value in {'arm64', 'aarch64'}: return 'aarch64'
    raise PermissionError('Unsupported Codex architecture; no guessed fallback')


def verify_stream(stream, arch):
    size, expected = OFFICIAL_CODEX[arch]
    digest = hashlib.sha256(); total = 0
    while True:
        chunk = stream.read(1048576)
        if not chunk: break
        total += len(chunk)
        if total > size: raise PermissionError('Codex size differs from official pinned release')
        digest.update(chunk)
    if total != size or digest.hexdigest() != expected:
        raise PermissionError('Codex SHA-256 differs from official pinned v0.162.1; no alternative selected')
    return expected


def verified_path(path, arch):
    path = Path(path)
    if not path.is_absolute() or path.name.casefold() != 'codex.exe' or path.is_symlink() or path.resolve(strict=True) != path.absolute():
        raise PermissionError('Canonical native codex.exe required; redirects rejected')
    with path.open('rb') as stream: verify_stream(stream, arch)
    return path


def discover(local_appdata, path_query, arch):
    primary = Path(local_appdata) / 'Programs/OpenAI/Codex/bin/codex.exe'
    # Existing user-local installation wins. Its failed verification is terminal.
    if primary.exists() or primary.is_symlink(): return verified_path(primary, arch)
    try: source = path_query().strip()
    except subprocess.CalledProcessError as exc:
        raise FileNotFoundError('Verified user-local Codex absent and PATH discovery unavailable; no install/fallback/elevation') from exc
    path = Path(source)
    if not path.is_absolute(): raise PermissionError('Native absolute installation path required')
    if path.name.casefold() == 'codex.exe': return verified_path(path, arch)
    if path.name.casefold() not in {'codex.cmd', 'codex.ps1'}:
        raise PermissionError('Unrecognized Codex launcher; no execution')
    package = 'codex-win32-arm64' if arch == 'aarch64' else 'codex-win32-x64'
    triple = arch + '-pc-windows-msvc'
    npm = path.parent / 'node_modules/@openai'
    for root in (npm / package, npm / 'codex', npm / 'codex/node_modules/@openai' / package):
        for leaf in ('bin/codex.exe', 'codex/codex.exe'):
            candidate = root / 'vendor' / triple / leaf
            if candidate.exists(): return verified_path(candidate, arch)
    raise FileNotFoundError('Official pinned native Codex not resolved; no install/fallback/elevation')
