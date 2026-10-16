# DMB Phase 8 continuation — October 12, 2026

Outcome: **DMB LOCAL SHADOW PASS / FULL CERTIFICATION BLOCKED**.
Dates in this narrative use America/New_York; capture timestamps use UTC.

The previous 18 hashed Phase 8 artifacts, 35 original source files, three Phase 8
source files and two verified Git bundles are retained. The existing 100-test
suite passes unchanged. The original 84-test milestone, 100 verifier cycles and
1,099 worker test executions remain preserved historical local evidence.

## Fresh external checks

The authenticated GitHub connector still identifies `oluadegbu` and repository
ID `1409360122`, `oluadegbu/Codex--DSV-`. User metadata reports push permission,
but branch creation from current `main` returns integration HTTP403. No branch
or successful push is claimed. Installation scope is not exposed by available
supported tools. A normal `gh` read-only identity probe also failed; no confirmed
standalone CLI identity is available for an alternate write path. No login,
credential export or integration permission change was attempted.

Windows still reports Administrator, enabled Administrators membership and High
integrity. Only `whoami` probes ran there. Cloud uid1000 Codex CLI remains version
0.159.0-alpha.3 with normal ChatGPT login status; its fixed 15-second read-only
invocation fails app-server runtime startup without a completed turn. No sandbox,
HOME, runtime or authentication protections were changed. Live Codex retry,
cancellation and sandbox-denial certification remain NOT TESTED.

Fresh synthetic canaries under two distinct temporary roots permit both read
and write by the neighboring same-UID subprocess. OS worker confinement is
therefore BLOCKED. These probes use no real project data or secrets. The earlier
logical isolation certificate is not promoted to OS isolation.

No new authorized external project locations, remote Brain endpoint, OAuth
issuer/client configuration, subscription, provider destination or activation
approval was supplied. Prior reconciliation retains VERIFIED LOCAL, HISTORICAL,
UNKNOWN and BLOCKED scopes. Real inbox/outbox and WhatsApp/email delivery remain
uncertified. No production service was stopped or modified.

## New safe work

`src/dci/master/authorization_contract.py` provides offline resource-policy
fixtures for exact issuer, audience, client, subject, project, scope and validity.
Fixture approval checks additionally bind request ID, scope digest and expiry;
ordinary approval cannot release a degraded execution outcome. The 17 tests also
verify stable synthetic subject identity across token refresh and denial after
ACL removal. Existing HEG rejects the fixture policy result as approval.

These are policy-rule tests, **not OAuth authentication**. The module accepts no
bearer tokens, decodes no JWTs, verifies no real signatures, and operates only
with synthetic principals and HTTPS `.invalid` origins. Results explicitly deny
external identity verification, live execution and human approval. No identity
service, account, key material, callback or network transport is created.
Official requirements are documented in
[OpenAI MCP authentication](https://developers.openai.com/plugins/build/auth):
real resource-server verification and scoped authorization must precede exposure.

The new tests are isolated under `certification_tests/` to preserve the exact
existing 100-test verifier and its source hashes. To reproduce both suites and
the fresh synthetic denial probes without rewriting prior certificates:

```sh
python tools/verify_phase8_authorization.py --output /tmp/dmb-authorization-evidence
```

[Complete matrix](evidence/phase8-20261012/CERTIFICATION_MATRIX.md),
[local verification](evidence/phase8-20261012/LOCAL_VERIFICATION.json),
[external checks](evidence/phase8-20261012/EXTERNAL_RECHECK.json), and
[artifact hashes](evidence/phase8-20261012/ARTIFACT_MANIFEST.json).

## Approval gates and next actions

Existing requests remain open; repeated development instructions do not authorize
their hard-gated actions. No duplicate escalation request was created.

HUMAN REQUIRED: inspect the existing GitHub App installation for only this
repository and Contents read/write; approve a pending update or reauthorize only
if needed. Keep other grants unchanged. Provide an existing supported non-admin
DirectiveCodex environment and independently enforced worker boundaries before
live worker certification. Remote Brain/HEG activation requires exact authenticated
endpoint/provider/destination/consent scope; persistent installation and costs
require separate explicit approval. No credentials need to be sent in chat.

Next safe work is offline callback/subscription authorization fixtures and scoped
reconciliation contracts. Exact supplied authorized project artifacts can be
reviewed read-only. Production integrations and the separate approved DAT Temporal
milestone remain unchanged. Full certification will stay blocked until actual
mandatory external and isolation evidence passes.
