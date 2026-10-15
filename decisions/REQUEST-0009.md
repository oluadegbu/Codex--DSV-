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
