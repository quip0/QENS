from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt

from qens.core.types import Syndrome, PauliString


@dataclass
class SimulationResult:
    """Results from a batch of Monte Carlo simulation shots."""
    syndromes: list[Syndrome]
    errors: list[PauliString]
    corrections: list[PauliString] = field(default_factory=list)
    logical_errors: list[bool] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def num_shots(self) -> int:
        return len(self.syndromes)

    @property
    def logical_error_rate(self) -> float:
        if not self.logical_errors:
            return 0.0
        return sum(self.logical_errors) / len(self.logical_errors)

    @property
    def logical_error_count(self) -> int:
        return sum(self.logical_errors)

    def sample_syndrome(self, index: int) -> Syndrome:
        return self.syndromes[index]

    def sample_error(self, index: int) -> PauliString:
        return self.errors[index]

    def __repr__(self) -> str:
        rate = f"{self.logical_error_rate:.4f}" if self.logical_errors else "N/A"
        return f"SimulationResult(shots={self.num_shots}, logical_error_rate={rate})"


@dataclass
class ThresholdResult:
    """Results from a threshold sweep experiment."""
    distances: list[int]
    physical_error_rates: list[float]
    logical_error_rates: npt.NDArray[np.float64]  # shape: (len(distances), len(physical_error_rates))
    shots_per_point: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"ThresholdResult(distances={self.distances}, "
            f"p_range=[{self.physical_error_rates[0]:.4f}, "
            f"{self.physical_error_rates[-1]:.4f}], "
            f"shots={self.shots_per_point})"
        )
