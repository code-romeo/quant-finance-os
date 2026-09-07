from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from quant_finance_os.backtest.accounting import Portfolio
from quant_finance_os.backtest.execution import ExecutionSimulator
from quant_finance_os.core.events import Event, MarketDataEvent, OrderEvent


class Strategy(Protocol):
    def on_market_data(self, event: MarketDataEvent, portfolio: Portfolio) -> list[OrderEvent]: ...


@dataclass
class BacktestResult:
    events: list[Event]


class BacktestEngine:
    def __init__(self, strategy: Strategy, initial_cash: float, execution: ExecutionSimulator | None = None) -> None:
        self.strategy = strategy
        self.execution = execution or ExecutionSimulator()
        self.portfolio = Portfolio(initial_cash=initial_cash)

    def run(self, market_events: list[MarketDataEvent]) -> BacktestResult:
        events: list[Event] = []
        prices: dict[str, float] = {}
        seq = 0

        for idx, market in enumerate(market_events):
            if idx > 0:
                prev = market_events[idx - 1]
                if (market.ts, market.seq, market.event_id) < (prev.ts, prev.seq, prev.event_id):
                    raise ValueError("market_events must be pre-ordered for deterministic replay")
            seq += 1
            prices[market.symbol] = market.price
            normalized_market = market.model_copy(update={"seq": seq, "event_id": f"mkt:{seq}"})
            events.append(normalized_market)

            orders = self.strategy.on_market_data(normalized_market, self.portfolio)
            for idx, order in enumerate(orders, start=1):
                seq += 1
                placed = order.model_copy(
                    update={"seq": seq, "event_id": f"ord:{seq}:{idx}", "ts": normalized_market.ts}
                )
                events.append(placed)

                next_fill_seq = seq + 1
                fill = self.execution.simulate_fill(placed, normalized_market, seq=next_fill_seq)
                if fill is None:
                    continue
                seq = next_fill_seq
                events.append(fill)
                seq += 1
                events.append(self.portfolio.apply_fill(fill, seq=seq))

            seq += 1
            pnl_ts = normalized_market.ts + timedelta(microseconds=1)
            events.append(self.portfolio.mark_to_market(seq=seq, ts=pnl_ts, prices=prices))

        return BacktestResult(events=events)
