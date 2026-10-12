# REQUEST-0003: Non-admin Windows/Codex runtime certification
STATUS: OPEN

## CONTEXT
The requested target is C:\Directive\DCI\Codex--DSV- under non-admin
DirectiveCodex. Safe cloud implementation can proceed separately.

## EVIDENCE
Desktop Commander identity probe returned Administrator, enabled Administrators
membership and High Mandatory Level. Windows directory listing exists, but Git
access fails and direct file realpath returns EPERM. Cloud is uid1000 agent.
Codex CLI 0.159.0-alpha.3 reports ChatGPT login; exec read-only initialization
fails because runtime storage is read-only. Exact Codex Remote account identity
and DirectiveCodex mapping are not certified. No bypass/elevation was attempted.

## OPTIONS
1. Provide an independently certified non-admin DirectiveCodex remote connection
   and accessible isolated workspace with supported Codex runtime storage.
2. Continue cloud-only shadow development while Windows activation stays gated.

## RECOMMENDATION
Continue option 2 now; supervisor/operator should certify option 1 separately.
Preserve sandbox and privilege protections; no credential requests or changes.

## IMPACT
Blocks Windows deployment and live Codex execution certification, not isolated
mailbox/Runner/HEG tests. No service or account change is authorized by this request.
BLOCKING: YES
HARD_GATE: YES

## SUPERVISOR RESPONSE
Pending. Administrator connection was used only for the read-only baseline probe.
