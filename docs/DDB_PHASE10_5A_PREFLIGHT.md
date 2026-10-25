# Phase 10.5A — trust and native containment preflight, review only

Verdict: preparation package is reviewable. **GO to consider approvals1–4 only
within the conditions below; NO-GO research execution and unattended operation.**
All new grants remain WITHHELD. No native tests, credentials, trusted branch,
VPS deployment or production action occurred. The verified worker ZIP is not rebuilt.

## Verified facts versus proposed/missing trust

| Item | Verified fact / exact proposal | Missing value and responsible owner |
|---|---|---|
| Publication | Phase10.4 draft PR#3 f0308c534fa695ea526dedfc790f098fad34590e; no merge | Repository owner retains merge authority; this phase grants none. |
| Worker package | 0.4.0-ddb-review1,source c7574b2757b48f5e167ee8135c3c70913f5908b3;ZIP SHA256 06a5eded7bcfc3ad2cbecf9140e47b88f6a65848c6929847f1de7dd8281791e0;manifest SHA256 8aa986c9a02f05fe1cd30fb18b957aa4610dd180e3e2866f23241197c33e5b0f | Target-account file/signature revalidation occurs only after approved deployment; not performed here. |
| Carrier | Proposed exact empty branch coordination/dmb-ddb-windows-0011,repo oluadegbu/Codex--DSV-; compiled JSON routes only | Not created/trusted; repository owner must approve one creation, no main/old-stream changes. |
| Signers | Proposed two dedicated Ed25519 roles; worker_id windows_codex_ddb_0011,key_id ddb-windows-0011 | No enrolled Windows public keys/fingerprints. Human approver plus designated supervisor/DirectiveCodex key custodians must authorize enrollment and publish public fingerprints. No test key becomes real trust. |
| Policy | Version1,SHADOW,policy_id ddb-windows-0011-foreground,max_tasks1,codex_shadow_review_v1,report_max_age600,document_ttl900;expiry60 minutes from verified future approved start | Signed Windows policy hash/absolute window absent; supervisor prepares after enrollment and human reviews actual binding before any research grant. |
| Old policy | Linux dc13ce2631f917271f3eb1921e4d6605b12850f5bfc664dcc9e449e15df5d704 is historical,expired and consumed | Cannot renew/reset/import its INTENT or keys to authorize Windows. Preserve quarantine/receipts. |
| Source pins | Published code f528274914cfe0ccb3743294d29ab6b6bf5e0b9a;tree c78bcd31b498bdfea9499f688fca08dd6acaa988; fixed source models.py/scoring.py | Clean Windows clone commit/per-file pins not created. Authorized deployment custodian records them later; not needed to run credential-free Python containment fixtures. |
| Endpoint | Compiled repository API https://api.github.com/repos/oluadegbu/Codex--DSV-; earlier cloud GitHub exchange verified | Actual Windows repo authorization and Codex service destinations/hook/MCP/proxy configuration unverified. Credential custodian/platform owner supplies narrow non-secret metadata; no broad discovery or secret reads. Offline native fixtures need no network. |
| Identity | Intended existing WIN-HQAAFGGU1AM\DirectiveCodex,SID S-1-5-21-3675741470-1525898003-3877381073-1000;historical non-admin Medium PASS | Current actual token/session and filesystem denial remain unverified; local operator must use that session, not Administrator observer. |
| Credential | Minimum Metadata read/Contents read-write,this repo only,prefer existing approved App installation token <=60 minutes | Availability/owner/expiry absent; repo credential owner must approve enrollment. No admin/Actions/secrets/merge/bypass/new App authority. Same-account DPAPI is not hostile-process isolation. |

Repository token permissions are not branch-scoped. Compiled branch checks do not
prove main protection. Role keys stored under one account are protocol separation,
not independent OS principals. No current Windows signer/policy hash is invented.

## Restricted deployment prerequisites and exact procedure

`preflight/ddb-10.5A/README.md` provides the ordered procedure, approval-parameter
schema and independent commands. Separate addon ZIP/file hashes are published in
`preflight/ddb-10.5A/releases/`. It contains only test scripts and existing offline
fixture snapshots; no interpreter, credential, signer, enrollment or Codex runner.
Download both artifacts through approved GitHub access, verify exact ZIP/manifest
hashes and entry boundaries, then (only after deployment approval) unpack once:

- Worker ZIP to C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011\package.
- Addon to that root\preflight-10.5A; empty state/artifacts under the same root.
- Existing root/reparse/substitution means STOP and preserve; no overwrite or
  alternative-path guessing. Use existing account permissions, never change ACLs.
- Verify embedded Python Authenticode,complete manifest/no extra import files,
  exact official Codex file hash without executing Codex. No system Git/Python,
  PATH, service, scheduled task, account or firewall installation.
- No DDB key/config/token enrollment,worker clone/native task or journal is
  required for these credential-free fixture cases. Enrollment is separate.

The deployment routes write only the new root. This is an application scope, NOT
proof the account cannot modify production. DAT/DSV/DPM/Pulse/OpenClaw/trading
paths, controls, services and credentials are prohibited and are not probed. Native
canaries assess only specific approved other-account fixtures; blanket OS or
production isolation cannot be inferred. Stop on any unexpected access requirement.

## Independently executable test package and evidence

The addon uses the existing bundled interpreter with -I -B, reviewed token/SID,
manifest verification, exact script hash and a separately approved public grant
file/hash. Local JSON hashes bind parameters; they do not authenticate a human or
create authority. The authenticated operator's explicit approval must precede runs.
New cases use fresh exclusive directories and never reset an uncertain case.

| Independent case | Evidence after future approval | Current classification |
|---|---|---|
| identity | Actual token user/SID/groups/Medium,no impersonation;no child/auth | Native NOT TESTED |
| filesystem | Own positive read/write; existing independently evidenced harmless canaries fail OPEN_EXISTING with WinError5 only | Native NOT TESTED;no ACL/fixture creation authorized |
| containment | Suspended fixed bundled Python image pinned by file identity;observe parent+descendant in owned Job,then zero after termination | Native NOT TESTED;not Codex/worker containment |
| cancel / timeout | Cooperative fixed Python STOP/exit;3-second deadline then job drains | Native NOT TESTED;not Codex turn/interrupt ACK |
| cpu / resource readback | 2 CPU seconds,64MiB,2-process configured Job;busy fixture terminates within6-second bound | Native NOT TESTED;memory-pressure/cap-overflow stress not implemented or claimed |
| crash | Fixed child exit73,owned cleanup,preserved INTENT/RESULT | Native NOT TESTED;owner-process crash/kill-on-close recovery still unproven |
| contracts signed-receipts | Signed fixture validation/tamper and duplicate suppression against in-memory carrier | Offline PASS:2 tests;no real signer enrollment/GitHub receipt |
| contracts recovery | SEALED recovery without rerun,uncertain INTENT refusal,corrupt audit denial | Offline PASS:3 tests;not native worker crash recovery |
| contracts policy | Expiry/signature/stream/workspace/tool denial | Offline PASS:5 tests;not OS isolation |

Native fixture code was compiled/read offline only, not executed or certified on
Windows. Win32 signatures reuse existing reviewed structures/APIs but these new
fixture paths are unrun. Each case needs explicit scope approval; a failure or
missing RESULT means preserve/stop,not retry. The intended next evidence is native
observation after approval, not another synthetic certification cycle.

## Separate approval decisions

| Decision | Recommendation for subsequent authorization | Exact scope / maximum window / rollback |
|---|---|---|
| 1 Coordination branch | Conditional GO for one empty documents-only branch creation | Exact repo/branch above;act within60 minutes of approval;no main/old-stream change. Disable dispatch on revocation;preserve history,never force/delete uncertain state. |
| 2 Dedicated enrollment | Conditional GO for approved custodians only;no enrollment now | Two role keys/current-user DPAPI and one repo-only credential;publish fingerprints/owner/expiry,not secrets. Enrollment within60 minutes of approval;policy/credential TTL<=60 minutes. If provider cannot meet scope/TTL,NO-GO pending exact deviation review. Owner revokes dedicated credential;retain evidence and expire policy. |
| 3 Restricted deployment | Conditional GO without native child launch or secrets | Exact unchanged worker ZIP and separate addon,new root only,existing non-admin identity;one <=30-minute prep session. Missing permissions/partial root means STOP;preserve all installs and no ACL changes. |
| 4 Native isolation fixtures | Conditional GO for specified credential-free Python cases only,after exact addon hash and independent canary evidence approved | Approval expires<=30 minutes;one invocation/case,combined<=120 seconds,each process+cleanup<=9 seconds. No Codex/network/credentials/production. Terminate only owned Job;preserve partial INTENT/RESULT,no rerun. Accept only component-scope evidence. |
| 5 Codex research | NO-GO / PROHIBITED in this phase | No native model/worker launch,renewal,capacity retry or implicit second turn. Later grant requires actual signed policy/source/endpoint/identity/isolation review. |
| 6 Unattended operation | NO-GO / WITHHELD | No task/service/scheduler/batch-right change. REQUEST-0009 remains separate. |

Recommendations are not grants. No actual start/expiry window is opened now.
Enrollment and branch approval do not authorize model execution. Independent receipt
fixtures are not actual delivery or human authorization. Owner-process recovery and
native Codex cancellation remain later gaps,not swept into approval4.

## Expiry, revocation and rollback

Revoking/expiring the public fixture approval blocks new cases. Retain original
approval record,probe/manifest hashes and case evidence. No credentials are involved
in fixture tests. For later enrollment, human owner revokes only dedicated GitHub
credential and retires that policy/signers; never rotate production credentials.
A key has no implicit lifetime grant beyond its signed policy; no auto-renewal.

Stop/drain only the new fixture-owned Job. Preserve new/old roots,keys,journals,
receipts and branch history. Do not delete INTENT,clear counters,change an approval
hash to resume,or treat a failed case as successful. SEALED receipt replay may
publish without re-executing; uncertain worker INTENT stays quarantined. Keep every
trading/service/schedule/security boundary unchanged. No deployment or rollback
command is executed by this review.

## Immutable addon release

Test-only ZIP: `DDB-Preflight-10.5A-75c2f293c634.zip`, 18683 bytes.
SHA256 `ff682dd000a7884f811887de387086dd70c1390da2568b319032175efe5d2bb9`.
Manifest SHA256 `ab4b26fed62c80d68e0243f1b65e79e0d686ca880cd596de21d4543615c9ba22`.
Two independent builds match; all ten contracts pass again from the extracted
archive. Linux negative gate refuses native execution before host access. These
checks do not run or validate native Win32 APIs. This addon changes neither the
verified worker ZIP nor its dependencies. Source/release inventory and evidence
are committed with this review; no native activation authority is included.
