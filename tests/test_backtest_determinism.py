from datetime import datetime, timezone

import pytest

from quant_finance_os.backtest.engine import BacktestEngine
from quant_finance_os.core.events import MarketEvent, Side, SignalEvent


class BuyOnceStrategy:
    def __init__(self) -> None:
        self._has_bought = False

    def on_market_event(self, event: MarketEvent, ledger):
        if self._has_bought:
            return []
        self._has_bought = True
        return [SignalEvent(timestamp=event.timestamp, symbol=event.symbol, side=Side.BUY, quantity=1.0, reason="entry")]


class MetadataAwareStrategy:
    def __init__(self) -> None:
        self.seen_seq: list[int] = []

    def on_market_event(self, event: MarketEvent, ledger):
        self.seen_seq.append(event.metadata.seq)
        return []


def _events():
    return [
        MarketEvent(timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc), symbol="AAPL", price=100.0, volume=10.0),
        MarketEvent(timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc), symbol="AAPL", price=101.0, volume=15.0),
    ]


def test_backtest_replay_is_deterministic():
    left = BacktestEngine(strategy=BuyOnceStrategy(), initial_cash=10_000, run_id="r1").run(_events())
    right = BacktestEngine(strategy=BuyOnceStrategy(), initial_cash=10_000, run_id="r1").run(_events())

    assert left.events == right.events
    assert [e.metadata.seq for e in left.events] == list(range(1, len(left.events) + 1))


def test_same_engine_run_restarts_sequence_and_portfolio():
    class BuyEveryTickStrategy:
        def on_market_event(self, event: MarketEvent, ledger):
            return [SignalEvent(timestamp=event.timestamp, symbol=event.symbol, side=Side.BUY, quantity=1.0, reason="entry")]

    engine = BacktestEngine(strategy=BuyEveryTickStrategy(), initial_cash=10_000, run_id="r1")
    first = engine.run(_events())
    second = engine.run(_events())

    assert first.events == second.events
    assert first.final_cash == second.final_cash
    assert first.final_equity == second.final_equity


def test_strategy_receives_normalized_market_event_metadata():
    strategy = MetadataAwareStrategy()
    BacktestEngine(strategy=strategy, initial_cash=10_000, run_id="r1").run(_events())
    assert strategy.seen_seq == [1, 2]


def test_backtest_rejects_out_of_order_market_events():
    events = [
        MarketEvent(timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc), symbol="AAPL", price=101.0, volume=15.0),
        MarketEvent(timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc), symbol="AAPL", price=100.0, volume=10.0),
    ]
    engine = BacktestEngine(strategy=BuyOnceStrategy(), initial_cash=10_000)

    with pytest.raises(ValueError, match="ordered"):
        engine.run(events)


def test_market_event_validation_fails_fast():
    with pytest.raises(ValueError, match="positive"):
        MarketEvent(timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc), symbol="AAPL", price=0.0, volume=1.0)
