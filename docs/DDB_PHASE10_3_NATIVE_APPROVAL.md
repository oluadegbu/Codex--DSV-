# Phase 10.3 native Windows approval package — review only

No approval, enrollment, deployment or native test is implied by this document.
Historical records are preserved. Current source/code and package pins are recorded
in the companion PUBLICATION_PACKAGE.json and WINDOWS_RELEASE.json evidence.

## Exact proposed persistent data changes

- Repository: oluadegbu/Codex--DSV-. Proposed new **empty documents-only** branch:
  coordination/dmb-ddb-windows-0011. Owner-approved creation must use an empty
  initial tree, not main or the quarantined Linux branch. The worker cannot
  create it and may only CAS-update this compiled branch. It has not been created.
- Preserve coordination/dmb-ddb-v1 and all original signed documents, Linux
  INTENT/quarantine, policy history, keys and audit without importing/resetting them.
  A Windows task gets a fresh policy, task ID and private journal namespace.
- Existing host WIN-HQAAFGGU1AM, existing account DirectiveCodex, SID
  S-1-5-21-3675741470-1525898003-3877381073-1000. No new identity or ACL grant.
- Fresh root only:
  C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011
  with package, worker-clone, state and artifacts children. Create/write only from
  the actual DirectiveCodex non-admin Medium session after explicit approval.
- Existing official user-local Codex0.162.1 stays installed/authenticated;
  SHA256 dd13bdb162a184fa04039488b234a8258ef9b76f84e926c505d5742b19249a6a.
  No reinstall, PATH change or borrowed CODEX_HOME. Existing v0.1.x/v0.3.0 state
  and pairing remain untouched.
- Dedicated supervisor/worker Ed25519 keys and a dedicated repository-selected
  GitHub credential. Current-user DPAPI for Windows private files in state:
  worker.dpapi, controller.dpapi, worker-signing.dpapi,
  controller-signing.dpapi and github.dpapi. No plaintext credential is written
  to disk/chat/arguments/documents. No Linux/DAT/DPM/Pulse secret is reused.
  Keys are not enrolled by this implementation phase. Public signer fingerprints
  and final signed policy hash therefore do not yet exist.
- GitHub minimum: repository Metadata read and Contents read/write; no admin,
  Actions, secrets, merge or bypass privilege. Application branch restriction
  is not a GitHub server-enforced branch grant. Same-account controller/worker
  keys separate roles, not OS identities; this limitation must be approved.
- No scheduled task, service, batch-logon right, firewall/security-policy change,
  paid host, public listener or production modification.

## Exact policy proposal and unresolved values

Keep signed document version1, SHADOW, policy_id ddb-windows-0011-foreground,
worker_id windows_codex_ddb_0011, worker_key_id ddb-windows-0011, template
codex_shadow_review_v1, max_tasks1, report_max_age600, document_ttl900. Expiry
proposal:60 minutes from verified approved start. No renewal or model fallback.
Fill actual dedicated supervisor/worker public keys only after enrollment approval;
review both fingerprints and resulting canonical policy SHA256 before execution.
Native execution deadline20 seconds; total foreground cycle420 seconds. Review
only pinned src/dci/models.py and src/dci/scoring.py, supplied as bounded context.
No arbitrary mailbox prompt, shell command, model tool or approval capability.

The API endpoint is https://api.github.com/repos/oluadegbu/Codex--DSV-.
Exact Codex service endpoints and inherited non-secret proxy/CA/config requirements
must be verified on the approved host before a final execution grant. No broad
network permission or credential inspection is requested. Managed/user hooks,
MCP and runtime configuration are a preflight review gate: client-side tool-event
rejection is reactive and cannot substitute for OS confinement or prove no
startup configuration side effect. Stop if host configuration exceeds the grant.

## Bounded native plan (NOT EXECUTED)

1. Verify real process token/SID, no impersonation or Administrator group,
   Medium integrity, exact source/Git/package/executable pins and active approved
   policy; refuse short/reparse/substituted paths. Inspect only dedicated config
   ownership/metadata; never dump secret contents. No Administrator observer launch.
2. Read existing approved harmless canary creator manifest, verify its pinned
   provenance/existence and perform OPEN_EXISTING read/write access probes. Only
   ERROR_ACCESS_DENIED counts; missing file and other errors are BLOCKED. Successful
   unauthorized open is FAIL and ends certification. Use existing harmless
   canaries in the fixed other-account fixture path, never production contents.
   Check positive own-workspace access separately. No ACL/user creation is authorized.
3. Verify outbound GitHub scope and exact remote branch state before a model turn.
   Publish signed admission/directive/ACK, validate role/policy/hash/sequence/expiry,
   commit INTENT, dispatch one genuine bounded Codex review, verify artifact/source
   unchanged, seal receipt, publish signed result, independently read it back and
   apply supervisory review. Only matching native receipt plus valid audit counts.
4. Reopen SEALED/REVIEWED state and replay signed delivery with zero second execution.
   Test crash-after-sealing/republication using separate controlled durable fixtures;
   an uncertain INTENT must stay quarantined. Do not kill unrelated processes.
5. Test native Job containment and deadline/cancellation with separately approved
   named harmless fixtures. Existing offline subprocess fixtures do not prove
   Win32 Job cleanup. Actual turn/interrupt acknowledgement would require an
   additional explicitly scoped native cancellation turn if the sole research
   turn already completed; do not silently spend a second model task. A process-only
   startup/termination fixture cannot be reported as actual turn cancellation.
6. Attempt disallowed workspace/tool routes via controlled signed fixtures only;
   rejection must occur without opening production paths. Preserve failure evidence.
   Native OS-denial results prove only the tested canaries, not universal hostile-code
   containment. DDB never obtains trading authority by implication.

## Command, approvals and rollback

The exact foreground command shape is recorded in DDB_WINDOWS_ADAPTER_CERTIFICATION.md.
Replace no hash/key placeholder by inference. Before execution approval, the owner
must review actual ZIP/source/policy hashes, public signer fingerprints, dedicated
credential ownership/expiry and exact endpoints. Approval to create the branch or
keys alone does not authorize the model turn. REQUEST-0009 scheduling remains withheld.

Rollback of a future approved attempt: STOP/drain only the new root's owned job,
verify zero child processes, seal audit/receipts and preserve the whole installation.
Keep journals, keys, artifacts and branch history; never delete/reset an uncertain
intent. No prior installation or production service/schedule is touched. Dedicated
credential revocation is a separate approved owner action. No automatic main merge.

Readiness: package/offline evidence can be approved for review; actual native
execution and OS isolation remain BLOCKED/NOT TESTED until the above approval and
host gates pass. This is not production or unattended readiness.
