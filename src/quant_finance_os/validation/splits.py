from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WalkForwardSplit:
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]


def generate_walk_forward_splits(
    n_samples: int,
    train_size: int,
    test_size: int,
    step_size: int | None = None,
    embargo_size: int = 0,
) -> list[WalkForwardSplit]:
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    if embargo_size < 0:
        raise ValueError("embargo_size must be non-negative")

    step = step_size or test_size
    if step <= 0:
        raise ValueError("step_size must be positive")

    splits: list[WalkForwardSplit] = []
    train_start = 0

    while True:
        train_end = train_start + train_size
        test_start = train_end + embargo_size
        test_end = test_start + test_size
        if test_end > n_samples:
            break
        splits.append(
            WalkForwardSplit(
                train_indices=tuple(range(train_start, train_end)),
                test_indices=tuple(range(test_start, test_end)),
            )
        )
        train_start += step

    if not splits:
        raise ValueError("configuration produced zero walk-forward splits")
    return splits
