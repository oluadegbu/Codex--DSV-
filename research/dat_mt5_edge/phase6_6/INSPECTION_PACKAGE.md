# Restricted inspection handoff — prepared, NOT RUN ON VPS

Do not run through the Administrator Desktop Commander executor. Do not bootstrap a
restricted process by runas/impersonation/token/policy/ACL modifications. This package
does not create a supported standard-user connector. Operator must provide the
existing officially supported restricted route first; availability is currently BLOCKED.

## Before running

1. Verify standard-user effective token, independent source read-only permissions
   and an existing isolated writable research output directory. No production or
   broker credentials/configuration are needed. Check that code/interpreter are
   approved existing software, not programs supplied inside the transferred data.
2. Source is exactly `C:\DirectiveAutoTrader\Researchdata\data\data`; never broaden
   to its parent, production directories or MT5 caches. Refuse source/output symlinks,
   junctions and reparse points. Do not modify access times/settings intentionally,
   source files, services, schedules or installed software. Read-only opens may
   cause OS-managed access-time accounting; no attempt to alter that policy.
3. Example destination outside production: an existing
   `%USERPROFILE%\Documents\DATMT5Research\Phase6_6\inventory_run01`. Operator verifies
   its isolation. Raw data/private licensing evidence do not go to the public repo.
4. Use Python 3.10+ already present under this standard user. If unavailable, report
   BLOCKED; no installation or Administrator substitution. Invoke with `-I -B` so
   current-directory code and bytecode writes are avoided. Review package hash first.

## Stage A: bounded census, no decoding or execution

From the approved package folder in the actual restricted session (not executed here):

```powershell
python -I -B inspect_data.py inventory --output "$env:USERPROFILE\Documents\DATMT5Research\Phase6_6\inventory_run01" --restriction-attestation VERIFIED_STANDARD_USER_SOURCE_READ_ONLY
```

Hard budgets: 20,000 files, 600 seconds, 2 GiB per checksum, 8 GiB total checksum
bytes; no automatic widening. Exact paths/formats/sizes/UTC-convertible modification
metadata/checksums are recorded in searchable JSONL. Reparse points and unreadable
paths are explicitly incomplete; zero-byte files fail. Checksum matches identify
byte-duplicate files, never independent feeds. Skipped/capped hashes remain unknown.
No compressed archive is expanded during census. Extensions and filename instrument
hints are not certified formats/provenance. Report unfinished traversal as incomplete.

Script hard errors/time limits leave partial JSONL; no successful summary means no
completion claim. File-access races cannot be solved merely by symlink checks; the
verified source must be stable and not writable by concurrent untrusted processes.
Permission or source-change errors stop affected evaluation; do not retry unboundedly.

## Stage B: priority schema review and CSV/GZIP inspection

Review a maximum 64 KiB header/sample in the same restricted environment using only
an existing bounded inert-text viewer, without 2026 price inspection. If filenames
suggest holdout-only material, defer content inspection. Never infer UTC, source or
volume from filename alone. Create a schema **outside the source** using the disabled
example only after proving column positions/date format and historical clock rules.
For split date/time or non-UTC records, stop: this initial parser is unsuitable until
a separately reviewed normalization step exists. Do not simply relabel source time.

Start EURUSD, then GBPUSD, Gold, BTCUSDT, futures, other FX, in that order. One explicit
file/schema per invocation; separate existing output directory for each run:

```powershell
python -I -B inspect_data.py audit --schema reviewed_eurusd_schema.json --output "$env:USERPROFILE\Documents\DATMT5Research\Phase6_6\eurusd_run01" --restriction-attestation VERIFIED_STANDARD_USER_SOURCE_READ_ONLY
```

Per-run limits: 128 MiB decoded bytes, 64 KiB logical input line, 500,000 bars,
30-second cooperative loop budget. No archive extraction, executable loading, network,
external parser dependency or strategy invocation. Decompression calls may exceed
cooperative checks on pathological input; the independently restricted runner must
enforce a **60-second wall timeout and 512 MiB memory cap**. If it cannot, don't
decompress untrusted archives. Stop at any limit; do not certify a sample as a full
series. Full multiyear inspection requires explicit independently bounded chunks and
a reviewed aggregation plan; do not raise constants to obtain a PASS.

The script measures pre-2026 first/last inspected times, chronological violations,
duplicate bar timestamps, OHLC invalidity, weekend rows and raw timestamp gaps.
It does not mistake raw gaps for missing expected trading minutes. Zero rows or
invalid OHLC/order/source change fail; other outputs remain pending, never PASS.
At the first 2026 timestamp it stops **before parsing price fields**; the remainder
is not read for audit. This does not unlock the 2026 final holdout or prove that
the rest of a mixed archive has no earlier out-of-order observations.

ZIP/TAR/vendor binary formats are **opaque** in this first-stage package. Inventory
their bytes/checksums; separately review a bounded archive-directory-only viewer
before member reads. Max 1,000 members, 128 MiB/member, 256 MiB aggregate expansion,
100:1 declared ratio, no encrypted members, nested archives or path traversal;
validate actual decompression counters too. Never extract to disk or execute members.
If no approved bounded viewer exists, mark those archives pending; no installs.

## Stage C: complete certification review, mandatory before PASS

- Reconcile all chunks, duplicates and overlapping archives; checksum/member lineage
  and actual earliest/latest timestamps; distinguish inspected subset from full range.
- Independently review provider provenance and organizational use license evidence.
  A user transfer or source folder name is not permission. No provider contact is sent.
- Build reviewed expected-session calendars, broker/exchange timezone and DST rules;
  calculate exact missing expected minutes, off-calendar bars and coverage per year/
  session/fold. Don't assume weekends are universally invalid (BTC trades weekends).
- Check paired bid/ask versus single-side OHLC; cross quotes, precision/tick grid,
  abnormal jumps with independent reference, tick count versus actual traded volume.
- Establish Gold units/contract, FX spread/fees/rollover, BTC venue/spot/perpetual
  USDT basis and funding timestamps, and futures dated contracts/roll/adjustment,
  exchange sessions, tick value/multiplier and licensing. Corporate actions only
  where relevant to the actual product, not presumed for every symbol.
- PASS only if complete quality plus intended rights are verified. CONDITIONAL only
  after actual technical usability is established with named remaining limitations;
  FAIL for invalid/inadequate data. Pending/unread/unsupported is NOT EVALUATED.
- Freeze existing evaluated-period lineage, definitions and sealed holdout. No
  optimization, strategy run, terminal startup, broker/API call, forward feed or order.

The package is a bounded acquisition-audit starting point, not a complete automated
licensing/calendar/contract certifier. Publish aggregate evidence and exact remaining
gaps after actual inspection, never raw prices or a fabricated full-coverage claim.
