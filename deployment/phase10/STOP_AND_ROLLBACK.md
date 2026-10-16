# Shutdown and rollback — only after final approved installation

No rollback command is executed by this package.

Normal shutdown: create the fixed `STOP` file in current-user LocalAppData under
`Directive/DMBWindowsWorker-ops-0.2.0-review1`. The wrapper stops accepting new polls
and drains the current bounded task. It does not remove the STOP marker on restart.
Check the lifecycle journal and owned processes before removing any block.

The Task Scheduler hard ceiling is1h2m; the worker's own acceptance lease is at most
1h. A forced task/process stop closes this process's non-inherited owned Codex Job
Object handles, whose kill-on-close setting terminates its children. The next
startup reconciles the durable worker journal; an incomplete started task is
UNCERTAIN/NEEDS_HUMAN and is never re-executed automatically. Real Windows forced
shutdown/recovery remains a preactivation test gate, not an inferred PASS.

Following approval, rollback disables and unregisters ONLY
`\Directive.DMB.ShadowWorker.Phase10`, using the supported Windows Task Scheduler
interface. It leaves the versioned package, STOP marker, activation/worker DPAPI
files, lifecycle journal, task/worker journals and audit receipts intact for review.
It never deletes a folder, resets a database, replaces pairing, touches any other
task/service, alters ACL/firewall/logon rights or changes production configuration.
Windows removes its own task-associated protected credential when unregistering;
the package never reads or exports that stored credential.

If normal drain cannot complete, retain the blocked task and evidence. A supported
Task Scheduler Stop of this exact task is the emergency limit; do not kill by an
unverified PID or reuse the worker with new pairing to evade quarantine.
