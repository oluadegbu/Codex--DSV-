# Phase10 final configuration review — not activated

Review package: [dmb-windows-v0.2.0-review1-2f446d25d1f2](https://github.com/oluadegbu/Codex--DSV-/releases/tag/dmb-windows-v0.2.0-review1-2f446d25d1f2). ZIP SHA256
`bcb5ee880163061d54441942c751d4ff850e96821dbc31ce87decd9aceff835a`; 58,496,268 bytes.
Existing v0.1.x installations, successful/failed journals and pairing remain intact.
Source is `2f446d25d1f20df16e1c01769bfc36a5391e1092`;171 CI tests and native package checks pass.

The complete prospective [Scheduled Task XML](../deployment/phase10/Directive.DMB.ShadowWorker.Phase10.xml)
was parsed by the real Windows Task Scheduler in memory. No registration or Run call
was made. Task XML SHA256: `2e9ff8a5dbe85640d357fd6d1397408e849a9f17f22dc83e4a364c30ee42e3e1`.

| Field | Exact proposed value |
| --- | --- |
| Task | `\Directive.DMB.ShadowWorker.Phase10` |
| Identity | `WIN-HQAAFGGU1AM\DirectiveCodex` |
| SID | `S-1-5-21-3675741470-1525898003-3877381073-1000` |
| Logon | Password; run without interactive/RDP logon, Windows protected task credential storage |
| Privilege | LeastPrivilege; native non-admin Medium check at every start; never Administrator/SYSTEM |
| Executable | `C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.2.0-review1\package\runtime\python\python.exe` |
| Arguments | `-I "C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.2.0-review1\package\app\tools\run_windows_operations_host.py" --seconds 3600` |
| Working directory | `C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.2.0-review1\package\app` |
| Trigger | OS boot, delay1minute; no repetition/daily/logon trigger |
| Overlap | IgnoreNew plus exclusive worker lock |
| Restart | Unexpected nonzero exit only; every5minutes, max3. Policy blocks exit0/NEEDS_HUMAN |
| Limits | Approval lease<=1h; polling reserves final120s for drain; Task Scheduler hard limit1h2m; priority7 |
| Shutdown | Fixed private STOP marker; drain current bounded task. Forced termination kills owned Codex jobs; uncertain work quarantined |

After FINAL explicit approval, the exact persistent footprint would be one
side-by-side package directory, one separate private state directory, exactly the
one task above, and its Windows-managed protected account credential enrollment.
No plaintext credentials, new account, Administrator/SYSTEM process, logon-right
change, ACL/firewall edit, service, public listener, paid infrastructure or change
to DAT/DPM/DSV/Pulse/trading schedules is included. Missing batch-logon permission
or incompatible DPAPI/provider authentication blocks deployment; never elevate.

Rollback disables/unregisters only this task through supported Windows interfaces,
then preserves package, STOP, DPAPI pairing/activation, journals and audit evidence.
See [shutdown/rollback](../deployment/phase10/STOP_AND_ROLLBACK.md).

The package contains the embedded Python/portable Git dependencies, fixed task
entry, source, XML, inactive config example and rollback review. It has no installer,
activation grant, credentials or endpoint. The entry requires a final current-user
DPAPI grant binding host/SID, source/manifest/task/pairing and real acceptance
hashes. Historical0.1.3 proof cannot certify the changed0.2.0 source. All new state
is separate; no automatic re-pairing, migration or reset of old journals.

## Existing DMB/Temporal relay assessment

The authorized portfolio registry describes Temporal as INTERFACE_ONLY with no
verified host/repository. Only one device is connected; scoped read-only metadata
found no DMB task or DMB/Temporal-named service/process. The managed dev environment
has no durable host identity, endpoint or VPN configuration. These limited checks
do not establish absence elsewhere. Existing relay capability is UNKNOWN, not PASS.
Temporal's durable workflow/gRPC interface alone is not the DMB authenticated HTTPS
mailbox. No existing DAT Temporal namespace/credentials/service was inspected or
reused and its separate milestone remains preserved.

Minimum missing information: the existing approved DMB/Temporal host/relay endpoint
and authorized read-only evidence location or access identity. No password/token
should be sent in chat; do not purchase infrastructure or open listeners.

## Real preactivation gates

The connected executor is Administrator/RID500, High12288. The existing
DirectiveCodex resolves to RID1000 but no supported non-admin execution path is
available through this connector. Genuine Windows cancellation, owned-worker crash
recovery and canary denial therefore remain BLOCKED here. No impersonation,
privileged account launch, ACL change or synthetic result is substituted.
Actual batch-token, DPAPI/network authentication, RDP-disconnect/logoff and reboot
survival remain untested until authorized non-admin execution/installation is possible.

[REQUEST-0009](../decisions/REQUEST-0009.md) is the consolidated final review request.
It is NOT READY FOR ACTIVATION until the private relay configuration and required
real package-bound acceptance evidence are complete and final approval is granted.
Architecture approval in [RESOLUTION-0008](../decisions/RESOLUTION-0008-architecture-only.json)
authorizes preparation, not task registration/enablement.

[Evidence and hashes](evidence/phase10-review/CERTIFICATION.json).
