# REQUEST-0009 — Phase10 exact persistent configuration review

CONTEXT

The operator approved the unattended startup architecture subject to final review,
and explicitly withheld Scheduled Task installation/enablement until final approval.
REQUEST-0008 architecture is accepted, not deployment authorization.

EVIDENCE

- Exact task: deployment/phase10/Directive.DMB.ShadowWorker.Phase10.xml
- Task XML SHA256: `2e9ff8a5dbe85640d357fd6d1397408e849a9f17f22dc83e4a364c30ee42e3e1`
- Exact paths, arguments, principal, trigger, restart and persistent footprint:
  deployment/phase10/DEPLOYMENT_REVIEW.json
- Native Windows Schedule.Service NewTask/XmlText parsed the actual definition;
  no RegisterTaskDefinition, Run, credential prompt or persistent change occurred.
- Native selected execution identity is Administrator/RID500, elevated/High12288.
  The existing DirectiveCodex account resolves to RID1000, but there is no supported
  non-admin worker invocation context in the connected executor. No impersonation,
  elevation, Administrator/SYSTEM launch or batch-logon right change was attempted.
- Existing registry Temporal is INTERFACE_ONLY with no verified host/workspace/repo.
  The only connected device reports no DMB task or DMB/Temporal-named service/process.
  The managed development runtime has no configured durable host identity, relay
  endpoint or VPN. This limited evidence does NOT establish absence elsewhere.
  Temporal gRPC/durable workflows alone do not implement the DMB signed HTTPS relay.

OPTIONS

1. Review the exact definition and version-pinned self-contained package, identify
   the existing approved DMB/Temporal host/relay and its authorized read-only access,
   then complete actual non-admin foreground acceptance and batch context checks.
   Request final install/enable approval only with complete private configuration,
   package hash and real preactivation evidence bound to this package.
2. Retain the certified0.1.3 foreground baseline without unattended activation.

RECOMMENDATION

Option1. This request records the exact proposed changes, but is NOT READY FOR
ACTIVATION until endpoint/pairing and real Windows evidence are complete. An
approval of the design, a delivery acknowledgement or a simulation cannot satisfy
those gates. Use an existing authorized host only; no purchases or public listener.

IMPACT

Only after final explicit approval: create the one side-by-side package directory,
one separate private state directory, and exactly one least-privilege Task Scheduler
entry `\Directive.DMB.ShadowWorker.Phase10` with Windows-managed protected task
credential enrollment for the existing DirectiveCodex account. No password enters
Git, chat, arguments or plaintext files. The process must prove the exact SID,
non-admin Medium token and package/activation grant before network or execution.

Boot trigger delay1m; no interactive-logon dependency. IgnoreNew; worker max1h;
hard Task Scheduler limit1h2m; unexpected failure restart every5m, max3. A policy,
identity, pairing, evidence or approval block exits0 without blind retries.
A fixed local STOP marker drains the current bounded task. Forced stop leaves
uncertain started work quarantined, never retried; owned Codex jobs kill on close.
Rollback disables/unregisters ONLY this task and retains all artifacts/journals.

No account creation, Administrator/SYSTEM execution, elevation, logon-right/ACL/
firewall changes, new service, public listener, production schedule/service changes,
paid provider, notification activation, trading or DAT Temporal changes are included.
If Task Scheduler or batch authentication requires an unavailable permission, stop.
The existing DAT, DPM, DSV, Pulse and Administrator recovery paths remain untouched.

BLOCKING: YES
HARD_GATE: YES

Status: FINAL REVIEW PREPARED; REGISTRATION/ENABLEMENT WITHHELD; REMOTE AND REAL
PREACTIVATION GATES BLOCKED. Package release/hash recorded in Phase10 evidence
when the review-only native Windows build completes.

Published REVIEW-ONLY package: https://github.com/oluadegbu/Codex--DSV-/releases/tag/dmb-windows-v0.2.0-review1-2f446d25d1f2
ZIP SHA256: `bcb5ee880163061d54441942c751d4ff850e96821dbc31ce87decd9aceff835a` (58,496,268 bytes).
Source: `2f446d25d1f20df16e1c01769bfc36a5391e1092`. Native package and171 tests PASS.
Task definition SHA256 remains `2e9ff8a5dbe85640d357fd6d1397408e849a9f17f22dc83e4a364c30ee42e3e1`.
Exact scope, hashes and blocked gates: docs/evidence/phase10-review/CERTIFICATION.json.
No activation grant, pairing credentials or remote endpoint is included.

Readiness addendum: docs/DMB_PHASE10_READINESS.md confirms review1 ends its bounded
acceptance session and does not restart on normal exit. A disabled five-minute
watchdog revision is designed/native-schema-parsed only, with a required durable
three-crash circuit not present in review1. No new release/activation is implied.
Actual local policy shows no observed batch-logon allowance for DirectiveCodex's
account/groups; policy/credential changes remain unauthorized. No verified existing
relay endpoint or supported non-admin invocation context is available. Do not
register/import either definition. Operator procedure and activation remain withheld
until those gates and real package-bound preactivation evidence are ready.


## Blocker-closure implementation — final activation still WITHHELD

The 0.3.0 implementation supersedes the historical review1 lifecycle description
above for final review. Exact new task:
`deployment/phase10/lifecycle-v0.3.0/Directive.DMB.ShadowWorker.Phase10.xml`,
SHA256 `2dd50b9b5493513cb1c4b2510d732a75320949980a126dc5143cc58f2aed5b14`.
Boot +1minute, indefinite five-minute repetition, IgnoreNew, no RestartOnFailure.
Native exclusive ownership plus a persistent three-crash circuit now exist;
normal session rotation preserves the crash count. STOP/policy/uncertainty are
sticky, no automatic renewal or quarantine clear. New package/private namespaces
preserve every old installation and journal. A version-2 grant up to8hours is a
PROPOSED explicit acceptance authorization, never an extension of old1hour grants.

One consolidated approval/access request remains in
`deployment/phase10/lifecycle-v0.3.0/README.md`: existing approved authenticated
relay host/access reference and private pairing; native DirectiveCodex foreground
certification with independent harmless canaries; minimum account-specific batch
right only if missing; local Windows-protected password enrollment; final exact
package/XML/evidence-bound registration and initial start. No password in chat.
Exact inert scripts perform only this task's create/start or disable/drain/remove,
with no overwrite, security policy/ACL/firewall change or other schedule access.
Actual batch logon is tested before registration to prevent implicit rights grant.
The known selected remote executor remains Administrator/High; no worker is
launched there. >1hour, actual cancellation/crash/denial and remote/batch/RDP
independence must each retain BLOCKED/NOT TESTED until native receipts exist.

BLOCKING: YES
HARD_GATE: YES
Status: REQUEST-0009 WITHHELD. Code/package publication is authorized development;
this request, a package release and passing CI do not authorize task activation.


### Exact boot-trigger installation prerequisite

Microsoft BootTrigger documentation states: "Only a member of the Administrators
group can create a task with a boot trigger."
https://learn.microsoft.com/en-us/windows/win32/taskschd/boottrigger

The final requested change therefore includes **one-time task registration by the
existing Administrator/security owner**, after explicit final authorization.
DirectiveCodex must never gain Administrator membership or be elevated. The worker
always runs Password/LeastPrivilege under its existing SID/Medium token. No
Administrator/SYSTEM worker execution or impersonation is authorized.

The corrected inert registration script accepts only the exact human-approved
SHA256/path of an immutable public PREDEPLOY receipt generated by actual
DirectiveCodex preflight. Preflight validates DPAPI/package/real acceptance and
performs a signed TLS/HMAC remote HELLO, without POLL, task execution or recovery
of pending dispatch. Installation verifies reviewed hashes/expiry and already
permitted native batch logon before creating the one task. Missing batch right
still requires separate explicit approval for that minimum account-specific
policy change; the script never grants it. Local protected password enrollment,
exact task create/start and retained-evidence rollback remain within this single
consolidated final request. No credential is requested in chat.

Current actual evidence: harmless independent canaries created/hash-verified;
exact task XML parsed by native VPS Schedule.Service without registration;
first corrected CI package passes native checks. No new-package DirectiveCodex
cancellation/crash/access-denial/elapsed-hour receipt, authenticated approved
remote endpoint, batch-context receipt or RDP-independent worker PASS exists yet.
Final registration and activation are still WITHHELD.
