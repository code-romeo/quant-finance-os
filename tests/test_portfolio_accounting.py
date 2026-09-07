from datetime import datetime, timezone

from quant_finance_os.core.events import FillEvent, Side
from quant_finance_os.portfolio.accounting import PortfolioLedger


def test_portfolio_accounting_realized_and_unrealized_pnl():
    ledger = PortfolioLedger(initial_cash=10_000)

    buy_fill = FillEvent(
        timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
        order_id="o1",
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        fill_price=100,
        fee=0,
    )
    ledger.apply_fill(buy_fill)
    ledger.mark_to_market({"AAPL": 105})

    sell_fill = FillEvent(
        timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
        order_id="o2",
        symbol="AAPL",
        side=Side.SELL,
        quantity=4,
        fill_price=110,
        fee=0,
    )
    ledger.apply_fill(sell_fill)
    state = ledger.mark_to_market({"AAPL": 110})

    assert round(state.realized_pnl, 6) == 40.0
    assert round(state.unrealized_pnl, 6) == 60.0
    assert round(state.cash, 6) == 9440.0
    assert round(state.equity, 6) == 10100.0


def test_fee_is_deducted_from_cash():
    ledger = PortfolioLedger(initial_cash=1_000)
    fill = FillEvent(
        timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
        order_id="o1",
        symbol="AAPL",
        side=Side.BUY,
        quantity=1,
        fill_price=100,
        fee=1.25,
    )
    ledger.apply_fill(fill)
    state = ledger.mark_to_market({"AAPL": 100})
    assert round(state.cash, 6) == 898.75
    assert round(state.equity, 6) == 998.75
    assert round(state.realized_pnl, 6) == -1.25


def test_short_add_updates_weighted_average_price():
    ledger = PortfolioLedger(initial_cash=10_000)
    first = FillEvent(
        timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
        order_id="o1",
        symbol="AAPL",
        side=Side.SELL,
        quantity=10,
        fill_price=100,
        fee=0,
    )
    second = FillEvent(
        timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
        order_id="o2",
        symbol="AAPL",
        side=Side.SELL,
        quantity=5,
        fill_price=110,
        fee=0,
    )
    ledger.apply_fill(first)
    position, _ = ledger.apply_fill(second)
    assert round(position.average_price, 6) == 103.333333


def test_reversal_long_to_short_resets_average_to_reversal_fill():
    ledger = PortfolioLedger(initial_cash=10_000)
    ledger.apply_fill(
        FillEvent(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
            order_id="o1",
            symbol="AAPL",
            side=Side.BUY,
            quantity=5,
            fill_price=100,
            fee=0,
        )
    )
    position, realized = ledger.apply_fill(
        FillEvent(
            timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
            order_id="o2",
            symbol="AAPL",
            side=Side.SELL,
            quantity=8,
            fill_price=110,
            fee=0,
        )
    )
    assert realized == 50
    assert position.quantity == -3
    assert position.average_price == 110


def test_reversal_short_to_long_resets_average_to_reversal_fill():
    ledger = PortfolioLedger(initial_cash=10_000)
    ledger.apply_fill(
        FillEvent(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
            order_id="o1",
            symbol="AAPL",
            side=Side.SELL,
            quantity=5,
            fill_price=100,
            fee=0,
        )
    )
    position, realized = ledger.apply_fill(
        FillEvent(
            timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
            order_id="o2",
            symbol="AAPL",
            side=Side.BUY,
            quantity=8,
            fill_price=90,
            fee=0,
        )
    )
    assert realized == 50
    assert position.quantity == 3
    assert position.average_price == 90
