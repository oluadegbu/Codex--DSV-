# Self-contained DMB Windows shadow package

This supersedes the Git/Python/OpenSSL prerequisite in the source-checkout
procedure. The operator downloads **one version-pinned ZIP**, verifies its
published SHA-256, extracts it in a fresh current-user directory and invokes
its official embedded Python executable. Nothing is installed and there is no
system/user PATH, trust-store, account, ACL, firewall, service or scheduled-task
change. The existing authenticated official Codex CLI0.162.1 is the only external
runtime prerequisite.

The package reuses the tested bridge and foreground driver, including identity
and Medium-integrity checks, current-user DPAPI, fixed zero-tool task, HMAC/TLS,
durable dispatch/audit, cancellation, quarantine and restart deduplication. It
bundles CPython3.12.10 AMD64, portable MinGit2.51.0.windows.1 and pinned
cryptography46.0.2/cffi2.0.0/pycparser2.23 wheels. Portable Git preserves actual
scratch/controller Git operations and never clones or accesses production projects.
Only the launched process and its children use its bundled Git path.

The CI builder exports committed application bytes, verifies MinGit against its
official release SHA-256, verifies each wheel against official PyPI metadata,
and checks the official embedded Python executable's Authenticode signature.
Every payload file is indexed by SHA-256 in PACKAGE_MANIFEST.json. The application
checks this index before pairing. The final ZIP is hash-verified, not claimed to
have a DCI Authenticode signature. No private pairing key, TLS key, auth material,
Git credential, runtime journal or model transcript enters the package or Git.

Windows CI executes the **actual embedded runtime**, removing system Git and Python
from PATH, and tests bundled Git, native cryptography, validated loopback TLS/HMAC,
SQLite reopen/audit and rejection of the CI identity before Codex launch. This is
package/dependency certification, not a genuine DirectiveCodex task or OS isolation.
The Linux suite retains all145 existing tests and adds five package-boundary checks.

## Foreground deployment

Published replacement: [dmb-windows-v0.1.2-d3ce1b9cc73e](https://github.com/oluadegbu/Codex--DSV-/releases/tag/dmb-windows-v0.1.2-d3ce1b9cc73e).
The ZIP is58,464,767 bytes; SHA-256
`4ebd023dbfd6c935fccca64bbe6ae3004b1b17052b693c90d9078f9d5f0d640e`.
Source is `d3ce1b9cc73ef646120f06a6056876086632df98`.

Version0.1.1 passed the repaired identity gate but its non-interactive Get-Command
lookup could not resolve the existing installation. Version0.1.2 checks native
current-user LocalAppData/Programs/OpenAI/Codex/bin/codex.exe first, without PATH.
The executable must match OpenAI's raw v0.162.1 release hash/size and pass the exact
version probe. Failed primary verification stops; it never silently chooses another
binary. Hash verification repeats under a no-write/no-delete-sharing file handle
through process creation. Windows8.3 aliases are canonicalized; junction/reparse
redirects are still rejected. No global PATH or installed Codex changes.

Native Windows CI38533236795 tested actual official Codex bytes in the user-local
layout with PATH lookup forbidden, and retained privileged-identity rejection,
TLS/HMAC/Git/SQLite checks.157 tests pass. CI does not execute/authenticate Codex
or substitute for the genuine RDP task. [Exact evidence](evidence/windows-codex-path/CERTIFICATION.json).

The old0.1.0/0.1.1 installations, pairing and journals are preserved. Before fresh
pairing in DMBWindowsWorker-v1-0.1.2, the driver reads only a checkpointed immutable
old controller snapshot and requires the original task to be QUEUED/attempts0,
with no dispatch, execution, lock, authenticated HELLO or worker journal. Missing,
changing, uncheckpointed or started/uncertain evidence blocks rather than being
reset or routed around. No old pairing file is decrypted or overwritten.

Paste this complete block into normal PowerShell in the existing DirectiveCodex
RDP session. It creates one distinct deployment directory, checks the predecessor,
pairs and automatically executes/verifies the genuine fixed shadow task and durable
completion/restart. No separate diagnostics, installs, elevation, services or
production changes. The [same block](DMB_WINDOWS_PACKAGE.ps1) is kept in Git.

```powershell
$ErrorActionPreference = 'Stop'
$DmbIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$DmbPrincipal = New-Object Security.Principal.WindowsPrincipal($DmbIdentity)
if ($DmbIdentity.Name -ine "$env:COMPUTERNAME\DirectiveCodex" -or $DmbPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use normal PowerShell in the existing non-admin DirectiveCodex RDP session.'
}
$DmbUrl = 'https://github.com/oluadegbu/Codex--DSV-/releases/download/dmb-windows-v0.1.2-d3ce1b9cc73e/DMB-Windows-0.1.2-d3ce1b9cc73e-amd64.zip'
$DmbSha = '4ebd023dbfd6c935fccca64bbe6ae3004b1b17052b693c90d9078f9d5f0d640e'
$DmbRoot = Join-Path $env:LOCALAPPDATA 'Directive\DMB-0.1.2-d3ce1b9cc73e'
if (Test-Path $DmbRoot) { throw 'Existing state preserved. Do not overwrite, delete or silently re-pair.' }
for ($DmbPath = [IO.DirectoryInfo]$DmbRoot; $null -ne $DmbPath; $DmbPath = $DmbPath.Parent) {
    if ($DmbPath.Exists -and ($DmbPath.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Junction/reparse deployment boundary rejected.' }
}
New-Item -ItemType Directory -Path $DmbRoot | Out-Null
$DmbZip = Join-Path $DmbRoot 'package.zip'
Invoke-WebRequest -UseBasicParsing -Uri $DmbUrl -OutFile $DmbZip
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $DmbZip).Hash -ine $DmbSha) { throw 'Package SHA-256 mismatch; nothing executed.' }
$DmbPackage = Join-Path $DmbRoot 'package'
Expand-Archive -LiteralPath $DmbZip -DestinationPath $DmbPackage
& (Join-Path $DmbPackage 'runtime\python\python.exe') -I (Join-Path $DmbPackage 'app\tools\run_windows_shadow_bridge.py')
if ($LASTEXITCODE -ne 0) { throw "Stopped safely. Preserve $DmbPackage\app\artifacts\windows-foreground; no blind rerun." }
Get-Content -LiteralPath (Join-Path $DmbPackage 'app\artifacts\windows-foreground\CERTIFICATION.json')
```

Under the existing non-admin DirectiveCodex RDP session the driver automatically:

1. Validates the actual Medium token and payload hashes.
2. Binds exported source to a local Git snapshot and records the upstream source commit.
3. Generates private loopback TLS and one-hour scoped HMAC pairing; protects the worker key with current-user DPAPI.
4. Starts the foreground DMB controller and outbound-only worker on authenticated loopback HTTPS.
5. Dispatches one actual Codex shadow task and verifies its exact JSON artifact, terminal turn, scratch Git state, owned-process termination, audit and one durable completion.
6. Closes/reopens both durable ends and proves that a second poll does not execute again.
7. Prints only sanitized CERTIFICATION.json. Keys, TLS private files and raw logs remain local under ignored application artifacts/current-user state.

The certificate is trusted only by the local client, with no OS certificate-store
change. No externally reachable port, reverse proxy or notification provider is
activated. Missing/expired/drifted pairing or uncertain execution stops and keeps
state and locks; do not remove state or re-pair to force a PASS. Release input or
repository authorization failures are material publication blockers, not permission
to bypass authentication.

Current hashes, actual release/download identity, CI and blockers are recorded
under docs/evidence/windows-package and BUILD_STATE.json after publication.
Windows task certification remains pending until the foreground task produces its
genuine receipt. Remote cloud delivery, Windows cancellation/crash, OS canary read
and write denial, multi-worker isolation and external integrations remain separate
gates. Full DMB certification stays BLOCKED; DAT Temporal integration and all
production systems remain unchanged.
