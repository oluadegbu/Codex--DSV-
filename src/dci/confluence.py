from dataclasses import dataclass
from decimal import Decimal
from .models import Buy, unique_buys
from .research import WalletRegistry


@dataclass(frozen=True)
class Confluence:
    clusters: tuple[str, ...]
    wallets: tuple[str, ...]
    quality: Decimal
    events: tuple[str, ...]


def converge(buys: list[Buy], registry: WalletRegistry, token: str, as_of: int,
             window: int = 300, min_samples: int = 5, profile_max_age: int = 86400) -> Confluence:
    if min(as_of, window, min_samples, profile_max_age) < 0:
        raise ValueError("invalid convergence policy")
    representatives = {}
    seen = set()
    for buy in sorted(unique_buys(buys), key=lambda b: (b.timestamp, b.event_id)):
        if buy.event_id in seen or buy.token != token or not buy.finalized or not as_of - window <= buy.timestamp <= as_of:
            continue
        seen.add(buy.event_id)
        profile = registry.at(buy.wallet, as_of)
        if profile is None or not profile.cluster or profile.samples < min_samples or as_of - profile.as_of > profile_max_age:
            continue
        prior = representatives.get(profile.cluster)
        if prior is None or profile.quality > prior[0].quality:
            representatives[profile.cluster] = (profile, buy)
    values = [representatives[k] for k in sorted(representatives)]
    quality = sum((p.quality for p, _ in values), Decimal(0)) / len(values) if values else Decimal(0)
    return Confluence(tuple(sorted(representatives)), tuple(p.wallet for p, _ in values),
                      quality, tuple(b.event_id for _, b in values))
