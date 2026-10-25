# Preflight10.5A — separate test addon, never a DDB worker release

REVIEW ONLY. No deployment/test authority is granted. Verified worker ZIP remains
unchanged. This addon adds no remote endpoint, Codex launch, scheduler or credential
provider. Exact addon hashes/file inventory are in the published ADDON_RELEASE.json
and ADDON_MANIFEST.json. Each native command requires an approved public parameter
file and explicit prior authorization through the authenticated operator channel.
A locally written `approved:true` or its hash is not independent human authentication.

## Prerequisites and deployment procedure — only after scope-specific approval

1. Use the existing WIN-HQAAFGGU1AM\DirectiveCodex RDP session, SID
   S-1-5-21-3675741470-1525898003-3877381073-1000. Verify token by native API:
   non-admin membership (including deny-only), Medium S-1-16-8192, no impersonation.
   Do not use Administrator's remote executor, RunAs or injected credentials.
2. Obtain the exact existing Windows ZIP from artifact12498015215/run39944383870
   through approved GitHub access. No credential is printed/exported or copied.
   Verify ZIP SHA256
   06a5eded7bcfc3ad2cbecf9140e47b88f6a65848c6929847f1de7dd8281791e0 and58475044 bytes;
   manifest SHA256
   8aa986c9a02f05fe1cd30fb18b957aa4610dd180e3e2866f23241197c33e5b0f.
   Source-only archives and mutable latest links are not substitutes.
3. Exact fresh root:
   C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011.
   If any part already exists/reparses unexpectedly, STOP and preserve it; do not
   overwrite, delete or select an unreviewed alternative path. Do not change ACLs.
   Inspect parent owner/DACL metadata only; existing account write authority must
   suffice. No batch-logon right, global PATH change, Git/Python install or service.
4. Inspect both ZIP entry names before extraction: reject absolute names, `..`,
   backslashes, drive/colon names, links and paths escaping the chosen destination.
   Worker ZIP entries must be app/,runtime/ or DDB_PACKAGE_MANIFEST.json. Hashes
   must match the immutable artifact. Extract worker ZIP to root\package only.
   Verify embedded Python Authenticode and every manifest member/digest; reject
   unlisted executable/import files. Per-file hashes are in the full ZIP manifest.
5. Verify addon ZIP SHA256 against published ADDON_RELEASE.json. Extract it only
   to root\preflight-10.5A (fresh), verify ADDON_MANIFEST.json membership/hashes.
   Create empty root\state and root\artifacts only. Do not enroll signers/tokens,
   initialize a worker journal, prepare production code or run Codex. No global
   configuration is written. Record target identity, manifest hashes and file list.
6. Before native tests, the owner supplies a public, scope-specific approval
   record at root\state\preflight-approval.json. Its exact hash must be approved
   externally. Schema below is a proposal, not a grant; timestamps/probe hash must
   be actual reviewed values. No automatic renewal. Expiry at most30 minutes
   from verified approved start. Each named case executes once, at most9 seconds
   of process activity/cleanup; all native cases fit a120-second test budget.
   Do not set DMB_APPROVED_CANARY_TEST or run older tests implicitly.

```json
{"version":1,"approved":false,"user_sid":"S-1-5-21-3675741470-1525898003-3877381073-1000","starts":0,"expires":0,"cases":[],"probe_sha256":"REVIEWED_PROBE_DIGEST","package_sha256":"06a5eded7bcfc3ad2cbecf9140e47b88f6a65848c6929847f1de7dd8281791e0","canary_manifest_sha256":"INDEPENDENT_APPROVED_CANARY_MANIFEST_DIGEST"}
```

## Independent commands — NOT authorized for execution now

Interpreter below means exactly root\package\runtime\python\python.exe.
Run with `-I -B` and absolute addon script paths. No system Python/Git is needed.

```text
<interpreter> -I -B <addon>\probe.py identity --approval-file <root>\state\preflight-approval.json --approval-sha256 <actual-approved-hash>
<interpreter> -I -B <addon>\probe.py filesystem --approval-file <root>\state\preflight-approval.json --approval-sha256 <actual-approved-hash>
<interpreter> -I -B <addon>\probe.py containment --approval-file <root>\state\preflight-approval.json --approval-sha256 <actual-approved-hash>
<interpreter> -I -B <addon>\probe.py cancel --approval-file <root>\state\preflight-approval.json --approval-sha256 <actual-approved-hash>
<interpreter> -I -B <addon>\probe.py timeout --approval-file <root>\state\preflight-approval.json --approval-sha256 <actual-approved-hash>
<interpreter> -I -B <addon>\probe.py cpu --approval-file <root>\state\preflight-approval.json --approval-sha256 <actual-approved-hash>
<interpreter> -I -B <addon>\probe.py crash --approval-file <root>\state\preflight-approval.json --approval-sha256 <actual-approved-hash>
<interpreter> -I -B <addon>\contracts.py signed-receipts
<interpreter> -I -B <addon>\contracts.py recovery
<interpreter> -I -B <addon>\contracts.py policy
```

Probe allows only this interpreter, fixed inlined Python fixtures and the reviewed
host/SID. No command string, executable or workspace can be supplied by a document.
Native cases create exclusive artifacts/preflight-10.5A/<case>/INTENT.json before
the test and atomically publish RESULT.json. An existing directory prevents retries;
missing RESULT after a crash is ambiguous/blocked, never successful or permission
to reset. No raw credential or production contents are read. These local parameter
checks are not an unattended authorization gateway or authenticated HEG approval.

## Evidence and limits

- identity: real token and fixed account; no child process or authentication load.
- filesystem: own harmless read/write positive control; exact existing read/write
  canaries at C:\Users\Administrator\AppData\Local\Directive\DMB-Isolation-Canary-v1\fixtures\v1.
  No denied bytes are read/written; OPEN_EXISTING only. Independently reviewed
  existence/creator and manifest digest required. Only WinError5 passes. Missing
  fixture is BLOCKED; successful unauthorized open is FAIL. No ACL/account creation.
- containment: suspended bundled-Python fixture assigned to an owned Win32 Job
  before resume, image file identity pinned; observe parent+descendant then zero
  active processes after job termination. No Codex or trading executable.
- cancel: cooperative STOP acknowledgement by the fixed Python loop and clean exit.
  This is NOT Codex turn/interrupt acknowledgement.
- timeout: fixed sleeping Python fixture reaches3-second deadline then job drains.
- cpu: configured2 CPU seconds,64MiB memory and2-process cap are read back; fixed
  busy loop stops within6-second wall bound. Memory pressure and process-cap overflow
  are NOT stress-tested. These lower fixture limits do not change worker risk limits.
- crash: fixture exits73, owned job drained and receipt preserved. This is child
  crash evidence, NOT owner-process crash/kill-on-close recovery certification.
- contracts: existing ephemeral memory-transport/SQLite fixtures prove signature,
  duplicate, recovered SEALED and blocked INTENT contracts. They do not publish
  genuine GitHub receipts or enroll real signers.

All native cases are UNRUN/NOT TESTED in this phase. They must be observed on the
approved non-admin Windows host; syntax/offline tests do not certify native APIs.
Do not claim universal OS isolation or production inability from canary checks.
Actual worker owner-crash recovery, native Codex cancellation and genuine signed
DDB delivery remain prohibited/unrun and require a later execution grant.

## Rollback/revocation

No installation exists from this preparation. For later approved tests, terminate
only the fixture-owned Job; handles close with kill-on-close. Preserve partial
new root, INTENT/RESULT and old installs/journals/pairing. Do not delete or retry
an ambiguous case. Scope-specific approval expires; removing or changing it blocks
new cases. Preserve the public approval audit; no credential revocation is needed
for these credential-free fixtures. Trusted branch/key enrollment needs separate
owner revocation plans and must not delete history. Production services/schedules,
security policy and unattended operation remain untouched.
