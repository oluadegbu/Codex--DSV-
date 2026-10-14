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
The Linux suite retains all existing regression checks; the current total is158 tests.

## Foreground deployment

Published replacement: [dmb-windows-v0.1.3-8d78f83963db](https://github.com/oluadegbu/Codex--DSV-/releases/tag/dmb-windows-v0.1.3-8d78f83963db).
The ZIP is 58,471,674 bytes; SHA-256 `3f469da9e5a326e66fd6e8dc43ded9cb42381f6c83a0b8c2ba3abc2201d66457`.
Source is `8d78f83963dbd2afb1eb06ffc5481e6d08934a26`.

The v0.1.2 rejection was the official installer junction
`Programs/OpenAI/Codex/bin` -> `.codex/packages/standalone/current/bin`.
The actual VPS native handle resolved this to the exact pinned
`releases/0.162.1-x86_64-pc-windows-msvc/bin/codex.exe`; its SHA-256 matches
OpenAI's raw release. Version0.1.3 accepts only these two exact mount-point
targets, validates the final path and volume/file identity with native Windows
APIs, and rejects other reparse components or destinations even with matching
binary bytes. It executes the resolved release path rather than either alias.
The final file and every ancestor stay pinned against write/delete redirection
through suspended process creation; the process image path/file identity must
match before resume. Hash, exact CLI version, identity and sandbox checks remain.
No global PATH, installed Codex, ACL, token, service or production changes.

Native Windows CI38645136491 validates actual official Codex bytes through the
real junction layout, rejects an untrusted target with identical official bytes,
and proves writes/directory renames fail while pinned. All158 tests pass.
The earlier CI failure38642171755 caught Windows8.3 name normalization and
published nothing; both expected/actual names now come from native handles,
with file-ID verification unchanged. CI does not execute/authenticate Codex
under its privileged account. [Exact evidence](evidence/windows-junction-repair/).

The old0.1.0/0.1.1/0.1.2 installations, pairing and journals are retained.
Before fresh pairing in DMBWindowsWorker-v1-0.1.3, the driver reads checkpointed
immutable controller snapshots for BOTH failed versions. Each must still be
QUEUED/attempts0, with no lease, dispatch, execution, lock, authenticated HELLO
or worker journal. Missing, changing, WAL-bearing or uncertain evidence blocks;
no old pairing is decrypted, state reset, or uncertainty routed around.
Actual read-only VPS validation already passed for both predecessors; the
foreground command checks again immediately before pairing.

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
$DmbUrl = 'https://github.com/oluadegbu/Codex--DSV-/releases/download/dmb-windows-v0.1.3-8d78f83963db/DMB-Windows-0.1.3-8d78f83963db-amd64.zip'
$DmbSha = '3f469da9e5a326e66fd6e8dc43ded9cb42381f6c83a0b8c2ba3abc2201d66457'
$DmbRoot = Join-Path $env:LOCALAPPDATA 'Directive\DMB-0.1.3-8d78f83963db'
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
under docs/evidence/windows-junction-repair and BUILD_STATE.json.
Windows task certification remains pending until the foreground task produces its
genuine receipt. Remote cloud delivery, Windows cancellation/crash, OS canary read
and write denial, multi-worker isolation and external integrations remain separate
gates. Full DMB certification stays BLOCKED; DAT Temporal integration and all
production systems remain unchanged.
