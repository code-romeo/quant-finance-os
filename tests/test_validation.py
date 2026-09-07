from datetime import datetime, timedelta, timezone

import pytest

from quant_finance_os.validation import (
    TimestampPair,
    assert_no_lookahead,
    bootstrap_mean_ci,
    generate_walk_forward_splits,
)


def test_leakage_detection_raises_clear_error():
    pairs = [
        TimestampPair(
            feature_timestamp=datetime(2024, 1, 1, 9, 35, tzinfo=timezone.utc),
            target_timestamp=datetime(2024, 1, 1, 9, 36, tzinfo=timezone.utc),
        )
    ]
    with pytest.raises(ValueError, match="Potential leakage"):
        assert_no_lookahead(pairs, horizon=timedelta(minutes=2))


def test_walk_forward_splits_with_embargo():
    splits = generate_walk_forward_splits(n_samples=12, train_size=4, test_size=2, embargo_size=1)

    assert splits[0].train_indices == (0, 1, 2, 3)
    assert splits[0].test_indices == (5, 6)
    assert len(splits) == 3


def test_bootstrap_mean_ci_is_seeded_and_repeatable():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    left = bootstrap_mean_ci(values, n_resamples=200, seed=7)
    right = bootstrap_mean_ci(values, n_resamples=200, seed=7)

    assert left == right
    assert left[1] <= left[0] <= left[2]
