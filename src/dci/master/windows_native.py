"""User-mode Windows identity, DPAPI and owned Job Object primitives.

Never create identities, alter ACL/firewalls, impersonate, elevate or install a
service. This module is deliberately unavailable on other operating systems.
"""
import base64
import csv
import ctypes
from ctypes import wintypes as w
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time
from contextlib import contextmanager


def dll(name):
    if os.name != "nt":
        raise PermissionError("actual Windows runtime required")
    return ctypes.WinDLL(name, use_last_error=True)


def system_directory():
    kernel = dll("kernel32")
    buffer = ctypes.create_unicode_buffer(32768)
    if not kernel.GetSystemDirectoryW(buffer, len(buffer)):
        raise ctypes.WinError(ctypes.get_last_error())
    return Path(buffer.value)


class SidAndAttributes(ctypes.Structure):
    _fields_ = [("sid", ctypes.c_void_p), ("attributes", w.DWORD)]


class TokenGroups(ctypes.Structure):
    _fields_ = [("count", w.DWORD), ("groups", SidAndAttributes * 1)]


def token_snapshot():
    """Read the real process token; reject thread impersonation. Never impersonate/elevate."""
    kernel, advapi = dll("kernel32"), dll("advapi32")
    signatures = {
        "GetCurrentProcess": ([], w.HANDLE), "GetCurrentThread": ([], w.HANDLE),
        "CloseHandle": ([w.HANDLE], w.BOOL),
        "GetComputerNameW": ([w.LPWSTR, ctypes.POINTER(w.DWORD)], w.BOOL),
        "LocalFree": ([ctypes.c_void_p], ctypes.c_void_p),
    }
    for name, (args, result) in signatures.items():
        getattr(kernel, name).argtypes, getattr(kernel, name).restype = args, result
    signatures = {
        "OpenProcessToken": ([w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)], w.BOOL),
        "OpenThreadToken": ([w.HANDLE, w.DWORD, w.BOOL, ctypes.POINTER(w.HANDLE)], w.BOOL),
        "GetTokenInformation": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD)], w.BOOL),
        "ConvertSidToStringSidW": ([ctypes.c_void_p, ctypes.POINTER(w.LPWSTR)], w.BOOL),
        "LookupAccountSidW": ([w.LPCWSTR, ctypes.c_void_p, w.LPWSTR, ctypes.POINTER(w.DWORD), w.LPWSTR, ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD)], w.BOOL),
    }
    for name, (args, result) in signatures.items():
        getattr(advapi, name).argtypes, getattr(advapi, name).restype = args, result
    thread = w.HANDLE()
    if advapi.OpenThreadToken(kernel.GetCurrentThread(), 8, True, ctypes.byref(thread)):
        kernel.CloseHandle(thread)
        raise PermissionError("impersonated thread token forbidden")
    if ctypes.get_last_error() != 1008:  # ERROR_NO_TOKEN is the only allowed absence.
        raise ctypes.WinError(ctypes.get_last_error())
    token = w.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    def information(kind):
        needed = w.DWORD()
        if advapi.GetTokenInformation(token, kind, None, 0, ctypes.byref(needed)) or ctypes.get_last_error() != 122 or not 1 <= needed.value <= 1048576:
            raise PermissionError("token-information sizing failed closed")
        data = ctypes.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token, kind, data, len(data), ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())
        return data
    def sid_string(sid):
        output = w.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(output)):
            raise ctypes.WinError(ctypes.get_last_error())
        try: return output.value
        finally: kernel.LocalFree(ctypes.cast(output, ctypes.c_void_p))
    try:
        host_buffer = ctypes.create_unicode_buffer(32768); host_size = w.DWORD(len(host_buffer))
        if not kernel.GetComputerNameW(host_buffer, ctypes.byref(host_size)):
            raise ctypes.WinError(ctypes.get_last_error())
        user_data = information(1)  # TokenUser: SID_AND_ATTRIBUTES
        user = SidAndAttributes.from_buffer(user_data)
        name_size, domain_size, use = w.DWORD(32768), w.DWORD(32768), w.DWORD()
        name, domain = ctypes.create_unicode_buffer(name_size.value), ctypes.create_unicode_buffer(domain_size.value)
        if not advapi.LookupAccountSidW(None, user.sid, name, ctypes.byref(name_size), domain, ctypes.byref(domain_size), ctypes.byref(use)) or use.value != 1:
            raise PermissionError("process token must resolve to an actual user")
        group_data = information(2)  # TokenGroups, includes disabled/deny-only membership.
        count = w.DWORD.from_buffer(group_data).value
        offset = TokenGroups.groups.offset
        if count > 4096 or offset + count * ctypes.sizeof(SidAndAttributes) > len(group_data):
            raise PermissionError("invalid token group buffer")
        groups = (SidAndAttributes * count).from_buffer(group_data, offset)
        integrity_data = information(25)  # TokenIntegrityLevel, separate mandatory label.
        # Fixed-size TOKEN_ELEVATION must be queried with its real DWORD buffer;
        # unlike variable-length classes, Windows may reject a null sizing probe.
        elevation = w.DWORD(); elevation_size = w.DWORD()
        if not advapi.GetTokenInformation(token, 20, ctypes.byref(elevation), ctypes.sizeof(elevation), ctypes.byref(elevation_size)) or elevation_size.value != ctypes.sizeof(elevation):
            raise ctypes.WinError(ctypes.get_last_error())
        return {"host": host_buffer.value, "user": domain.value + "\\" + name.value,
                "user_sid": sid_string(user.sid), "group_sids": [sid_string(g.sid) for g in groups],
                "integrity_sid": sid_string(SidAndAttributes.from_buffer(integrity_data).sid),
                "elevated": bool(elevation.value)}
    finally:
        kernel.CloseHandle(token)


def require_identity():
    token = token_snapshot()
    if token["user"].casefold() != (token["host"] + "\\DirectiveCodex").casefold() or token["elevated"] or "S-1-5-32-544" in token["group_sids"] or token["integrity_sid"] != "S-1-16-8192":
        raise PermissionError("DirectiveCodex non-admin Medium-integrity token required; " +
                              "user=" + token["user"] + "; elevated=" + str(token["elevated"]) +
                              "; administrators_member=" + str("S-1-5-32-544" in token["group_sids"]) +
                              "; integrity_sid=" + token["integrity_sid"])
    return {"host": token["host"], "user": token["host"] + "\\DirectiveCodex", "administrator": False, "integrity": "Medium"}


def private_root(namespace="DMBWindowsWorker-v1-0.1.3"):
    if namespace not in {"DMBWindowsWorker-v1-0.1.3", "DMBWindowsWorker-ops-0.2.0-review1", "DMBWindowsWorker-ops-0.3.0",
                         "DMBWindowsWorker-cert-0.3.0-success", "DMBWindowsWorker-cert-0.3.0-cancel",
                         "DMBWindowsWorker-cert-0.3.0-crash"}:
        raise PermissionError("Unapproved DMB private namespace")
    require_identity()
    buffer = ctypes.create_unicode_buffer(32768)
    if dll("shell32").SHGetFolderPathW(None, 0x1C, None, 0, buffer) != 0:
        raise PermissionError("current-user LocalAppData unavailable")
    root = Path(buffer.value) / "Directive" / namespace
    kernel = dll("kernel32")
    kernel.GetFileAttributesW.argtypes = [w.LPCWSTR]
    kernel.GetFileAttributesW.restype = w.DWORD
    for path in [root, *root.parents]:
        attributes = kernel.GetFileAttributesW(str(path))
        if attributes != 0xFFFFFFFF and attributes & 0x400:
            raise PermissionError("reparse/junction worker boundary rejected")
    return root


class WorkerOwnershipError(PermissionError):
    """A live native lock owner exists; never recover its journal."""


@contextmanager
def foreground_lock(root):
    """One local owner. A competing foreground process must never recover its peer."""
    require_identity()
    import msvcrt
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    with (root / "foreground.lock").open("a+b") as stream:
        if not stream.seek(0, os.SEEK_END):
            stream.write(b"1"); stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise WorkerOwnershipError("another foreground bridge owns this worker; no concurrent recovery") from exc
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


class Blob(ctypes.Structure):
    _fields_ = [("size", w.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def dpapi(data, protect=True):
    require_identity()
    crypt, kernel = dll("crypt32"), dll("kernel32")
    value = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(value, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    function = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, w.DWORD, ctypes.POINTER(Blob)]
    function.restype = w.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(output.data)


def local_appdata():
    require_identity()
    buffer = ctypes.create_unicode_buffer(32768)
    if dll("shell32").SHGetFolderPathW(None, 0x1C, None, 0, buffer) != 0:
        raise PermissionError("current-user LocalAppData unavailable")
    return Path(buffer.value)


def resolve_codex():
    require_identity()
    from .windows_codex_locator import discover, architecture
    powershell = system_directory() / "WindowsPowerShell/v1.0/powershell.exe"
    def path_query():
        return subprocess.check_output([str(powershell), "-NoProfile", "-NonInteractive", "-Command",
                                        "(Get-Command codex -ErrorAction Stop).Source"], text=True, timeout=5)
    return discover(local_appdata(), path_query, architecture())


@contextmanager
def pinned_codex_file(executable):
    require_identity()
    from .windows_codex_locator import pinned_image
    with pinned_image(executable) as pinned:
        yield pinned


class BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong), ("flags", w.DWORD),
                ("minimum_working_set", ctypes.c_size_t), ("maximum_working_set", ctypes.c_size_t),
                ("active_process_limit", w.DWORD), ("affinity", ctypes.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]


class IOCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IOCounters), ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t), ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_longlong) for name in ("user_time", "kernel_time", "period_user", "period_kernel")] + [
        (name, w.DWORD) for name in ("page_faults", "total_processes", "active_processes", "terminated_processes")]


class SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", w.DWORD), ("descriptor", ctypes.c_void_p), ("inherit", w.BOOL)]


class StartupInfo(ctypes.Structure):
    _fields_ = [("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR), ("title", w.LPWSTR)] + [
        (name, w.DWORD) for name in ("x", "y", "xsize", "ysize", "xchars", "ychars", "fill", "flags")] + [
        ("show", w.WORD), ("reserved2_size", w.WORD), ("reserved2", ctypes.POINTER(ctypes.c_ubyte)),
        ("stdin", w.HANDLE), ("stdout", w.HANDLE), ("stderr", w.HANDLE)]


class ProcessInfo(ctypes.Structure):
    _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE), ("pid", w.DWORD), ("tid", w.DWORD)]


class WindowsJobProcess:
    """Create suspended, assign this job, then resume. Owned handles survive PID reuse."""
    def __init__(self, executable, arguments, cwd, directory):
        with pinned_codex_file(executable) as (resolved, identity):
            self._launch(resolved, arguments, cwd, directory, identity)

    def _launch(self, executable, arguments, cwd, directory, image_identity):
        require_identity()
        self.kernel = k = dll("kernel32")
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "QueryInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            "CreatePipe": ([ctypes.POINTER(w.HANDLE), ctypes.POINTER(w.HANDLE), ctypes.POINTER(SecurityAttributes), w.DWORD], w.BOOL),
            "SetHandleInformation": ([w.HANDLE, w.DWORD, w.DWORD], w.BOOL),
            "CloseHandle": ([w.HANDLE], w.BOOL), "ResumeThread": ([w.HANDLE], w.DWORD),
            "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL), "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
            "TerminateProcess": ([w.HANDLE, w.UINT], w.BOOL),
            "CreateProcessW": ([w.LPCWSTR, w.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, w.BOOL, w.DWORD, ctypes.c_void_p, w.LPCWSTR, ctypes.POINTER(StartupInfo), ctypes.POINTER(ProcessInfo)], w.BOOL),
            "WriteFile": ([w.HANDLE, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p], w.BOOL),
            "GetExitCodeProcess": ([w.HANDLE, ctypes.POINTER(w.DWORD)], w.BOOL),
        }
        for name, (args, restype) in signatures.items():
            getattr(k, name).argtypes, getattr(k, name).restype = args, restype
        self.job, self.process, self.stdin = None, None, None
        self.output_files = []
        read, write = w.HANDLE(), w.HANDLE()
        info = ProcessInfo()
        try:
            self.job = k.CreateJobObjectW(None, None)
            if not self.job: raise ctypes.WinError(ctypes.get_last_error())
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000 | 0x200 | 0x4 | 0x8  # kill-on-close, job memory/time, active-process cap
            limits.basic.job_time = 10 * 10000000
            limits.basic.active_process_limit = 8
            limits.job_memory = 256 * 1048576
            if not k.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), None, True)
            if not k.CreatePipe(ctypes.byref(read), ctypes.byref(write), ctypes.byref(attributes), 0):
                raise ctypes.WinError(ctypes.get_last_error())
            self.stdin = write
            if not k.SetHandleInformation(write, 1, 0): raise ctypes.WinError(ctypes.get_last_error())
            import msvcrt
            startup = StartupInfo(); startup.cb = ctypes.sizeof(startup); startup.flags = 0x100; startup.stdin = read
            for name in ("stdout", "stderr"):
                file = (Path(directory) / (name + ".log")).open("wb")
                self.output_files.append(file)
                handle = msvcrt.get_osfhandle(file.fileno()); os.set_handle_inheritable(handle, True)
                setattr(startup, name, handle)
            # Retain normal user/auth/proxy/CA context. Drop unrelated provider/trading variables.
            allowed = {"PATH", "SYSTEMROOT", "WINDIR", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "COMSPEC",
                       "CODEX_HOME", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS"}
            env = {name: value for name, value in os.environ.items() if name.upper() in allowed}
            block = ctypes.create_unicode_buffer("\0".join(name + "=" + value for name, value in sorted(env.items(), key=lambda item: item[0].upper())) + "\0\0")
            command = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(executable), *arguments]))
            if not k.CreateProcessW(str(executable), command, None, None, True, 0x4 | 0x400 | 0x08000000,
                                    block, str(cwd), ctypes.byref(startup), ctypes.byref(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.process, self.pid, self.stdin = info.process, info.pid, write
            from .windows_codex_locator import verify_suspended_image
            try:
                verify_suspended_image(self.process, Path(executable), image_identity)
            except BaseException:
                k.TerminateProcess(self.process, 1)
                raise
            if not k.AssignProcessToJobObject(self.job, self.process):
                k.TerminateProcess(self.process, 1)
                raise ctypes.WinError(ctypes.get_last_error())
            if k.ResumeThread(info.thread) == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise
        finally:
            if read.value: k.CloseHandle(read)
            if info.thread: k.CloseHandle(info.thread)

    def send(self, value):
        data = (json.dumps(value, separators=(",", ":")) + "\n").encode()
        buffer = ctypes.create_string_buffer(data); written = w.DWORD()
        if not self.kernel.WriteFile(self.stdin, buffer, len(data), ctypes.byref(written), None) or written.value != len(data):
            raise ctypes.WinError(ctypes.get_last_error())

    def active(self):
        value = Accounting()
        if not self.kernel.QueryInformationJobObject(self.job, 1, ctypes.byref(value), ctypes.sizeof(value), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return value.active_processes

    def terminate(self):
        if self.job and not self.kernel.TerminateJobObject(self.job, 1):
            raise ctypes.WinError(ctypes.get_last_error())
        deadline = time.monotonic() + 3
        while self.active() and time.monotonic() < deadline:
            time.sleep(.02)
        return self.active()

    def close(self):
        if self.job:
            self.kernel.CloseHandle(self.job); self.job = None
        for handle in (self.stdin, self.process):
            if handle: self.kernel.CloseHandle(handle)
        self.stdin = self.process = None
        for file in self.output_files: file.close()
        self.output_files = []
