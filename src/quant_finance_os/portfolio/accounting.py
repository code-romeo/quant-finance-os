from __future__ import annotations

from dataclasses import dataclass, field

from quant_finance_os.core.events import FillEvent, Side


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    average_price: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class PortfolioState:
    cash: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    equity: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)


class PortfolioLedger:
    def __init__(self, initial_cash: float) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        self.state = PortfolioState(cash=initial_cash, equity=initial_cash)

    def apply_fill(self, fill: FillEvent) -> tuple[Position, float]:
        signed_qty = fill.quantity if fill.side == Side.BUY else -fill.quantity
        position = self.state.positions.setdefault(fill.symbol, Position(symbol=fill.symbol))
        realized_delta = 0.0

        if position.quantity == 0 or (position.quantity > 0 and signed_qty > 0) or (position.quantity < 0 and signed_qty < 0):
            new_qty = position.quantity + signed_qty
            if new_qty != 0:
                existing_abs_qty = abs(position.quantity)
                added_abs_qty = abs(signed_qty)
                combined_notional = (position.average_price * existing_abs_qty) + (fill.fill_price * added_abs_qty)
                position.average_price = combined_notional / abs(new_qty)
            else:
                position.average_price = 0.0
            position.quantity = new_qty
        else:
            close_qty = min(abs(position.quantity), abs(signed_qty))
            if position.quantity > 0:
                realized_delta = (fill.fill_price - position.average_price) * close_qty
            else:
                realized_delta = (position.average_price - fill.fill_price) * close_qty

            remaining = position.quantity + signed_qty
            if remaining == 0:
                position.quantity = 0.0
                position.average_price = 0.0
            elif position.quantity > 0 and remaining < 0:
                position.quantity = remaining
                position.average_price = fill.fill_price
            elif position.quantity < 0 and remaining > 0:
                position.quantity = remaining
                position.average_price = fill.fill_price
            else:
                position.quantity = remaining

        trade_cash = fill.fill_price * fill.quantity
        self.state.cash += -trade_cash if fill.side == Side.BUY else trade_cash
        self.state.cash -= fill.fee
        position.realized_pnl += realized_delta
        self.state.realized_pnl += realized_delta
        return position, realized_delta

    def mark_to_market(self, prices: dict[str, float]) -> PortfolioState:
        unrealized = 0.0
        inventory_value = 0.0
        for symbol, position in self.state.positions.items():
            if position.quantity == 0:
                continue
            if symbol not in prices:
                raise ValueError(f"missing mark price for symbol '{symbol}'")
            mark = prices[symbol]
            inventory_value += position.quantity * mark
            unrealized += (mark - position.average_price) * position.quantity

        self.state.unrealized_pnl = unrealized
        self.state.equity = self.state.cash + inventory_value
        return self.state
