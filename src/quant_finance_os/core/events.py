from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    MARKET_DATA = "market_data"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"
    POSITION = "position"
    PNL = "pnl"


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class BaseEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    seq: int = Field(ge=0)
    ts: datetime


class MarketDataEvent(BaseEvent):
    event_type: Literal[EventType.MARKET_DATA] = EventType.MARKET_DATA
    symbol: str
    price: float = Field(gt=0)
    volume: float = Field(ge=0)


class SignalEvent(BaseEvent):
    event_type: Literal[EventType.SIGNAL] = EventType.SIGNAL
    symbol: str
    strength: float = Field(ge=-1, le=1)


class OrderEvent(BaseEvent):
    event_type: Literal[EventType.ORDER] = EventType.ORDER
    order_id: str
    symbol: str
    side: Side
    quantity: float = Field(gt=0)


class FillEvent(BaseEvent):
    event_type: Literal[EventType.FILL] = EventType.FILL
    order_id: str
    symbol: str
    side: Side
    quantity: float = Field(gt=0)
    fill_price: float = Field(gt=0)
    fee: float = Field(ge=0)


class PositionEvent(BaseEvent):
    event_type: Literal[EventType.POSITION] = EventType.POSITION
    symbol: str
    quantity: float
    avg_price: float
    market_price: float = Field(gt=0)
    unrealized_pnl: float


class PnLEvent(BaseEvent):
    event_type: Literal[EventType.PNL] = EventType.PNL
    cash: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float


Event = MarketDataEvent | SignalEvent | OrderEvent | FillEvent | PositionEvent | PnLEvent
