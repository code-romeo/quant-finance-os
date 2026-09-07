from __future__ import annotations

import polars as pl


def walk_forward_splits(
    frame: pl.DataFrame,
    timestamp_col: str,
    train_size: int,
    test_size: int,
    step_size: int | None = None,
) -> list[tuple[pl.DataFrame, pl.DataFrame]]:
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    if step_size is not None and step_size <= 0:
        raise ValueError("step_size must be positive")

    sorted_frame = frame.sort(timestamp_col)
    if sorted_frame[timestamp_col].to_list() != frame[timestamp_col].to_list():
        raise ValueError("frame must be sorted by timestamp_col")

    step = step_size or test_size
    splits: list[tuple[pl.DataFrame, pl.DataFrame]] = []

    start = 0
    n = len(frame)
    while start + train_size + test_size <= n:
        train = frame.slice(start, train_size)
        test = frame.slice(start + train_size, test_size)
        splits.append((train, test))
        start += step

    return splits
