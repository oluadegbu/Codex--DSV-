# Phase10 deployment review — NOT AN ACTIVATION PACKAGE

This self-contained ZIP contains the pinned embedded runtime, portable Git,
application, exact prospective Scheduled Task XML, review metadata, inactive
configuration example and rollback instructions. Nothing registers or starts a
Windows task. Extracting a ZIP is not approval to activate it.

Read DEPLOYMENT_REVIEW.json and STOP_AND_ROLLBACK.md. The XML's Enabled=true is the
proposed FINAL configuration, not a task registered on any machine. The native
Task Scheduler parsed it in memory; RegisterTaskDefinition and Run were never
called. Do not import it until the final configuration and package/task hashes
are explicitly approved and every preactivation gate passes.

The fixed entry verifies actual local DirectiveCodex SID, non-admin Medium token,
exact deployment directory, package hashes and a current-user DPAPI activation
grant binding source/manifest/task/pairing/evidence hashes and <=1h approval lease.
It requires real cancellation, owned-worker crash recovery and access-denial
receipts for this new source, then repeats the actual canary denial check. No
activation grant, remote endpoint or credentials are included. A config example
and historical0.1.3 receipt cannot satisfy the activation gate.

The Windows task credential would be enrolled through the supported Windows
interface after final approval. It is retained by Windows protected storage, not
plaintext files, arguments or repository content. S4U is deliberately not used:
DPAPI and network/provider authentication must work in the real non-interactive
Password logon context and remain uncertified until tested. No logon right is
assigned or changed automatically. Any missing batch-logon permission or denial
by policy blocks registration; it is not bypassed or fixed by elevation.

No existing successful or failed installation, pairing, journal or task is replaced.
The new worker state namespace is separate. Old source fingerprints and receipts
remain valid only for their original version. This new source requires its own
real Windows acceptance evidence before activation.
