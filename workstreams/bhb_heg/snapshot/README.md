# BHB/HEG isolated DMB shadow worker

This bounded workstream tests the supplied DCI source snapshot from commit
`7564365`. It does not modify the original DCI repository, other workers, or any
Directive production service. The worker runs as non-root Linux `agent` uid 1000;
this evidence does not certify Windows DirectiveCodex identity.

Run `PYTHONPATH=src python -m unittest discover -s tests -v` from this workspace.
Tests use temporary local SQLite mailboxes and explicit simulated timestamps.
They cover expiry, correlated reporting, approval denial, uncertain restart,
route and replay rejection, persistent PAUSE, and notification fallback/timeout.
WhatsApp and email are in-process simulations. No notification can grant an
approval. No provider, credentials, Codex execution, service installation,
network calls, signing, orders, trading, or funds movement is involved.

`WORKER_REPORT.json` records actual results, identity, source hashes and Git
provenance. The snapshot's CODEX.md mentions main-repository documentation not
included in this worker; this worker follows the parent-provided bounded scope
and does not claim full production or live interface certification.
