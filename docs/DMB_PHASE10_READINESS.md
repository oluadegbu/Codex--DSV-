> Historical review1 findings below are preserved. The implemented0.3.0 lifecycle supersedes the design-only runtime status; see [current package](../deployment/phase10/lifecycle-v0.3.0/README.md). Activation remains withheld.

# Phase10 targeted readiness — activation withheld

The released0.2.0-review1 package is NOT a continuous unattended service. Its
host computes `min(3600, grant expiry - current time) - 120` seconds for polling,
then drains its current bounded call and exits normally. This is normally about
58minutes of polling for a fresh one-hour grant; it is not an exact3600-second
process kill. The proposed Scheduled Task adds a1h2m hard ceiling. Neither a
normal success exit nor an expired grant invokes RestartOnFailure. Without a
later boot or on-demand start the current definition does not restart after a
successful bounded session. No one-hour timed simulation was substituted for
this direct source and Windows scheduler-semantics finding.

## Targeted durable lifecycle design

Keep the worker sessions bounded; use Windows Task Scheduler as the independent
watchdog rather than adding another persistent service:

1. Boot+1minute with an indefinitely repeating5minute trigger. A clean bounded
   session can be followed by another at the next5minute tick. `IgnoreNew` skips
   overlapping triggers and the native exclusive lock prevents a second worker
   even if invoked outside Task Scheduler. No process is detached on session exit.
2. Disable RestartOnFailure in this revision so retries cannot multiply with the
   periodic trigger. There is one fixed restart cadence, never a tight spawn loop.
3. Before starting any new worker, use the existing lifecycle SQLite authority to
   transactionally record the owner/heartbeat and a persistent crash budget.
   Three unexpected interrupted starts over the deployment lifetime trip a sticky
   BLOCKED circuit. The count survives interpreter exit and OS reboot; it does not
   reset when a new scheduler invocation begins. A successful bounded rotation is
   not a crash. No automatic counter reset, re-pairing or replacement database.
4. Reconcile the existing worker journal before polling. A sealed completion may
   be delivered idempotently; an uncertain started task stops the route, retains
   locks and emits NEEDS_HUMAN. No scheduler retry authorizes re-execution.
5. STOP, policy/identity/pairing failure or absent/expired authorization leaves a
   sticky paused/blocked state. A periodic watchdog may inspect that state at its
   fixed cadence but cannot start a worker or renew authority. Work resumes only
   after exact authenticated reconciliation/new authorization allowed by the
   explicitly approved policy, never because another5minutes elapsed.
6. The one-hour acceptance lease remains enforced. Continuous *authorized* work
   beyond it requires an explicitly approved operational lease/renewal policy and
   authenticated relay supervision; no current grant is silently extended.

The **disabled design candidate** is
[PROPOSED-WATCHDOG-NOT-FOR-REGISTRATION.xml](../deployment/phase10/PROPOSED-WATCHDOG-NOT-FOR-REGISTRATION.xml).
Windows Task Scheduler parsed it in memory:5minute repetition, indefinite pattern,
IgnoreNew, RestartCount0, Password/LeastPrivilege. Both task and trigger are disabled.
It points to an unreleased review2 path. It is NOT an activation definition and
must not be imported. The persistent global crash circuit is a required runtime
revision, not implemented/certified by the old review1 package. No new package is
published while the external/policy gates below remain blocked.

## Supported logon configuration and newly measured prerequisite

Microsoft documents that Password logon requires the password at registration,
and that both Password and S4U task logon require Logon as Batch. S4U explicitly
has no access to network or encrypted files. An interactive-token task depends
on an existing user logon and cannot establish logoff/reboot independence.
Therefore the least-privilege supported candidate remains Password logon under
**existing DirectiveCodex**, LeastPrivilege with a native Medium/non-admin check.
There is no Administrator/SYSTEM/service-account fallback.

If finally approved, Windows accepts the password locally through its supported
registration interface and retains the task credential in protected OS storage.
No password is placed in the ZIP, XML, arguments, JSON, repository or chat. No
credential was requested, read or enrolled during this readiness review.
Task creation must not implicitly grant a missing logon right; verify and stop
if the authorized security boundary does not already permit batch logon.

A read-only native LSA/NetAPI query on the actual host found:

- DirectiveCodex SID ends1000; local groups Users and Remote Desktop Users.
- No SeBatchLogonRight allowance matched the account, observed local groups,
  Everyone, Authenticated Users or Local Account; no matching deny was found.
- This establishes **no allowance observed in current local policy**, not a
  successful batch logon or a claim about uninspected domain/GPO outcomes.

Actual batch-token Medium integrity, loaded user profile, current-user DPAPI and
Codex/HTTPS authentication are still NOT TESTED. Interactive RDP success does not
certify them. Any required right/security-policy change is outside current
approval and was not made. Do not try S4U, stored-password workarounds or elevation.
Official sources and the exact observed facts are retained in
[readiness evidence](evidence/phase10-readiness/READINESS.json).

## Existing relay and genuine Windows preactivation

The approved portfolio/Phase10 evidence still provides no existing remote endpoint,
host identity or authorized connection for a DMB relay. Managed environment162
has no outbound identity/credential/relay/VPN binding. The known registry marks
Temporal INTERFACE_ONLY, not a certified authenticated DMB HTTPS mailbox. An
approved DAT Temporal milestone is not permission to inspect/reuse DAT credentials,
change its namespace/services or repurpose production infrastructure. No endpoint
was invented, public listener opened, infrastructure purchased or runtime deployed.
An existing approved host/endpoint and authorized non-secret evidence/access
reference are necessary before real authenticated remote delivery can be tested.

The selected native executor remains Administrator/RID500 at High12288. Its only
managed terminal, PID8400, is also owned by Administrator. The tool has no supported
run-as/session-selection option. Being able to enumerate an RDP account/session
does not authorize token duplication, impersonation, injected commands or a task
registration to gain that execution context. Consequently no Codex worker was
launched through it. No operator diagnostic or deployment procedure is issued.

Real preactivation remains: actual non-admin task cancellation with interrupt ACK;
owned-worker crash with Job cleanup, durable uncertain quarantine and no duplicate;
independent harmless creator canaries with actual read/write access denied;
restart/reopen with exact artifact/durable completion; and eventual approved batch
logon, RDP-disconnect/logoff/reboot validation. All use fresh side-by-side evidence,
not overwrites/retries of existing successful or failed journals. These remain
BLOCKED, not PASS inferred from native schema checks or historical0.1.3 success.

REQUEST-0009 remains activation WITHHELD. No consolidated operator action will be
issued until the relay, authorization/context and real acceptance gates are ready.
All persistent changes, prior packages, pairing and production systems are unchanged.
