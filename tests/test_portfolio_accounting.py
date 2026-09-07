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
