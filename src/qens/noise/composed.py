from __future__ import annotations

from typing import Sequence

import numpy as np

from qens.core.types import QubitIndex, PauliString
from qens.core.circuit import Gate
from qens.noise.base import ErrorModel
from qens.utils.pauli_algebra import pauli_string_multiply


class ComposedNoiseModel(ErrorModel):
    """Compose multiple error models into a single noise model.

    Applies each model sequentially and combines errors via Pauli multiplication.
    Each model's ``applies_to`` filter is respected independently.

    Usage:
        noise = ComposedNoiseModel([
            DepolarizingError(p=0.001),
            MeasurementError(p_0to1=0.01),
            CrosstalkError(coupling_map={(0,1): 0.002}),
        ])
    """

    def __init__(self, models: list[ErrorModel]) -> None:
        self.models = models

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        combined = np.zeros(num_qubits, dtype=np.uint8)
        for model in self.models:
            error = model.sample_errors(num_qubits, affected_qubits, rng)
            combined, _ = pauli_string_multiply(combined, error)
        return combined

    def sample_errors_for_gate(
        self,
        num_qubits: int,
        gate: Gate,
        rng: np.random.Generator,
    ) -> PauliString:
        """Sample errors for a specific gate, respecting each model's filter."""
        combined = np.zeros(num_qubits, dtype=np.uint8)
        for model in self.models:
            if model.applies_to(gate):
                error = model.sample_errors(num_qubits, list(gate.qubits), rng)
                combined, _ = pauli_string_multiply(combined, error)
        return combined

    def reset(self) -> None:
        """Reset all component models."""
        for model in self.models:
            model.reset()

    def applies_to(self, gate: Gate) -> bool:
        return any(m.applies_to(gate) for m in self.models)

    def __repr__(self) -> str:
        return f"ComposedNoiseModel({self.models})"
