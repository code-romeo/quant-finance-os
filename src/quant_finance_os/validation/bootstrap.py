from __future__ import annotations

import random
from statistics import mean


def bootstrap_mean_ci(
    values: list[float],
    n_resamples: int = 200,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float, float]:
    if len(values) < 2:
        raise ValueError("values must contain at least two observations")
    if n_resamples < 50:
        raise ValueError("n_resamples must be at least 50")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")

    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(n_resamples):
        sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
        boot_means.append(mean(sample))

    boot_means.sort()
    lower_idx = int((alpha / 2) * n_resamples)
    upper_idx = int((1 - alpha / 2) * n_resamples) - 1
    return mean(values), boot_means[lower_idx], boot_means[upper_idx]
