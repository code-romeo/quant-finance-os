from __future__ import annotations

from dataclasses import dataclass

from quant_finance_os.core.events import FillEvent, Side


@dataclass(frozen=True)
class AttributionReport:
    notional_flow_by_symbol: dict[str, float]
    notes: str


class AttributionEngine:
    def from_fills(self, fills: list[FillEvent]) -> AttributionReport:
        contributions: dict[str, float] = {}
        for fill in fills:
            signed_notional = fill.fill_price * fill.quantity * (1 if fill.side == Side.SELL else -1)
            contributions[fill.symbol] = contributions.get(fill.symbol, 0.0) + signed_notional
        return AttributionReport(
            notional_flow_by_symbol=contributions,
            notes="First-pass attribution by signed traded notional flow; replace with return or factor attribution in later iterations.",
        )
