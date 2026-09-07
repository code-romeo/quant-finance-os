from datetime import datetime, timezone

from quant_finance_os.analytics.attribution import AttributionEngine
from quant_finance_os.core.events import FillEvent, Side


def test_attribution_engine_aggregates_signed_notional_by_symbol():
    fills = [
        FillEvent(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
            order_id="o1",
            symbol="AAPL",
            side=Side.BUY,
            quantity=2,
            fill_price=100,
            fee=0,
        ),
        FillEvent(
            timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
            order_id="o2",
            symbol="AAPL",
            side=Side.SELL,
            quantity=1,
            fill_price=110,
            fee=0,
        ),
        FillEvent(
            timestamp=datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
            order_id="o3",
            symbol="MSFT",
            side=Side.SELL,
            quantity=1,
            fill_price=50,
            fee=0,
        ),
    ]

    report = AttributionEngine().from_fills(fills)

    assert report.notional_flow_by_symbol["AAPL"] == -90
    assert report.notional_flow_by_symbol["MSFT"] == 50
