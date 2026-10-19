# DMB single foreground attempt: FAILED — PRESERVED FAIL-CLOSED

One authorized attempt ran October18,2026,9:10:07–9:10:58PM EDT (51.426s),
within the420s overall/20s native limits. Policy renewal was expiry-only, signed
and verified with both existing keys; exact policy SHA256:
`dc13ce2631f917271f3eb1921e4d6605b12850f5bfc664dcc9e449e15df5d704`.
No credential, privilege, model, source pin or runtime safety setting was changed
for execution. The reviewed driver source was local0e54c43 / GitHubfb24fe9;
worker clone02643e0 and the pinned Codex0.159.0-alpha.3 binary were unchanged.

| Requested evidence | Result |
| --- | --- |
| Signed directive admission | PASS: DMB published `d1-f24714f48bd39707`; worker validated and durably acknowledged its exact digest. |
| Genuine Codex research | FAIL at CLI initialization: read-only filesystem, OS error30. One launch intent; no model-turn events or sealed native completion. Model capacity was NOT TESTED. |
| Signed completion and GitHub readback | Signed **NEEDS_HUMAN failure report** published and read back successfully. No successful completion is claimed or produced. |
| Durable audit | PASS: both audit chains verify; worker has29 records, controller18. Both retain blocked state and escalation evidence. |
| Duplicate suppression/restart | A subsequent worker restart was refused by quarantine. One native intent remains; no second execution. Successful-completion replay/recovery remains NOT TESTED. |
| Unattended readiness | BLOCKED. No scheduler proposal/activation follows this failed attempt. |

GitHub readback commit `b4bc96b6c8244b72526b589085d1239960520f20`,
tree `3e36e77f3c772f9de4dfd15fa49368152925f1c9`. Signatures and Git blob
identities were independently verified for the directive, ACK, failure report
and original immutable BLOCKED heartbeat. The receipt is a failure attestation,
not evidence that a Codex model completed a research task.

The raw private startup logs contain read-only-filesystem initialization failure
(OS error30). Their content is not exported; hashes and sanitized classification
are retained. The exact initialization component/path has not yet been isolated;
do not infer a credential problem, capacity failure or a particular directory.
No model switch, second task, window extension or automatic recovery was attempted.
The native journal remains INTENT, worker EXECUTION_UNCERTAIN and controller
SUPERVISORY_EXCEPTION; the directive is not marked completed.

A post-attempt control-flow correction makes a quarantined CLI return nonzero
**after** delivering its existing durable failure report, and checks quarantine
before publishing any new admission. The old driver could make metadata-only
stage calls after failure while the native gate still prevented another launch.
This correction is prepared for review and is not recertified by the failed run.
It does not clear quarantine, reset counters or retry native execution.

Next safe work: isolate the supported writable runtime-initialization requirement
from read-only evidence, then prepare a narrowly scoped fix preserving existing
authentication, sandbox and identity controls. A **new native certification attempt
requires separate explicit authorization** and evidence-bound reconciliation of
this retained INTENT. Do not delete/reset the journal or silently renew authority.
Windows isolation/cancellation/recovery, durable remote supervision and approved
unattended scheduling also remain separate gates. REQUEST-0009 stays WITHHELD.

All production systems, original heartbeat/history, prior installations, private
keys, journals and certificates remain preserved. No service/task, paid platform,
main merge, trading action or production change occurred.

Evidence and SHA256 manifest: `docs/evidence/ddb-single-foreground-20261019/`.
