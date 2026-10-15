# Bounded lifecycle package 0.3.0 — REQUEST-0009 remains WITHHELD

No installation, task import, activation or logon-right change has been performed.
Old 0.1.x installations, 0.2.0-review1 package, pairing and journals remain intact.
This directory supersedes the old review1 task for final review; it does not amend
that historical definition or its source-bound receipts.

The exact prospective persistent task is `\Directive.DMB.ShadowWorker.Phase10`:

| Setting | Exact value |
|---|---|
| Identity | WIN-HQAAFGGU1AM\DirectiveCodex; SID S-1-5-21-3675741470-1525898003-3877381073-1000 |
| Logon / privileges | Password / LeastPrivilege; native non-admin Medium token required |
| Executable | C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.3.0\package\runtime\python\python.exe |
| Arguments | -I "C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.3.0\package\app\tools\run_windows_lifecycle_host.py" --seconds 3600 |
| Working directory | C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.3.0\package\app |
| Trigger | Boot + 1 minute, indefinite 5-minute repetition; initial explicit start only after approval |
| Overlap / retry | IgnoreNew + held native exclusive lock; no RestartOnFailure |
| Session / hard ceiling | Up to 3600 seconds minus 120-second grant drain margin; 1h2m task hard limit |
| Authorization | New version-2 exact-package/task/identity/endpoint/evidence-bound grant, maximum 8 hours; old version-1 grants cannot extend |
| Recovery | Persistent global 3-crash circuit, at least 300 seconds after each observed crash; normal rotation keeps crash count |
| Shutdown | Fixed private STOP file drains current <=20s task, sticky PAUSED; no automatic clear |
| Uncertainty | Reconcile only; no POLL/executor after UNCERTAIN; controller locks/reservations retained |

At each scheduler tick, active owners are skipped by Scheduler and the native
lock. A previous committed ACTIVE whose lock is now free counts as a crash. The
first observation starts its five-minute cooldown. Third crash, source/binding
drift, clock regression, uncertain execution or policy block stops new dispatch.
A durable initialization marker makes missing/mismatched lifecycle state block
instead of creating a fresh crash budget. The grant expiry/drain margin is
rechecked before every dispatch, including forward wall-clock jumps.
No automatic database replacement, circuit reset, pairing renewal or authority
extension exists. An expired grant cannot be turned into an unlimited worker by
the periodic trigger. Longer operation requires a separately approved renewal
policy; the proposed eight-hour acceptance lease is an explicit approval item.
Cancellation retains the existing signed controller -> heartbeat -> actual
Codex turn/interrupt -> acknowledged interrupted turn -> zero-owned-process path.
STOP is a drain request, not a claim of a remotely acknowledged cancellation.

## One consolidated native preactivation procedure

After the final release ZIP and SHA256 are recorded in the release evidence,
download that exact version into a **new** `DMB-OPS-0.3.0` directory, verify the
ZIP before extraction and every manifest file, then run this single foreground
certification entry in the existing DirectiveCodex Medium session:

```powershell
$ErrorActionPreference='Stop'
$pkg='C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.3.0\package'
& "$pkg\runtime\python\python.exe" -I "$pkg\app\tools\certify_windows_lifecycle.py" --full-hour
if ($LASTEXITCODE -ne 0) { throw 'Certification blocked: preserve evidence; do not retry or replace state' }
```

This is one actual elapsed-hour run: genuine completion, bounded normal rotation,
at least five minutes before another owner, a second genuine task after >3600s,
actual controller cancellation, owned bridge crash with observed Codex exit,
recovery-only quarantine and independent canary denial. No simulated turn can
pass. It creates three fixed fresh certification namespaces with DPAPI pairing;
any existing scenario state blocks rerun. Logs/keys remain private in ignored
artifacts. Package-bound sanitized `CERTIFICATION.json` and, only if all real
foreground gates pass, `WINDOWS_ACCEPTANCE.json` are produced. No task is installed.
No RDP-disconnect, batch-token or external remote-delivery PASS is inferred.
The bundled CANARY_CREATOR.json records actual harmless files independently
created and hash-verified in the existing Administrator account's own profile.
No ACL was changed and no worker was launched as Administrator. The driver uses
only this exact package-bound public plan and tests denial as DirectiveCodex
before any Codex launch. A missing/allowed canary blocks without blind retry.

## Final consolidated authorization required

1. Supply the existing approved relay HTTPS hostname and authorized deployment/
   access reference. Validate its TLS and the existing end-to-end signed DMB
   `/v1/dmb/windows`, `/v1/dmb/operations` and outbound relay contracts, durable
   replies/ACKs and independent host recovery before pairing. Temporal's workflow
   contracts alone do not establish these endpoints. No relay is provisioned here.
   No DAT/DPM credentials may be reused. Keys must be distinct, bounded and
   transferred through an approved private channel, sealed with current-user DPAPI.
2. Provide the existing DirectiveCodex Medium foreground execution context for
   the one certification run above (operator action if no supported remote
   non-admin route exists). Canary creation and creator-side verification are
   already completed without ACL changes; denial remains to be measured. The
   currently exposed remote executor is Administrator/High, so cannot run Codex.
3. Approve only the missing `SeBatchLogonRight` for existing DirectiveCodex if
   required; no deny-right removal, Administrator/SYSTEM, S4U substitution or
   privilege inheritance. Actual local read-only evidence currently observes no
   allowance. The registration script first tests native LOGON32_LOGON_BATCH using
   locally entered credentials; failure stops **before** task registration so it
   cannot implicitly grant a logon right.
4. After native gates and remote verification, explicitly approve the exact
   new package hash, task XML hash, 8-hour version-2 activation lease and one task
   installation/initial start by the existing Administrator/security owner.
   No Administrator membership/elevation is granted to DirectiveCodex. Enroll the existing account password **locally**
   using Windows-supported Password logon/protected task storage; never send it
   to chat or store it in XML, arguments, configuration or logs. The transient
   registration API password exists in process memory only, never on disk.

Microsoft explicitly limits boot-trigger task creation to an Administrator:
https://learn.microsoft.com/en-us/windows/win32/taskschd/boottrigger .
This is an installation permission, not permission to elevate DirectiveCodex.
After real gates and final configuration exist, run `run_windows_lifecycle_host.py
--preflight` under DirectiveCodex. It verifies the protected grant/package/native
acceptance, performs one TLS/HMAC remote HELLO without POLL/task execution, then
writes an immutable public `PREDEPLOY-<activation-ciphertext-sha256>.json` receipt.
The final human approval must name that receipt's SHA256 and exact persistent
changes. No pairing secret, DPAPI plaintext or password is in the receipt.

Only after that final approval, the existing security owner uses its existing
Administrator session for `REGISTER-AFTER-APPROVAL.ps1 -ApprovedPreflightPath
<exact-receipt-path> -ApprovedPreflightSHA256 <human-approved-digest>`. No caller
is elevated by the script; the worker is never launched directly as Administrator.
The installer verifies the approved receipt, package/file hashes, exact XML,
expiry and private configuration digests, then checks existing batch logon before
creating/starting only the pinned LeastPrivilege task. It refuses any existing
task and does not alter policy, ACLs or other schedules. Final activation.dpapi must already
bind reviewed source, manifest, task, pairing, native canaries and acceptance.
Registration/initial start are not authorized by this document or example values.
Then verify actual batch Medium identity, current-user DPAPI/Codex/network auth,
>1h operation and signed remote reporting across approved RDP disconnect/restart.
Failure retains the blocked task/journals, never falls back to elevated execution.

Rollback uses the companion script: verify exact task action, create sticky STOP,
disable this task only, wait 45s for drain, then unregister only after it stops.
If drain is unverified, stop and retain the disabled task for exact-task emergency
Stop review. Every installation, journal, DPAPI pairing/grant and audit remains.
No file deletion, circuit reset, security-policy undo or other production change
is bundled into rollback. Removing a separately authorized batch right is its own
reviewed security action; it is not silently performed by this package.
