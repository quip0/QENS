from __future__ import annotations

import numpy as np


def get_rng(seed: int | None = None) -> np.random.Generator:
    """Create a seeded random number generator for reproducible simulations.

    Args:
        seed: Integer seed. If None, uses non-deterministic entropy.

    Returns:
        A numpy Generator instance.
    """
    return np.random.default_rng(seed)
