from __future__ import annotations

from dataclasses import dataclass

from quant_finance_os.core.events import FillEvent, MarketDataEvent, OrderEvent, Side


@dataclass(frozen=True)
class ExecutionConfig:
    slippage_bps: float = 1.0
    fill_ratio: float = 1.0
    fee_per_share: float = 0.0


class ExecutionSimulator:
    def __init__(self, config: ExecutionConfig | None = None) -> None:
        self.config = config or ExecutionConfig()

    def simulate_fill(self, order: OrderEvent, market: MarketDataEvent, seq: int) -> FillEvent | None:
        fill_qty = round(order.quantity * self.config.fill_ratio, 8)
        if fill_qty <= 0:
            return None

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
