from __future__ import annotations

from dataclasses import dataclass

from quant_finance_os.core.events import FillEvent, MarketDataEvent, OrderEvent, Side


@dataclass(frozen=True)
class ExecutionConfig:
    slippage_bps: float = 1.0
    fill_ratio: float = 1.0
    fee_per_share: float = 0.0
    min_fill_quantity: float = 1e-8

    def __post_init__(self) -> None:
        if self.slippage_bps < 0:
            raise ValueError("slippage_bps must be non-negative")
        if not 0 <= self.fill_ratio <= 1:
            raise ValueError("fill_ratio must be between 0 and 1")
        if self.fee_per_share < 0:
            raise ValueError("fee_per_share must be non-negative")
        if self.min_fill_quantity <= 0:
            raise ValueError("min_fill_quantity must be positive")


class ExecutionSimulator:
    def __init__(self, config: ExecutionConfig | None = None) -> None:
        self.config = config or ExecutionConfig()

    def simulate_fill(self, order: OrderEvent, market: MarketDataEvent, seq: int) -> FillEvent | None:
        raw_fill_qty = order.quantity * self.config.fill_ratio
        if raw_fill_qty < self.config.min_fill_quantity:
            return None
        fill_qty = round(raw_fill_qty, 8)

        slip = self.config.slippage_bps / 10_000
        price = market.price * (1 + slip if order.side == Side.BUY else 1 - slip)
        fee = fill_qty * self.config.fee_per_share

        return FillEvent(
            event_id=f"fill:{seq}:{order.order_id}",
            seq=seq,
            ts=market.ts,
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=fill_qty,
            fill_price=price,
            fee=fee,
        )
