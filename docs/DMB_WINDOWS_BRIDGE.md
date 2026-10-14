# DMB Windows worker bridge — foreground pairing

For a VPS without Git/Python, use the [self-contained package](DMB_WINDOWS_PACKAGE.md).
The source-checkout procedure below is retained for already provisioned development environments.

This milestone adds an authenticated outbound-only worker using the existing
PortfolioPlanner, durable BHB store/audit, scope fences, locks and resource budgets.
The only enabled operation is `windows_codex_ping`, a compiled zero-tool prompt
returning `{"mode":"SHADOW","answer":"DCI_SHADOW_OK"}`. Messages cannot provide
shell commands, prompts, credentials, executables or filesystem paths.

## Delivered and certified scope

HMAC-SHA256 authenticates both directions, worker/key/host/source/scratch bindings,
monotonic sequence and message identity. HTTPS validates certificate and hostname;
redirects are forbidden. Authentication errors stop immediately. Transient delivery
has three bounded retries with the same durable request identity. Database actions,
reply cache and audit commit together before replying. A lost acknowledgement can
be replayed without dispatching or completing twice.

The worker stores its scoped pairing key with **current-user DPAPI**, holds one
nonblocking foreground-owner lock, and refuses Administrator membership or any
integrity level other than Medium. It launches the existing official native Codex
CLI 0.162.1 through supported `app-server --listen stdio://`. The fixed lifecycle
uses initialize, thread/start, turn/start, outputSchema and turn/interrupt. It
checks the effective read-only/no-network/never-approve policy, rejects tool/approval
requests, and does not change authentication, managed requirements or user accounts.
An owned Job Object is assigned while the process is suspended, with 256 MiB,
10 CPU seconds, eight child processes and kill-on-close; wall time is 20 seconds.
Job assignment failure aborts before resume. These Windows primitives remain
NOT TESTED here until this procedure actually runs on Windows.

Success requires the exact artifact, a genuine completed turn/thread, original
scratch Git HEAD and clean status, and zero active processes in the owned Job.
Cancellation needs the requested route, actual interrupt acknowledgement and an
interrupted terminal turn. A started task without durable completion is uncertain:
restart preserves its locks and moves it to NEEDS_HUMAN rather than executing again.
Neither notification nor signed worker claims constitute human approval.

18 portable contract tests pass locally; the 19th test uses actual loopback TLS
with a **fixture executor**, not genuine Codex. CI runs all 19 alongside the
preserved 126 tests. Historical certificates stay immutable. See
[certification](evidence/windows-bridge/CERTIFICATION.json) for current CI and scope.

## One copy-paste procedure, existing DirectiveCodex RDP session

Use normal **non-elevated PowerShell** inside the existing `DirectiveCodex` session.
Existing Python 3.11+, Git for Windows (including bundled OpenSSL) and authenticated
Codex CLI 0.162.1 are prerequisites. This procedure installs nothing. If a
prerequisite is missing, it stops and leaves evidence; it must not elevate or install.

The foreground driver creates a new DCI checkout and controller reservation,
private one-hour pairing key, locally generated one-day TLS certificate, and
current-user DPAPI pairing. The worker makes outbound HTTPS requests to its own
foreground loopback DMB controller; no public/VPS port, firewall change, OS trust
store change, external endpoint, credential transfer or persistent service is
needed. This is **local Windows bridge certification**, not remote cloud delivery.

```powershell
$ErrorActionPreference = 'Stop'
$DmbUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$DmbPrincipal = New-Object Security.Principal.WindowsPrincipal($DmbUser)
if ($DmbUser.Name -ine "$env:COMPUTERNAME\DirectiveCodex" -or $DmbPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use the existing non-admin DirectiveCodex RDP session. Do not Run as Administrator.'
}
$DmbPr = Invoke-RestMethod 'https://api.github.com/repos/oluadegbu/Codex--DSV-/pulls/1'
if (!$DmbPr.draft -or $DmbPr.merged -or $DmbPr.head.repo.full_name -ne 'oluadegbu/Codex--DSV-') { throw 'Expected open draft PR #1.' }
$DmbCommit = $DmbPr.head.sha
$DmbCheckout = Join-Path $env:LOCALAPPDATA 'Directive\DMBWindowsBridgeReview'
if (Test-Path $DmbCheckout) { throw 'Existing checkout retained. Use its original foreground command; do not overwrite it.' }
& git clone --single-branch --branch $DmbPr.head.ref 'https://github.com/oluadegbu/Codex--DSV-.git' $DmbCheckout
if ($LASTEXITCODE -ne 0) { throw 'Git clone failed; no authentication changes attempted.' }
& git -C $DmbCheckout checkout --detach $DmbCommit
if ($LASTEXITCODE -ne 0) { throw 'Reviewed commit checkout failed.' }
$DmbPython = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } elseif (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { throw 'Existing Python 3.11+ required; do not install automatically.' }
$DmbScript = Join-Path $DmbCheckout 'tools\run_windows_shadow_bridge.py'
if ($DmbPython -eq 'py') { & py -3 $DmbScript } else { & python $DmbScript }
if ($LASTEXITCODE -ne 0) { throw "Stopped safely. Preserve private evidence under $DmbCheckout\artifacts\windows-foreground. No blind rerun." }
Get-Content (Join-Path $DmbCheckout 'artifacts\windows-foreground\CERTIFICATION.json')
```

No further task command is needed: after pairing, the driver automatically submits
`windows-shadow-001`, runs one **actual Windows Codex** turn, verifies its fixed
artifact and one durable completion, stops/reopens the controller and bridge,
then proves the second poll causes no new execution. The sanitized JSON printed
at the end is the result to return to the supervisor. It contains process IDs,
actual identity, turn IDs, source commit, hashes, scope and restart evidence;
it contains no pairing key, TLS key, auth token or raw transcript.

The driver does not run synthetic Codex substitutes. On failure it retains private
logs, databases, pairing and uncertain locks; do not delete state, re-pair, reset
leases or edit the task to force a PASS. A completed session can safely rerun its
original `python tools/run_windows_shadow_bridge.py` command while its pairing is
valid; the same task identity remains completed, not executable again. Pairing
expiry/code drift requires reviewed reconciliation, not silent key replacement.

## Other controller deployments

`python -m dci.master.windows_bridge_cli --help` exposes prepare, pair, run,
submit, report, cancel and a bounded loopback TLS serve command. A separate cloud
controller requires an already approved reachable HTTPS route and secure bootstrap
transfer. No such remote route or non-admin remote executor is configured here.
Do not activate a public listener, reverse proxy, VPN, notification provider,
service, scheduled task, account or ACL/firewall modification through this milestone.

Read-only Codex sandboxing and Job Objects do **not** prove filesystem read denial
or separation from other projects. No canary denial, genuine Windows cancellation,
injected Windows crash, multi-worker separation, authenticated remote Brain delivery
or WhatsApp/email integration is certified by portable fixtures or the foreground
restart check. Full DMB certification remains BLOCKED. DAT Temporal integration
remains a separate preserved milestone; production systems are untouched.

Supported references: [Codex app-server](https://learn.chatgpt.com/docs/app-server),
[Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).
