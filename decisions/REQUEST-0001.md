# REQUEST-0001: Research cohort and validation target
STATUS: OPEN

## CONTEXT
A fixture pipeline can be built safely now. Real historical discovery and scoring
validation need an agreed cohort, evaluation period and success criteria.

## EVIDENCE
Selecting only high-performing tokens creates survivorship bias. RPC history may
be pruned, and raw transfers do not reliably identify DEX buys. No approved real
cohort, labelled outcome horizon, live feature definition or independence model
has been supplied. Fixture profiles and normalized inputs are synthetic.

## OPTIONS
1. Public historical winners plus matched dead/failed controls, split by time.
2. Prospective public read-only shadow collection, with delayed outcome labels.
3. Paid archival/indexed provider (separate purchase authorization required).

## RECOMMENDATION
Combine 1 and 2 once the supervisor specifies launch date range, token universe,
return/liquidity eligibility, outcome horizons and false-positive tolerance.
Keep weights versioned; compare against simple baselines on a temporal holdout.

## IMPACT
Blocks claims of empirical strategy validation and a real data cohort implementation.
Does not block durable replay, schemas, adapter tests or standalone shadow tooling.
BLOCKING: NO
HARD_GATE: NO

## SUPERVISOR RESPONSE
Pending; no approval inferred. Paid purchases remain separately hard-gated.
