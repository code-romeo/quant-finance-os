from datetime import datetime, timezone

import polars as pl

from quant_finance_os.core import MarketDataEvent
from quant_finance_os.validation import (
    detect_lookahead_indices,
    validate_market_data_lineage,
    walk_forward_splits,
)


def test_detect_lookahead_indices_flags_future_features():
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    features = [base, base.replace(minute=1), base.replace(minute=4)]
    labels = [base, base.replace(minute=2), base.replace(minute=3)]
    assert detect_lookahead_indices(features, labels) == [2]


def test_validate_market_data_lineage_detects_time_regression():
    events = [
        MarketDataEvent(
            event_id="a",
            seq=0,
            ts=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            symbol="AAPL",
            price=100,
            volume=1,
        ),
        MarketDataEvent(
            event_id="b",
            seq=1,
            ts=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            symbol="AAPL",
            price=101,
            volume=1,
        ),
    ]
    assert validate_market_data_lineage(events) == ["timestamp regression at index 1"]


def test_walk_forward_splits_generates_expected_windows():
    frame = pl.DataFrame(
        {
            "ts": [
                datetime(2024, 1, 1, 0, i, tzinfo=timezone.utc)
                for i in range(8)
            ],
            "price": [100 + i for i in range(8)],
        }
    )
    splits = walk_forward_splits(frame, timestamp_col="ts", train_size=4, test_size=2, step_size=2)
    assert len(splits) == 2
    assert splits[0][0]["price"].to_list() == [100, 101, 102, 103]
    assert splits[0][1]["price"].to_list() == [104, 105]
    assert splits[1][0]["price"].to_list() == [102, 103, 104, 105]
    assert splits[1][1]["price"].to_list() == [106, 107]


def test_walk_forward_rejects_non_positive_step():
    frame = pl.DataFrame(
        {
            "ts": [datetime(2024, 1, 1, 0, i, tzinfo=timezone.utc) for i in range(3)],
            "price": [100, 101, 102],
        }
    )
    try:
        walk_forward_splits(frame, timestamp_col="ts", train_size=1, test_size=1, step_size=0)
    except ValueError as exc:
        assert "step_size must be positive" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-positive step_size")
