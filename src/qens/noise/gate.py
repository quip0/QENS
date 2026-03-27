from __future__ import annotations

from typing import Sequence

import numpy as np

from qens.core.types import QubitIndex, PauliString, PauliOp
from qens.core.circuit import Gate
from qens.noise.base import ErrorModel


class CoherentRotationError(ErrorModel):
    """Coherent over/under-rotation error.

    Models systematic gate errors where each gate application includes
    a small additional rotation drawn from a Gaussian distribution.
    In the Pauli frame, this is approximated as a probabilistic Pauli
    error with probability proportional to sin^2(angle).
    """

    def __init__(self, angle_stddev: float = 0.01) -> None:
        if angle_stddev < 0:
            raise ValueError("Standard deviation must be non-negative")
        self.angle_stddev = angle_stddev

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        for q in affected_qubits:
            angle = rng.normal(0, self.angle_stddev)
            p_error = np.sin(angle) ** 2
            if rng.random() < p_error:
                # Randomly choose X, Y, or Z with equal probability
                error[q] = rng.choice([PauliOp.X, PauliOp.Y, PauliOp.Z])
        return error

    def applies_to(self, gate: Gate) -> bool:
        return gate.name != "M"

    def __repr__(self) -> str:
        return f"CoherentRotationError(angle_stddev={self.angle_stddev})"


class CrosstalkError(ErrorModel):
    """Crosstalk error between neighboring qubits.

    Models unwanted ZZ interactions between qubit pairs during gate operations.
    The coupling_map specifies which pairs experience crosstalk and the strength.
    """

    def __init__(
        self, coupling_map: dict[tuple[int, int], float] | None = None
    ) -> None:
        self.coupling_map: dict[tuple[int, int], float] = coupling_map or {}

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        affected_set = set(affected_qubits)
        for (q0, q1), strength in self.coupling_map.items():
            # Crosstalk activates when at least one qubit in the pair is active
            if q0 in affected_set or q1 in affected_set:
                if rng.random() < strength:
                    # ZZ crosstalk: apply Z to both qubits
                    error[q0] ^= PauliOp.Z
                    error[q1] ^= PauliOp.Z
        return error

    def applies_to(self, gate: Gate) -> bool:
        return gate.name not in ("M", "R")

    def __repr__(self) -> str:
        return f"CrosstalkError(pairs={len(self.coupling_map)})"
