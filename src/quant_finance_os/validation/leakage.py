from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TimestampPair:
    feature_timestamp: datetime
    target_timestamp: datetime


def assert_no_lookahead(pairs: list[TimestampPair], horizon: timedelta) -> None:
    if horizon.total_seconds() < 0:
        raise ValueError("horizon must be non-negative")

    for idx, pair in enumerate(pairs):
        latest_allowed_feature_time = pair.target_timestamp - horizon
        if pair.feature_timestamp > latest_allowed_feature_time:
            raise ValueError(
                "Potential leakage detected at index "
                f"{idx}: feature_timestamp={pair.feature_timestamp.isoformat()} exceeds "
                f"target_timestamp-horizon={latest_allowed_feature_time.isoformat()}"
            )
