# Integration roadmap

Existing DCI research/paper components and local Git history remain intact.
No DAT, DPM, DSV, VMA/DAR, Pulse or OpenClaw production resources were modified.
Their existing patterns and the approved DAT Temporal Integration milestone are
external constraints, not assumed-accessible implementations.

1. Restore non-admin DirectiveCodex access and verify Windows ACL/isolation,
   Git state, Codex account mapping and prior certification evidence. Resolve
   REQUEST-0003 before Windows activation; no privilege/account changes here.
2. Restore GitHub integration write access (REQUEST-0002), preserve remote main
   history and certify one content commit plus remote read-back. Do not force-push
   the independent local root onto the existing remote root.
3. Certify Codex exec read-only on a supported writable runtime while retaining
   sandbox/approval protections; then review bounded patch task templates.
4. Review existing DSV and VMA/DAR routing contracts via read-only artifacts once
   supplied. Map identities and correlation IDs, never import execution credentials
   or accept conversational text as a command. DSV is optional, not required for
   Runner recovery or email delivery.
5. Select/certify an authenticated Brain boundary (REQUEST-0004). MCP tools plus
   MCP Events are supported candidates; prove actual ChatGPT task/result delivery
   with account isolation before activation. Otherwise implement the independent
   persistent Brain worker design with strategic ChatGPT review and separate
   explicit authorization for any paid API or persistent installation.
6. Independently certify WhatsApp/Pulse and email adapters against their exact
   authenticated principals, destination consent, provider ACK/idempotency,
   failures and expiry. Use separately authorized provider activation; no
   credentials are requested during simulation. Live approvals need an identity
   verification service, not a boolean field or delivery receipt.
7. Wrap bridge/workflows.py interfaces in Temporal activities and deterministic
   workflows. Preserve task/scope/idempotency across retries; external ambiguity
   routes to reconciliation. Keep production DAT Temporal milestone unchanged;
   no DAT service/namespace/credential changes are part of DCI work.
8. After review, prepare explicit deployment evidence and seek authorization for
   persistent-service installation. Until then use foreground one-shot simulated
   scheduling; no Windows scheduled tasks, services or external accounts.

Remaining safe work: offline task-scope/identity adapters, more replay fault
fixtures and read-only comparison of supplied non-secret integration artifacts.
