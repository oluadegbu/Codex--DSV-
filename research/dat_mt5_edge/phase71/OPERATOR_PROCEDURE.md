# Conditional read-only preflight procedure — NOT EXECUTED

The present phase authorizes offline preparation only. This procedure may be used
only after [Gate A](GATE_A_APPROVAL_DRAFT.md) receives explicit approval against
a complete private manifest. Do not run a terminal, sign in or deploy this script
from the current directive. Existing no-credential/no-trading boundaries remain.

## Offline prerequisites, before any session

1. Privately populate one Target record using the disabled field example. Server
   is exactly VantageMarkets-Demo. Populate exact login/company/currency, terminal
   identity/build/paths and the four exact broker symbols; there are no defaults
   or suffix searches. Do not put a password/token into either JSON file.
2. Record actual existing investor-access/isolation evidence. No new account,
   credential, permission, software install or security change is implied.
3. Independently review the native source and Python validator, compile source
   offline with an already authorized native toolchain, and record source/EX5/
   terminal binary hashes and compilation provenance. Compile/runtime have **not**
   been verified here. Do not start MT5 to perform the offline review.
4. Obtain the exact Gate A approval, window and nonce, then make the private plan
   reflect that external approval. The JSON flags/references are not a signed
   approval mechanism and cannot create authority by themselves.

## Approved session only

The operator starts only the named isolated research terminal and authenticates
through the official interface with existing investor credentials. No password
is passed to the collector, Python, chat or Git. Enable no trading or DLL feature.
If read-only access is unavailable, stop; do not try master login as a substitute.

The exact four symbols must already be available/selected in the approved isolated
configuration. The collector does not call SymbolSelect or change settings. If
preparation of that configuration requires additional terminal mutation outside
the approved scope, request it separately; never modify production Market Watch.

Run the reviewed one-shot native script with private exact expected inputs and
Gate A reference/nonce/window/evidence flags. It rejects incomplete inputs,
wrong/real/contest accounts, enabled account trading, mismatched terminal,
unrelated exposure, disabled connection or failing symbol data. It performs four
bounded symbol reads and calculation-only margin estimates, with identity fences
before/around/after capture. It has no account-selection/login/startup or order-
submission/modification/close code and no includes/imports/DLLs/web requests.

Capture produces one nonce-named private JSON file in the isolated terminal's
MQL5 Files sandbox, never FILE_COMMON or an arbitrary external path. It refuses
an already existing nonce file and verifies output bytes. Unique nonce plus a
single supervised invocation are required; the file-existence check is not an
adversarial multi-process atomic-create guarantee. Keep terminal metadata, private
snapshots and normal platform logs private. No automatic upload occurs.

If the script stalls, fails, is stopped, encounters stale/closed symbols or emits
no valid output, the result is NO-GO. Do not widen the window, switch accounts,
enable trading, select a substitute symbol or retry automatically. End only this
approved read-only research session as instructed by its operator; do not alter
production processes. Ordinary terminal cache/log changes are confined to its
approved isolated data folder, not a claim of whole-filesystem read-only behavior.

## Offline validation, after capture

On an authorized offline machine with the existing repository Python environment:

```sh
cd research/dat_mt5_edge
python -m phase71.preflight --snapshot private_snapshot.json --plan private_gate_a_plan.json --output redacted_gate_a_result.json
```

All three paths must be the operator's explicit isolated research files. Never
point the command at credential files or production locations. The validator
reads at most 64 KiB per input, rejects unknown/duplicate keys, checks the approved
source hash and exact account/symbol schema, and creates a new redacted result
without overwriting the inputs or existing output. It makes no broker connection.

`PASS_READ_ONLY_SNAPSHOT_CHECKS_ONLY` means those supplied data satisfy the offline
checks. It does not authenticate the snapshot, establish a compiled binary's
provenance, prove investor login or grant Gate B. Evidence references/hashes must
be independently reconciled to the actual supervised run. The result deliberately
keeps snapshot authentication and order authority FALSE. Retain private evidence
locally and publish only reviewed redacted aggregate outcomes.
