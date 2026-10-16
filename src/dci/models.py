import json
from dataclasses import dataclass
from decimal import Decimal


def unit(value: Decimal) -> Decimal:
    if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
        raise ValueError("feature must be finite and in [0, 1]")
    return value


def positive(value: Decimal) -> Decimal:
    if not value.is_finite() or value <= 0:
        raise ValueError("value must be finite and positive")
    return value


@dataclass(frozen=True)
class Buy:
    signature: str
    instruction: int
    wallet: str
    token: str
    timestamp: int
    slot: int
    price: Decimal
    finalized: bool = True

    def __post_init__(self):
        positive(self.price)
        if type(self.finalized) is not bool:
            raise ValueError("finalized must be a boolean")
        if not all((self.signature, self.wallet, self.token)) or min(self.instruction, self.timestamp, self.slot) < 0:
            raise ValueError("invalid buy identity or time")

    @property
    def event_id(self) -> str:
        return json.dumps([self.signature, self.instruction, self.wallet, self.token], separators=(",", ":"))


@dataclass(frozen=True)
class WalletProfile:
    wallet: str
    cluster: str | None
    quality: Decimal
    samples: int
    as_of: int

    def __post_init__(self):
        unit(self.quality)
        if self.samples < 0 or self.as_of < 0 or not self.wallet:
            raise ValueError("invalid profile")


@dataclass(frozen=True)
class RiskEvidence:
    token: str
    as_of: int
    mint_authority_revoked: bool | None
    freeze_authority_revoked: bool | None
    liquidity_verified: bool | None
    safety: Decimal
    liquidity: Decimal

    def __post_init__(self):
        unit(self.safety)
        unit(self.liquidity)
        if self.as_of < 0 or not self.token:
            raise ValueError("invalid risk evidence")


@dataclass(frozen=True)
class Opportunity:
    token: str
    as_of: int
    score: Decimal
    eligible: bool
    reasons: tuple[str, ...]
    features: dict[str, Decimal]
    events: tuple[str, ...]
    config_version: str


def unique_buys(buys: list[Buy]) -> list[Buy]:
    unique = {}
    for buy in buys:
        if buy.event_id in unique and unique[buy.event_id] != buy:
            raise ValueError("conflicting payload for buy event identity")
        unique[buy.event_id] = buy
    return list(unique.values())
