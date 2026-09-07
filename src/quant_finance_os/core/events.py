from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class ReplayMetadata:
    run_id: str = ""
    seq: int = 0
    event_id: str = ""
    parent_event_id: str | None = None


@dataclass(frozen=True)
class EventBase:
    timestamp: datetime
    metadata: ReplayMetadata = ReplayMetadata()


@dataclass(frozen=True)
class MarketEvent(EventBase):
    symbol: str = ""
    price: float = 0.0
    volume: float = 0.0

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("MarketEvent.symbol must be non-empty")
        if self.price <= 0:
            raise ValueError("MarketEvent.price must be positive")
        if self.volume < 0:
            raise ValueError("MarketEvent.volume must be non-negative")


@dataclass(frozen=True)
class SignalEvent(EventBase):
    symbol: str = ""
    side: Side = Side.BUY
    quantity: float = 0.0
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("SignalEvent.symbol must be non-empty")
        if self.quantity <= 0:
            raise ValueError("SignalEvent.quantity must be positive")


@dataclass(frozen=True)
class OrderEvent(EventBase):
    order_id: str = ""
    symbol: str = ""
    side: Side = Side.BUY
    quantity: float = 0.0
    limit_price: float | None = None

    def __post_init__(self) -> None:
        if not self.order_id:
            raise ValueError("OrderEvent.order_id must be non-empty")
        if not self.symbol:
            raise ValueError("OrderEvent.symbol must be non-empty")
        if self.quantity <= 0:
            raise ValueError("OrderEvent.quantity must be positive")
        if self.limit_price is not None and self.limit_price <= 0:
            raise ValueError("OrderEvent.limit_price must be positive when set")


@dataclass(frozen=True)
class FillEvent(EventBase):
    order_id: str = ""
    symbol: str = ""
    side: Side = Side.BUY
    quantity: float = 0.0
    fill_price: float = 0.0
    fee: float = 0.0

    def __post_init__(self) -> None:
        if not self.order_id:
            raise ValueError("FillEvent.order_id must be non-empty")
        if not self.symbol:
            raise ValueError("FillEvent.symbol must be non-empty")
        if self.quantity <= 0:
            raise ValueError("FillEvent.quantity must be positive")
        if self.fill_price <= 0:
            raise ValueError("FillEvent.fill_price must be positive")


@dataclass(frozen=True)
class PositionUpdateEvent(EventBase):
    symbol: str = ""
    quantity: float = 0.0
    average_price: float = 0.0


@dataclass(frozen=True)
class PnLEvent(EventBase):
    symbol: str = ""
    realized_delta: float = 0.0
    unrealized_delta: float = 0.0
    total_realized: float = 0.0
    total_unrealized: float = 0.0
    cash: float = 0.0
    equity: float = 0.0


def with_metadata(event: EventBase, metadata: ReplayMetadata) -> EventBase:
    return replace(event, metadata=metadata)
