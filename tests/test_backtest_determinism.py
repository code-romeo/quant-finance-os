from datetime import datetime, timezone

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
