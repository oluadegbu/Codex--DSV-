"""Synthetic USD ledger only; no execution adapter exists."""
from dataclasses import dataclass
from decimal import Decimal
from .models import Opportunity, positive, unit


@dataclass
class Position:
    token: str
    units: Decimal
    cost: Decimal
    opened_at: int
    last_at: int
    entry: Decimal
    pnl: Decimal | None = None
    closed_at: int | None = None


class ShadowBook:
    def __init__(self, cash: Decimal = Decimal("1000"), size: Decimal = Decimal("100"),
                 friction: Decimal = Decimal(".003"), max_positions: int = 3):
        positive(cash)
        positive(size)
        unit(friction)
        if friction >= Decimal(1) or max_positions < 1 or size > cash:
            raise ValueError("invalid shadow limits")
        self.cash, self.size, self.friction = cash, size, friction
        self.max_positions = max_positions
        self.positions: dict[str, Position] = {}
        self.audit: list[dict] = []

    def enter(self, opportunity: Opportunity, price: Decimal) -> Position:
        positive(price)
        if not opportunity.eligible or opportunity.token in self.positions:
            raise ValueError("ineligible or repeated entry")
        if sum(p.closed_at is None for p in self.positions.values()) >= self.max_positions or self.cash < self.size:
            raise ValueError("shadow exposure limit")
        entry = price * (1 + self.friction)
        position = Position(opportunity.token, self.size / entry, self.size,
                            opportunity.as_of, opportunity.as_of, entry)
        self.cash -= self.size
        self.positions[position.token] = position
        self.audit.append({"type": "paper_entry", "token": position.token, "at": opportunity.as_of,
                           "score": str(opportunity.score), "events": opportunity.events, "config": opportunity.config_version})
        return position

    def mark(self, token: str, price: Decimal, at: int, force_exit: bool = False) -> Position:
        positive(price)
        position = self.positions[token]
        if position.closed_at is not None or at < position.last_at:
            raise ValueError("closed position or out-of-order mark")
        position.last_at = at
        proceeds = position.units * price * (1 - self.friction)
        position.pnl = proceeds - position.cost
        ratio = proceeds / position.cost
        if force_exit or ratio <= Decimal(".80") or ratio >= Decimal("1.50") or at - position.opened_at >= 3600:
            position.closed_at = at
            self.cash += proceeds
            self.audit.append({"type": "paper_exit", "token": token, "at": at, "pnl": str(position.pnl)})
        else:
            self.audit.append({"type": "paper_mark", "token": token, "at": at, "pnl": str(position.pnl)})
        return position
