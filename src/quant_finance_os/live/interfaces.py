from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from quant_finance_os.core.events import MarketEvent, OrderEvent


class MarketDataFeed(Protocol):
    def next_event(self) -> MarketEvent | None:
        ...


class ExecutionAdapter(Protocol):
    def submit_order(self, order: OrderEvent) -> str:
        ...


@dataclass
class ShadowDecision:
    backtest_order: OrderEvent
    live_ack_id: str | None


class ShadowTrader:
    def __init__(self, execution_adapter: ExecutionAdapter) -> None:
        self._execution_adapter = execution_adapter

    def mirror_order(self, order: OrderEvent, send_live: bool = False) -> ShadowDecision:
        ack = self._execution_adapter.submit_order(order) if send_live else None
        return ShadowDecision(backtest_order=order, live_ack_id=ack)
