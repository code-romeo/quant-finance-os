from __future__ import annotations

from datetime import datetime, timezone

from quant_finance_os.backtest import BacktestEngine
from quant_finance_os.core import MarketDataEvent, OrderEvent, Side


class BuyDipStrategy:
    def __init__(self) -> None:
        self.in_position = False

    def on_market_data(self, event: MarketDataEvent, portfolio):
        if not self.in_position and event.price <= 100:
            self.in_position = True
            return [
                OrderEvent(
                    event_id="input-order",
                    seq=event.seq,
                    ts=event.ts,
                    order_id=f"order-{event.seq}",
                    symbol=event.symbol,
                    side=Side.BUY,
                    quantity=10,
                )
            ]
        return []


if __name__ == "__main__":
    prices = [101, 100, 102]
    events = [
        MarketDataEvent(
            event_id=f"in-{i}",
            seq=i,
            ts=datetime(2024, 1, 1, 0, i, tzinfo=timezone.utc),
            symbol="AAPL",
            price=price,
            volume=1_000,
        )
        for i, price in enumerate(prices)
    ]

    result = BacktestEngine(strategy=BuyDipStrategy(), initial_cash=10_000).run(events)
    for event in result.events:
        print(event)
