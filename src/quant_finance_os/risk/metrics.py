from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Exposure:
    gross: float
    net: float


def calculate_exposure(positions: dict[str, float], prices: dict[str, float]) -> Exposure:
    gross = 0.0
    net = 0.0
    for symbol, qty in positions.items():
        if symbol not in prices:
            raise ValueError(f"missing price for symbol '{symbol}'")
        value = qty * prices[symbol]
        gross += abs(value)
        net += value
    return Exposure(gross=gross, net=net)


def max_drawdown(equity_curve: list[float]) -> float:
    if len(equity_curve) < 2:
        raise ValueError("equity_curve must contain at least two points")
    if any(point <= 0 for point in equity_curve):
        raise ValueError("equity_curve values must be strictly positive for drawdown calculation")

    peak = equity_curve[0]
    max_dd = 0.0
    for point in equity_curve[1:]:
        if point > peak:
            peak = point
        dd = (peak - point) / peak if peak != 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd
