from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from quant_finance_os.core.events import FillEvent, PnLEvent, PositionEvent, Side


@dataclass
class PositionState:
    quantity: float = 0.0
    avg_price: float = 0.0


class Portfolio:
    def __init__(self, initial_cash: float) -> None:
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.realized_pnl = 0.0
        self.positions: dict[str, PositionState] = {}

    def apply_fill(self, fill: FillEvent, seq: int | None = None) -> PositionEvent:
        qty = fill.quantity if fill.side == Side.BUY else -fill.quantity
        state = self.positions.setdefault(fill.symbol, PositionState())
        self.realized_pnl -= fill.fee

        prev_qty = state.quantity
        new_qty = prev_qty + qty

        if fill.side == Side.BUY:
            self.cash -= fill.fill_price * fill.quantity + fill.fee
        else:
            self.cash += fill.fill_price * fill.quantity - fill.fee

        if prev_qty == 0 or prev_qty * qty > 0:
            total_abs = abs(prev_qty) + abs(qty)
            state.avg_price = (
                (state.avg_price * abs(prev_qty) + fill.fill_price * abs(qty)) / total_abs
                if total_abs
                else 0.0
            )
            if new_qty == 0:
                state.avg_price = 0.0
        else:
            closed = min(abs(prev_qty), abs(qty))
            direction = 1.0 if prev_qty > 0 else -1.0
            self.realized_pnl += direction * closed * (fill.fill_price - state.avg_price)
            if new_qty == 0:
                state.avg_price = 0.0
            elif prev_qty * new_qty < 0:
                state.avg_price = fill.fill_price

        state.quantity = new_qty
        if new_qty == 0:
            self.positions.pop(fill.symbol, None)
        event_seq = seq if seq is not None else fill.seq

        return PositionEvent(
            event_id=f"pos:{event_seq}:{fill.symbol}",
            seq=event_seq,
            ts=fill.ts,
            symbol=fill.symbol,
            quantity=state.quantity,
            avg_price=state.avg_price,
            market_price=fill.fill_price,
            unrealized_pnl=state.quantity * (fill.fill_price - state.avg_price),
        )

    def mark_to_market(self, seq: int, ts: datetime, prices: dict[str, float]) -> PnLEvent:
        market_value = 0.0
        unrealized = 0.0
        for symbol, state in self.positions.items():
            price = prices.get(symbol)
            if price is None:
                price = state.avg_price
            market_value += state.quantity * price
            unrealized += state.quantity * (price - state.avg_price)

        return PnLEvent(
            event_id=f"pnl:{seq}",
            seq=seq,
            ts=ts,
            cash=self.cash,
            equity=self.cash + market_value,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=unrealized,
        )
