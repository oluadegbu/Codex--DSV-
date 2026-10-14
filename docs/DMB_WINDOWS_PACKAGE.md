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

The final supervisor report supplies the exact development-prerelease ZIP URL,
SHA-256 and a complete PowerShell block. No placeholders, interactive account
setup, pip, Git/Python installation or downloaded-script policy bypass is required.
The package source commit and release version are immutable selections in that
procedure; it never downloads `latest` or overwrites an existing workspace.

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
