from datetime import datetime, timezone

from quant_finance_os.backtest import Portfolio
from quant_finance_os.core import FillEvent, Side


def test_portfolio_accounting_realized_unrealized_and_cash():
    portfolio = Portfolio(initial_cash=1_000)
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

    buy = FillEvent(
        event_id="f1",
        seq=1,
        ts=ts,
        order_id="o1",
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        fill_price=10,
        fee=1,
    )
    portfolio.apply_fill(buy)

    sell = FillEvent(
        event_id="f2",
        seq=2,
        ts=ts,
        order_id="o2",
        symbol="AAPL",
        side=Side.SELL,
        quantity=4,
        fill_price=12,
        fee=1,
    )
    portfolio.apply_fill(sell)

    pnl = portfolio.mark_to_market(seq=3, ts=ts, prices={"AAPL": 11})

    assert round(portfolio.cash, 6) == 946
    assert round(portfolio.realized_pnl, 6) == 6
    assert round(pnl.unrealized_pnl, 6) == 6
    assert round(pnl.equity, 6) == 1012


def test_portfolio_flip_resets_average_price():
    portfolio = Portfolio(initial_cash=1_000)
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

    portfolio.apply_fill(
        FillEvent(
            event_id="f1",
            seq=1,
            ts=ts,
            order_id="o1",
            symbol="AAPL",
            side=Side.BUY,
            quantity=5,
            fill_price=10,
            fee=0,
        )
    )
    position = portfolio.apply_fill(
        FillEvent(
            event_id="f2",
            seq=2,
            ts=ts,
            order_id="o2",
            symbol="AAPL",
            side=Side.SELL,
            quantity=8,
            fill_price=12,
            fee=0,
        )
    )

    assert position.quantity == -3
    assert position.avg_price == 12
    assert round(portfolio.realized_pnl, 6) == 10


def test_partial_cover_short_keeps_cost_basis_on_remaining_position():
    portfolio = Portfolio(initial_cash=1_000)
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    portfolio.apply_fill(
        FillEvent(
            event_id="f1",
            seq=1,
            ts=ts,
            order_id="o1",
            symbol="AAPL",
            side=Side.SELL,
            quantity=10,
            fill_price=10,
            fee=0,
        )
    )
    position = portfolio.apply_fill(
        FillEvent(
            event_id="f2",
            seq=2,
            ts=ts,
            order_id="o2",
            symbol="AAPL",
            side=Side.BUY,
            quantity=4,
            fill_price=8,
            fee=0,
        )
    )
    assert position.quantity == -6
    assert position.avg_price == 10
    assert round(portfolio.realized_pnl, 6) == 8


def test_mark_to_market_skips_missing_price_symbols():
    portfolio = Portfolio(initial_cash=1_000)
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    portfolio.apply_fill(
        FillEvent(
            event_id="f1",
            seq=1,
            ts=ts,
            order_id="o1",
            symbol="AAPL",
            side=Side.BUY,
            quantity=5,
            fill_price=10,
            fee=0,
        )
    )
    pnl = portfolio.mark_to_market(seq=2, ts=ts, prices={})
    assert pnl.unrealized_pnl == 0
    assert pnl.equity == portfolio.cash


def test_mark_to_market_missing_price_for_short_skips_revaluation():
    portfolio = Portfolio(initial_cash=1_000)
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    portfolio.apply_fill(
        FillEvent(
            event_id="f1",
            seq=1,
            ts=ts,
            order_id="o1",
            symbol="AAPL",
            side=Side.SELL,
            quantity=5,
            fill_price=10,
            fee=0,
        )
    )
    pnl = portfolio.mark_to_market(seq=2, ts=ts, prices={})
    assert pnl.unrealized_pnl == 0
    assert pnl.equity == portfolio.cash
