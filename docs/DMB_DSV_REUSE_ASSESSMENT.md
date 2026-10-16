# DSV reuse assessment: no infrastructure activated

Recommendation: retain the existing DSV supervisory routing and policy layer; reuse
DMB's existing atomic SQLite controller as the durable inbox/outbox. Mount the new
thin HTTPS adapter in an **identified and approved existing non-admin host** with
an approved TLS ingress. Windows continues outbound-only. Add an existing Temporal
namespace/task queue for durable wake/recovery only after its endpoint, ownership,
authentication and DMB-specific permissions are verified. Do not create another
queue platform, expose OpenClaw's local port, or reuse DAT/DPM credentials.

This is a conditional integration recommendation, not an activated endpoint.
REQUEST-0009 remains WITHHELD. DMB LOCAL SHADOW PASS / FULL CERTIFICATION BLOCKED.

## Verified infrastructure and its limits

Read-only inspection was restricted to DSV's own public source, selected own-state
metadata, approved task/network/process metadata and the supported OpenClaw status
interface. No production project internals, messages, credentials, browser tokens
or raw runtime logs were exported. DSV CLI was not invoked because its commands
initialize state. Its database was opened read-only/query-only.

| Component | Actual evidence | What it establishes |
| --- | --- | --- |
| DSV | `C:\DirectiveSupervisor`, on `WIN-HQAAFGGU1AM`; source and own SQLite metadata | Existing routed envelopes, delivery queue, approvals and hash-chained audit. Three COMPLETE messages, zero queued deliveries at inspection. No DMB route in observed configuration. |
| DSV browser handling | Current `browser_adapter.available=false`, `required=false`; `service.py` preserves QUEUED messages and returns BROWSER_DEFERRED | Core queue survives browser loss. The shown reasoning path still calls BrowserBridge for ChatGPT responses; no independent Brain delivery or self-wake is established. |
| DSV historical certification | Browser-optional certificate PASS dated 2026-10-03; Phase1 certificate BRIDGE_ACTIVE_AUTO_SAFE | Historical receipts only; no new unattended/remote DMB certification. Current mode does not grant DMB authority. |
| OpenClaw | Official installed package 2026.9.7; supported `gateway status --json --timeout 3000` exits 0, local RPC reports OK | Existing configured local RPC works. No credential exported; the status response does not report authentication mode, so independent auth validation remains BLOCKED. |
| OpenClaw network/startup | Loopback listeners `127.0.0.1:18789` and `:18799`; probe `ws://127.0.0.1:18789`. Existing gateway task Running, Administrator / Interactive / Limited, LogonTrigger | Local control-plane reuse candidate only. No verified remote HTTPS ingress, reboot/full-logoff independence or least-privilege DMB execution host. Do not change this production task. |
| Existing Pulse task | Task metadata only: existing Administrator / Interactive / Limited | Not a DMB worker or hosting authorization. DAT internals and schedules unchanged. |
| Temporal | No Temporal endpoint/task queue in scoped DSV sources; no matching service/process in scoped metadata | Deployment elsewhere remains UNKNOWN, not absent. No namespace, queue, TLS identity, durable trigger or approved DMB access verified. Preserve separate approved DAT Temporal milestone. |
| DMB | Existing dedicated atomic SQLite controller and signed Brain/Windows protocols | Local durable state and retry/deduplication contracts can be reused directly; no new broker required. |
| Execution access | Connected remote executor is Administrator; existing DirectiveCodex Windows execution receipt is preserved | Current executor cannot certify non-admin Windows workers. No impersonation/elevation or injection into the user's session. |

DSV's observed routes target DAT and DPM; DPM explicitly records HANDS_OFF. Those
routes confer no DMB authorization. No project route, account, service, task, ACL,
firewall, policy or credential was changed. OpenClaw's existing credential handling
stayed inside its official CLI; it must not be copied into a worker or GitHub.

## Shortest approaches

| Approach | Dependencies / decision |
| --- | --- |
| **DSV supervision + existing DMB SQLite + approved host/TLS mount** | Recommended smallest path. DSV emits only approved structured task IDs/templates through a dedicated scoped Brain identity. Mount `/v1/dmb/operations` and `/v1/dmb/windows` in existing approved hosting. Windows only polls HTTPS. Needs host/ingress ownership, durable storage, non-admin identity, private pairing and explicit deployment approval. |
| Same, with existing Temporal | Preferred durable wake/recovery extension if an approved deployment exists. Verify address, namespace, DMB-only task queue/identity, TLS, retention and healthy worker first. Do not repurpose DAT queues or modify its integration milestone. |
| DSV browser + OpenClaw local gateway alone | Insufficient for independent remote HTTPS delivery, browser disconnect and OpenClaw outage requirements. Keep as strategic interface, not durable authority or latency-sensitive executor. |
| New relay/platform | Not recommended while approved existing hosting/Temporal inventory is unresolved. Requires separate approval and cost review. |

The controller's durable state must not depend on DSV/OpenClaw/browser uptime.
The HTTPS serving host also needs an approved durable trigger/controller pump for
supervisory review and follow-up. Neither a WSGI callable nor an ordinary ChatGPT
conversation supplies scheduling. A persistent bounded Brain worker or supported
authenticated connector must be explicitly identified and certified; no automatic
future ChatGPT execution is claimed. Latency-sensitive ingestion remains separate.

## Reusable adapter delivered

`dci.master.https_gateway.DMBHTTPSApplication` is a WSGI callable, not a server or
installer. It directly invokes the existing signed handlers and atomic controller
with a fresh database connection per request. It opens no port and installs no
service. Exact HTTPS origin, route, JSON member uniqueness, body bounds, separate
Brain/worker keys, scopes, replay checks and durable signed ACK semantics remain
enforced. Untrusted forwarded headers cannot assert TLS. Backend uncertainty
returns 503; clients retain stable message IDs. There is no remote shell, raw
mailbox prompt, approval action or implied DAT/DPM execution authority.

`configured_factory` reads only explicit private DMB configuration, requires the
existing non-admin workspace guard, and retains DPAPI on Windows/current-user-only
files on POSIX. It does not provision identities or export credentials. The
existing Windows v0.3.0 package and fingerprinted worker sources are unchanged.

Eight new offline adapter tests plus eight existing operations tests PASS. They
exercise actual temporary SQLite state, signed requests, replay/reopen, original
worker protocol, scope/route refusal, simulated backend outage/recovery and audit
corruption. They do **not** certify real HTTPS ingress, external authentication,
Temporal, Windows cancellation or OS-enforced isolation. TLS termination and body
read timeouts remain serving-host responsibilities; never trust forwarded headers
without an explicitly configured trusted ingress. No endpoint was activated.

## One consolidated approval/access request

Continue REQUEST-0009, not a new deployment or credential request. Minimum missing
operator input is the **existing approved host and HTTPS endpoint/access reference**
plus, if available, Temporal address/namespace/DMB task-queue ownership reference
(non-secret metadata only). Approve a DMB-only scoped route/identity and approved
private configuration mechanism; do not send any secret in chat. Existing DSV
routing and OpenClaw Administrator credentials must not be inherited implicitly.

After endpoint review and real non-admin preactivation certification, final
approval must enumerate: hosting the two exact HTTPS routes and durable DMB
storage/trigger under a dedicated least-privilege runtime; private DMB pairing;
any demonstrably missing account-specific Windows batch-logon right/local
Windows-protected credential enrollment; and exact receipt-bound registration and
activation of the existing pinned worker task. No registration, credential
enrollment, security policy or persistent host process is approved by this report.

The already published single foreground procedure remains
`docs/DMB_PHASE10_NATIVE_CERTIFICATION.ps1`; no new exploratory diagnostic loop is
requested. Its real Windows cancellation/crash/recovery/access-denial/hour-boundary
receipt and remote TLS/HMAC preflight must precede task activation. Current remote
executor cannot safely perform those DirectiveCodex actions.

No new software subscription is needed for the adapter/SQLite. Existing hosting
capacity, ingress availability, backups and incremental cost are unverified; no
zero-cost hosting or new account is assumed. For capacity review only, a small
non-admin application host with dedicated durable storage/backups is sufficient
for initial bounded shadow traffic; measure before assigning production capacity.
Rollback: remove only the approved DMB route/mount and stop its owned runtime,
then use the existing exact-task disable/drain/unregister procedure if activated.
Preserve all journals, private pairing, installations and audit evidence. Never
rollback or restart DAT, DPM, DSV, Pulse or OpenClaw as part of DMB rollback.

Evidence and source hashes: `docs/evidence/phase10-dsv-reuse/ASSESSMENT.json`.

Published source `8afb01009aa07532da912a22ff42ecafc63fad17` passes **194 CI
tests**, 100 verifier cycles and 1,099 worker test executions. Linux paper-process
workflow completes three jobs with zero duplicate dispatches and recovers a
controller crash without rerunning its worker. Run `38841861224`, job
`116783543495`; exact provenance and suite counts are in `PUBLICATION_CI.json`.
These remain local/shadow contracts, not remote ingress or native Windows gates.
