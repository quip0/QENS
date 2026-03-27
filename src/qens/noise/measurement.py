from __future__ import annotations

from typing import Sequence

import numpy as np

from qens.core.types import QubitIndex, PauliString, PauliOp
from qens.core.circuit import Gate
from qens.noise.base import ErrorModel


class MeasurementError(ErrorModel):
    """Asymmetric measurement (readout) error.

    Models faulty readout where:
    - A |0> state is misread as |1> with probability p_0to1
    - A |1> state is misread as |0> with probability p_1to0

    In the Pauli frame picture, this is modeled as a bit-flip (X) error
    applied just before measurement.
    """

    def __init__(self, p_0to1: float = 0.01, p_1to0: float | None = None) -> None:
        if p_1to0 is None:
            p_1to0 = p_0to1
        if not (0.0 <= p_0to1 <= 1.0 and 0.0 <= p_1to0 <= 1.0):
            raise ValueError("Probabilities must be in [0, 1]")
        self.p_0to1 = p_0to1
        self.p_1to0 = p_1to0

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        # Use the average flip rate as the pre-measurement bit-flip probability
        p_avg = (self.p_0to1 + self.p_1to0) / 2.0
        for q in affected_qubits:
            if rng.random() < p_avg:
                error[q] = PauliOp.X
        return error

    def applies_to(self, gate: Gate) -> bool:
        return gate.name == "M"

    def __repr__(self) -> str:
        return f"MeasurementError(p_0to1={self.p_0to1}, p_1to0={self.p_1to0})"
