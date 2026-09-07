from datetime import datetime, timezone

import pytest

from quant_finance_os.backtest import BacktestEngine, ExecutionConfig, ExecutionSimulator
from quant_finance_os.core import MarketDataEvent, OrderEvent, Side


class OneShotLongStrategy:
    def __init__(self):
        self.sent = False

    def on_market_data(self, event, portfolio):
        if self.sent:
            return []
        self.sent = True
        return [
            OrderEvent(
                event_id="strategy-order",
                seq=event.seq,
                ts=event.ts,
                order_id="ord-1",
                symbol=event.symbol,
                side=Side.BUY,
                quantity=2,
            )
        ]


class StaleTimestampOrderStrategy:
    def on_market_data(self, event, portfolio):
        return [
            OrderEvent(
                event_id="stale-order",
                seq=0,
                ts=datetime(2000, 1, 1, tzinfo=timezone.utc),
                order_id="ord-stale",
                symbol=event.symbol,
                side=Side.BUY,
                quantity=1,
            )
        ]


def build_market_events():
    prices = [100.0, 101.0, 102.0]
    return [
        MarketDataEvent(
            event_id=f"m{i}",
            seq=i,
            ts=datetime(2024, 1, 1, 0, i, tzinfo=timezone.utc),
            symbol="AAPL",
            price=p,
            volume=1000,
        )
        for i, p in enumerate(prices)
    ]


def test_backtest_replay_is_deterministic():
    config = ExecutionConfig(slippage_bps=5, fill_ratio=1.0, fee_per_share=0.01)

    result_1 = BacktestEngine(
        strategy=OneShotLongStrategy(),
        initial_cash=1_000,
        execution=ExecutionSimulator(config),
    ).run(build_market_events())

    result_2 = BacktestEngine(
        strategy=OneShotLongStrategy(),
        initial_cash=1_000,
        execution=ExecutionSimulator(config),
    ).run(build_market_events())

    assert [e.model_dump() for e in result_1.events] == [e.model_dump() for e in result_2.events]


def test_no_fill_path_emits_no_fill_events():
    config = ExecutionConfig(slippage_bps=0, fill_ratio=0.0, fee_per_share=0.0)
    result = BacktestEngine(
        strategy=OneShotLongStrategy(),
        initial_cash=1_000,
        execution=ExecutionSimulator(config),
    ).run(build_market_events())

    event_types = [event.event_type.value for event in result.events]
    assert "order" in event_types
    assert "fill" not in event_types


def test_execution_config_validates_fill_ratio():
    with pytest.raises(ValueError, match="fill_ratio"):
        ExecutionConfig(fill_ratio=1.2)


def test_execution_config_validates_min_fill_quantity():
    with pytest.raises(ValueError, match="min_fill_quantity"):
        ExecutionConfig(min_fill_quantity=0)


def test_execution_config_validates_slippage_bps():
    with pytest.raises(ValueError, match="slippage_bps"):
        ExecutionConfig(slippage_bps=-1)


def test_execution_config_validates_fee_per_share():
    with pytest.raises(ValueError, match="fee_per_share"):
        ExecutionConfig(fee_per_share=-0.01)


def test_engine_normalizes_order_timestamp_to_market_event():
    market_event = build_market_events()[0]
    result = BacktestEngine(strategy=StaleTimestampOrderStrategy(), initial_cash=1_000).run([market_event])
    order_events = [event for event in result.events if event.event_type.value == "order"]
    assert len(order_events) == 1
    assert order_events[0].ts == market_event.ts
