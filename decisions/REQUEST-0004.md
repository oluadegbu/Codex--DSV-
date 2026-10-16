# REQUEST-0004: Live Brain and HEG authentication/deployment boundary
STATUS: OPEN

## CONTEXT
Local shadow Brain tools and HEG work without external providers. A live connection
needs an independently certified identity/transport and explicit deployment scope.

## EVIDENCE
Official MCP tools and MCP Events offer supported task/result candidates. No
DCI ChatGPT plugin subscription, authenticated endpoint, webhook or live HEG
identity/provider has been connected. SimulationSession is a synthetic identity
fixture, not authentication. Codex/GitHub/Windows live gates are also blocked.

## OPTIONS
1. Authenticated MCP tool/event endpoint with independently certified notifications.
2. Independent persistent Brain worker with ChatGPT as strategic reviewer.
3. Retain local shadow prototype until operational identity evidence is supplied.

## RECOMMENDATION
Keep option 3 operationally; review option 1 and fallback option 2 against the
existing non-secret DSV/VMA/DAR integration artifacts. Approve exact endpoints,
identity mapping, provider/destination consent and persistence scope separately.
Do not assume an ordinary conversation can poll files or self-wake.

## IMPACT
Blocks live ChatGPT bidirectional delivery, production approval authentication,
external WhatsApp/Pulse/email activation and persistent service installation.
Does not block further offline tests, adapters or documentation.
BLOCKING: YES
HARD_GATE: YES

## SUPERVISOR RESPONSE
Pending. No providers, accounts, credentials or services requested or activated.
