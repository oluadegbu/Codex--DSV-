"""Fixture discovery and point-in-time wallet registry contracts."""
from decimal import Decimal
from .models import Buy, WalletProfile, unit, unique_buys


class FixtureDiscovery:
    def __init__(self, buys: list[Buy]):
        self.buys = buys

    def early_buyers(self, token: str, launch: int, cutoff: int) -> list[Buy]:
        if launch > cutoff:
            raise ValueError("invalid discovery interval")
        unique = [b for b in unique_buys(self.buys) if b.token == token and b.finalized and launch <= b.timestamp <= cutoff]
        return sorted(unique, key=lambda b: (b.timestamp, b.slot, b.event_id))


class WalletRegistry:
    def __init__(self):
        self.history: dict[str, list[WalletProfile]] = {}

    def register(self, profile: WalletProfile):
        history = self.history.setdefault(profile.wallet, [])
        if any(p.as_of == profile.as_of for p in history):
            raise ValueError("profile timestamp already exists")
        history.append(profile)

    def at(self, wallet: str, as_of: int) -> WalletProfile | None:
        available = [p for p in self.history.get(wallet, []) if p.as_of <= as_of]
        return max(available, key=lambda p: p.as_of, default=None)

    def recalibrate(self, wallet: str, outcomes: list[Decimal], as_of: int) -> WalletProfile:
        # Experimental bounded hit-rate posterior: beta(1,1). No automatic strategy
        # promotion; only finalized measured outcomes from a separate cohort belong here.
        previous = self.at(wallet, as_of)
        if previous is None or not outcomes:
            raise ValueError("profile and outcome cohort required")
        for outcome in outcomes:
            unit(outcome)
        profile = WalletProfile(wallet, previous.cluster,
                                (sum(outcomes, Decimal(0)) + 1) / (len(outcomes) + 2),
                                len(outcomes), as_of)
        self.register(profile)
        return profile
