import json
from decimal import Decimal
from pathlib import Path
from .confluence import converge
from .models import Buy, RiskEvidence, WalletProfile
from .research import FixtureDiscovery, WalletRegistry
from .scoring import assess
from .shadow import ShadowBook
from .journal import DurableShadowBook


def run_fixture(path: str | Path, journal: str | Path | None = None) -> dict:
    data = json.loads(Path(path).read_text())
    registry = WalletRegistry()
    for profile in data["profiles"]:
        registry.register(WalletProfile(**{**profile, "quality": Decimal(profile["quality"])}))
    buys = [Buy(**{**buy, "price": Decimal(buy["price"])}) for buy in data["buys"]]
    discovered = FixtureDiscovery(buys).early_buyers(data["token"], data["launch"], data["as_of"])
    confluence = converge(discovered, registry, data["token"], data["as_of"])
    raw = data["risk"]
    risk = RiskEvidence(**{**raw, "safety": Decimal(raw["safety"]), "liquidity": Decimal(raw["liquidity"])})
    opportunity = assess(data["token"], data["as_of"], confluence, risk,
                         Decimal(data["timing"]), Decimal(data["momentum"]))
    book = DurableShadowBook(journal) if journal is not None else ShadowBook()
    try:
        if opportunity.eligible:
            book.enter(opportunity, Decimal(data["entry_price"]))
            for mark in data["marks"]:
                book.mark(data["token"], Decimal(mark["price"]), mark["at"])
        return {"mode": "SHADOW", "synthetic": True, "token": data["token"], "score": str(opportunity.score),
                "eligible": opportunity.eligible, "reasons": opportunity.reasons,
                "clusters": confluence.clusters, "cash": str(book.cash), "audit": book.audit,
                "config": opportunity.config_version}
    finally:
        if isinstance(book, DurableShadowBook):
            book.close()
