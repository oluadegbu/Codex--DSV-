import ctypes
import getpass
import os
import subprocess
from pathlib import Path


def require_non_admin(workspace):
    root = Path(workspace).resolve(strict=True)
    if not (root / 'CODEX.md').is_file() or not (root / 'src' / 'dci').is_dir():
        raise PermissionError('dedicated DCI workspace markers missing')
    if os.name == 'nt':
        groups = subprocess.run(['whoami', '/groups', '/fo', 'csv'], capture_output=True, text=True, timeout=5, check=True, shell=False).stdout
        if ctypes.windll.shell32.IsUserAnAdmin() or 'S-1-5-32-544' in groups or getpass.getuser().casefold() != 'directivecodex':
            raise PermissionError('non-admin DirectiveCodex identity required')
    elif os.geteuid() == 0 or 0 in os.getgroups():
        raise PermissionError('non-root identity required')
    return root
