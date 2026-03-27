from __future__ import annotations

from typing import Sequence

import numpy as np

from qens.core.types import QubitIndex, PauliString
from qens.noise.base import ErrorModel


class CorrelatedPauliError(ErrorModel):
    """Correlated Pauli error across qubit pairs.

    Models noise where errors on neighboring qubits are correlated,
    such as cosmic ray events or shared control lines.

    The joint_errors dict maps qubit pairs to a list of
    (probability, pauli_on_q0, pauli_on_q1) tuples.
    """

    def __init__(
        self,
        joint_errors: dict[
            tuple[int, int],
            list[tuple[float, int, int]],
        ],
    ) -> None:
        self.joint_errors = joint_errors

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        for (q0, q1), error_list in self.joint_errors.items():
            r = rng.random()
            cumulative = 0.0
            for prob, p0, p1 in error_list:
                cumulative += prob
                if r < cumulative:
                    # XOR to compose with any existing errors
                    error[q0] ^= p0
                    error[q1] ^= p1
                    break
        return error

    def __repr__(self) -> str:
        return f"CorrelatedPauliError(pairs={len(self.joint_errors)})"
