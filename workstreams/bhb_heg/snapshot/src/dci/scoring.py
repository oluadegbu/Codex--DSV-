from dataclasses import dataclass, field
from decimal import Decimal
from .confluence import Confluence
from .models import Opportunity, RiskEvidence, unit


FEATURES = ("wallet_quality", "convergence", "entry_timing", "token_safety", "liquidity", "momentum")


@dataclass(frozen=True)
class ScoreConfig:
    version: str = "hypothesis-v1"
    weights: tuple[Decimal, ...] = field(default_factory=lambda: tuple(map(Decimal, (".25", ".20", ".15", ".20", ".10", ".10"))))
    threshold: Decimal = Decimal(".70")
    min_clusters: int = 2
    risk_max_age: int = 60

    def __post_init__(self):
        if len(self.weights) != 6 or sum(self.weights) != 1:
            raise ValueError("weights must sum to one")
        for weight in self.weights:
            unit(weight)
        unit(self.threshold)
        if self.min_clusters < 2 or self.risk_max_age < 0:
            raise ValueError("invalid research policy")


def assess(token: str, as_of: int, confluence: Confluence, risk: RiskEvidence | None,
           timing: Decimal, momentum: Decimal, config: ScoreConfig = ScoreConfig()) -> Opportunity:
    unit(timing)
    unit(momentum)
    reasons = []
    if len(confluence.clusters) < config.min_clusters:
        reasons.append("insufficient_independent_wallets")
    valid_risk = risk is not None and risk.token == token and 0 <= as_of - risk.as_of <= config.risk_max_age
    if not valid_risk:
        reasons.append("missing_or_stale_risk")
    elif not all(v is True for v in (risk.mint_authority_revoked, risk.freeze_authority_revoked, risk.liquidity_verified)):
        reasons.append("unsafe_or_unknown_token")
    features = dict(zip(FEATURES, (confluence.quality, min(Decimal(len(confluence.clusters)) / 3, Decimal(1)), timing,
                                  risk.safety if valid_risk else Decimal(0),
                                  risk.liquidity if valid_risk else Decimal(0), momentum)))
    for value in features.values():
        unit(value)
    score = sum((features[name] * weight for name, weight in zip(FEATURES, config.weights)), Decimal(0))
    if score < config.threshold:
        reasons.append("below_research_threshold")
    return Opportunity(token, as_of, score, not reasons, tuple(reasons), features, confluence.events, config.version)
