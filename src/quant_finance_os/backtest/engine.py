from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

from quant_finance_os.core.events import (
    FillEvent,
    MarketEvent,
    OrderEvent,
    PnLEvent,
    PositionUpdateEvent,
    ReplayMetadata,
    SignalEvent,
    Side,
    with_metadata,
)
from quant_finance_os.portfolio.accounting import PortfolioLedger


class Strategy(Protocol):
    def on_market_event(self, event: MarketEvent, ledger: PortfolioLedger) -> Iterable[SignalEvent]:
        ...


class SlippageModel(Protocol):
    def apply(self, side: Side, market_price: float) -> float:
        ...


class FillModel(Protocol):
    def fill_order(
        self,
        order: OrderEvent,
        market_event: MarketEvent,
        slippage_model: SlippageModel,
    ) -> FillEvent | None:
        ...


@dataclass(frozen=True)
class ConstantBpsSlippage:
    bps: float = 0.0

    def apply(self, side: Side, market_price: float) -> float:
        if self.bps < 0:
            raise ValueError("bps must be non-negative")
        offset = market_price * (self.bps / 10_000)
        return market_price + offset if side == Side.BUY else market_price - offset


class ImmediateFillModel:
    def __init__(self, fee_bps: float = 0.0) -> None:
        self._fee_bps = fee_bps

    def fill_order(self, order: OrderEvent, market_event: MarketEvent, slippage_model: SlippageModel) -> FillEvent:
        fill_price = slippage_model.apply(order.side, market_event.price)
        fee = fill_price * order.quantity * (self._fee_bps / 10_000)
        return FillEvent(
            timestamp=market_event.timestamp,
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            fee=fee,
        )


@dataclass
class BacktestResult:
    events: list
    final_cash: float
    final_equity: float
    realized_pnl: float
    unrealized_pnl: float


class BacktestEngine:
    def __init__(
        self,
        strategy: Strategy,
        initial_cash: float,
        slippage_model: SlippageModel | None = None,
        fill_model: FillModel | None = None,
        run_id: str = "backtest",
    ) -> None:
        self._strategy = strategy
        self._initial_cash = initial_cash
        self._ledger = PortfolioLedger(initial_cash=initial_cash)
        self._slippage_model = slippage_model or ConstantBpsSlippage()
        self._fill_model = fill_model or ImmediateFillModel()
        self._run_id = run_id
        self._seq = 0

    def _next_metadata(self, parent_event_id: str | None = None) -> ReplayMetadata:
        self._seq += 1
        return ReplayMetadata(
            run_id=self._run_id,
            seq=self._seq,
            event_id=f"evt-{self._seq:010d}",
            parent_event_id=parent_event_id,
        )

    def _normalize(self, event, parent_event_id: str | None = None):
        return with_metadata(event, self._next_metadata(parent_event_id))

    def run(self, market_events: Iterable[MarketEvent]) -> BacktestResult:
        self._ledger = PortfolioLedger(initial_cash=self._initial_cash)
        self._seq = 0
        output_events: list = []
        latest_timestamp: datetime | None = None
        prices: dict[str, float] = {}

        for raw_market_event in market_events:
            if latest_timestamp and raw_market_event.timestamp < latest_timestamp:
                raise ValueError("market_events must be ordered by non-decreasing timestamp")
            latest_timestamp = raw_market_event.timestamp

            market_event = self._normalize(raw_market_event)
            output_events.append(market_event)
            prices[market_event.symbol] = market_event.price

            self._ledger.mark_to_market(prices)

            signals = tuple(self._strategy.on_market_event(market_event, self._ledger))
            for signal in signals:
                normalized_signal = self._normalize(signal, parent_event_id=market_event.metadata.event_id)
                output_events.append(normalized_signal)

                order = OrderEvent(
                    timestamp=market_event.timestamp,
                    order_id=f"ord-{normalized_signal.metadata.seq:010d}",
                    symbol=normalized_signal.symbol,
                    side=normalized_signal.side,
                    quantity=normalized_signal.quantity,
                    limit_price=None,
                )
                normalized_order = self._normalize(order, parent_event_id=normalized_signal.metadata.event_id)
                output_events.append(normalized_order)

                fill = self._fill_model.fill_order(normalized_order, raw_market_event, self._slippage_model)
                if fill is None:
                    continue

                normalized_fill = self._normalize(fill, parent_event_id=normalized_order.metadata.event_id)
                output_events.append(normalized_fill)

                position, realized_delta = self._ledger.apply_fill(normalized_fill)
                marked_state = self._ledger.mark_to_market(prices)

                position_event = self._normalize(
                    PositionUpdateEvent(
                        timestamp=market_event.timestamp,
                        symbol=position.symbol,
                        quantity=position.quantity,
                        average_price=position.average_price,
                    ),
                    parent_event_id=normalized_fill.metadata.event_id,
                )
                output_events.append(position_event)

                pnl_event = self._normalize(
                    PnLEvent(
                        timestamp=market_event.timestamp,
                        symbol=position.symbol,
                        realized_delta=realized_delta,
                        unrealized_delta=0.0,
                        total_realized=marked_state.realized_pnl,
                        total_unrealized=marked_state.unrealized_pnl,
                        cash=marked_state.cash,
                        equity=marked_state.equity,
                    ),
                    parent_event_id=position_event.metadata.event_id,
                )
                output_events.append(pnl_event)

        final_state = self._ledger.state
        return BacktestResult(
            events=output_events,
            final_cash=final_state.cash,
            final_equity=final_state.equity,
            realized_pnl=final_state.realized_pnl,
            unrealized_pnl=final_state.unrealized_pnl,
        )
