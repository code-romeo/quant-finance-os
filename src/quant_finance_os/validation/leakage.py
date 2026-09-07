from __future__ import annotations

from datetime import datetime

from quant_finance_os.core.events import MarketDataEvent


def detect_lookahead_indices(feature_times: list[datetime], label_times: list[datetime]) -> list[int]:
    if len(feature_times) != len(label_times):
        raise ValueError("feature_times and label_times must have the same length")
    return [idx for idx, (f, l) in enumerate(zip(feature_times, label_times, strict=True)) if f > l]


def validate_market_data_lineage(events: list[MarketDataEvent]) -> list[str]:
    issues: list[str] = []
    for idx in range(1, len(events)):
        if events[idx].ts < events[idx - 1].ts:
            issues.append(f"timestamp regression at index {idx}")
    return issues
