"""Fixed official Codex162.1 discovery and content verification; never execute PATH candidates."""
import hashlib
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import platform
import subprocess
import struct
from contextlib import contextmanager, ExitStack

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


class FileInformation(ctypes.Structure):
    _fields_ = [('attributes', wintypes.DWORD), ('created', wintypes.FILETIME),
                ('accessed', wintypes.FILETIME), ('written', wintypes.FILETIME),
                ('volume', wintypes.DWORD), ('size_high', wintypes.DWORD),
                ('size_low', wintypes.DWORD), ('links', wintypes.DWORD),
                ('index_high', wintypes.DWORD), ('index_low', wintypes.DWORD)]


def kernel_api():
    if os.name != 'nt': raise PermissionError('Native Windows path validation required')
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateFileW': ([wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE], wintypes.HANDLE),
        'CloseHandle': ([wintypes.HANDLE], wintypes.BOOL),
        'GetFileAttributesW': ([wintypes.LPCWSTR], wintypes.DWORD),
        'GetFinalPathNameByHandleW': ([wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD], wintypes.DWORD),
        'GetFileInformationByHandle': ([wintypes.HANDLE, ctypes.POINTER(FileInformation)], wintypes.BOOL),
        'DeviceIoControl': ([wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL),
        'QueryFullProcessImageNameW': ([wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
    }
    for name, (args, result) in signatures.items():
        getattr(k, name).argtypes, getattr(k, name).restype = args, result
    return k


@contextmanager
def native_handle(path, directory=False, reparse=False):
    k = kernel_api()
    # Read-only sharing denies concurrent write/delete opens; no ACL mutation.
    flags = (0x02000000 if directory else 0) | (0x00200000 if reparse else 0)
    handle = k.CreateFileW(str(path), 0x80 if directory else 0x80000000, 1, None, 3, flags, None)
    if handle == ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
    try: yield handle
    finally: k.CloseHandle(handle)


def file_information(handle):
    value = FileInformation()
    if not kernel_api().GetFileInformationByHandle(handle, ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return value


def file_identity(handle):
    value = file_information(handle)
    return value.volume, value.index_high, value.index_low


def final_path(handle):
    buffer = ctypes.create_unicode_buffer(32768)
    length = kernel_api().GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    if not length or length >= len(buffer): raise PermissionError('Native final executable path unavailable')
    value = buffer.value
    if not value.startswith('\\\\?\\') or value.startswith('\\\\?\\UNC\\'):
        raise PermissionError('Local native DOS volume path required')
    return Path(value[4:])


def strict_components(path):
    k = kernel_api()
    for component in (path, *path.parents):
        attributes = k.GetFileAttributesW(str(component))
        if attributes == 0xFFFFFFFF: raise ctypes.WinError(ctypes.get_last_error())
        if attributes & 0x400:
            raise PermissionError('Untrusted Codex reparse component rejected: ' + str(component))


def junction_target(handle):
    data = ctypes.create_string_buffer(16384); returned = wintypes.DWORD()
    if not kernel_api().DeviceIoControl(handle, 0x900A8, None, 0, data, len(data), ctypes.byref(returned), None):
        raise ctypes.WinError(ctypes.get_last_error())
    raw = data.raw[:returned.value]
    if len(raw) < 16 or struct.unpack_from('<I', raw)[0] != 0xA0000003:
        raise PermissionError('Only exact official installation mount-point junctions allowed')
    offset, size = struct.unpack_from('<HH', raw, 8)
    if size % 2 or 16 + offset + size > len(raw): raise PermissionError('Invalid junction data')
    target = raw[16 + offset:16 + offset + size].decode('utf-16-le')
    if not target.startswith('\\??\\') or target.startswith('\\??\\UNC\\'):
        raise PermissionError('Absolute local official junction target required')
    return Path(target[4:])


def canonical_path(path, profile=None, arch=None):
    path = Path(path)
    if not path.is_absolute() or path.name.casefold() != 'codex.exe':
        raise PermissionError('Canonical native codex.exe required')
    if os.name != 'nt':
        if path.resolve(strict=True) != path.absolute(): raise PermissionError('Codex redirected path rejected')
        return path.resolve(strict=True)
    # The sole exception is the installer-owned bin -> standalone/current/bin
    # -> releases/<exact pinned version>/bin layout. Never execute either alias.
    if profile is not None:
        profile = Path(profile)
        primary = profile / 'AppData/Local/Programs/OpenAI/Codex/bin/codex.exe'
        if path == primary:
            standalone = profile / '.codex/packages/standalone'
            release = standalone / ('releases/0.162.1-' + (arch or architecture()) + '-pc-windows-msvc/bin/codex.exe')
            aliases = {primary.parent: standalone / 'current/bin', standalone / 'current': release.parent.parent}
            with ExitStack() as locks:
                for alias, target in aliases.items():
                    attributes = kernel_api().GetFileAttributesW(str(alias))
                    if attributes == 0xFFFFFFFF: raise ctypes.WinError(ctypes.get_last_error())
                    if attributes & 0x400:
                        handle = locks.enter_context(native_handle(alias, directory=True, reparse=True))
                        if junction_target(handle) != target:
                            raise PermissionError('Official Codex junction target mismatch: ' + str(alias))
                    elif alias == primary.parent:
                        # Non-junction official user-local installs retain the strict gate.
                        strict_components(path)
                        return path.resolve(strict=True)
                    else: raise PermissionError('Official standalone current junction required')
                # Other original ancestors, including executable symlinks, stay rejected.
                for component in (path, *path.parents):
                    attributes = kernel_api().GetFileAttributesW(str(component))
                    if attributes == 0xFFFFFFFF: raise ctypes.WinError(ctypes.get_last_error())
                    if attributes & 0x400 and component not in aliases:
                        raise PermissionError('Untrusted Codex reparse component rejected: ' + str(component))
                strict_components(release)
                with native_handle(path) as handle:
                    resolved = final_path(handle)
                    with native_handle(release) as expected:
                        if resolved != final_path(expected) or file_identity(handle) != file_identity(expected):
                            raise PermissionError('Official Codex final path/file identity mismatch')
                strict_components(resolved)
                return resolved
    strict_components(path)
    with native_handle(path) as handle: return final_path(handle)


@contextmanager
def pinned_image(path):
    """Pin every final-path ancestor and exact file through suspended creation."""
    path = canonical_path(path)
    with ExitStack() as locks:
        for component in reversed(path.parents):
            handle = locks.enter_context(native_handle(component, directory=True, reparse=True))
            if file_information(handle).attributes & 0x400:
                raise PermissionError('Final executable ancestor changed to reparse point')
        handle = locks.enter_context(native_handle(path, reparse=True))
        if file_information(handle).attributes & 0x400 or final_path(handle) != path:
            raise PermissionError('Final executable changed while acquiring pins')
        # Independent reader shares only READ with the pinned image handle.
        with path.open('rb') as stream: verify_stream(stream, architecture())
        yield path, file_identity(handle)


def verify_suspended_image(process, expected_path, expected_identity):
    buffer = ctypes.create_unicode_buffer(32768); size = wintypes.DWORD(len(buffer))
    if not kernel_api().QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    path = canonical_path(buffer.value)
    with native_handle(path) as handle:
        if path != expected_path or file_identity(handle) != expected_identity:
            raise PermissionError('Suspended process image differs from pinned executable')


def verified_path(path, arch, profile=None):
    path = canonical_path(path, profile, arch)
    with path.open('rb') as stream: verify_stream(stream, arch)
    return path


def discover(local_appdata, path_query, arch):
    primary = Path(local_appdata) / 'Programs/OpenAI/Codex/bin/codex.exe'
    # Existing user-local installation wins. Its failed verification is terminal.
    if primary.exists() or primary.is_symlink(): return verified_path(primary, arch, Path(local_appdata).parent.parent)
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
