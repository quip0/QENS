from __future__ import annotations

from typing import Sequence

import numpy as np

from qens.core.types import QubitIndex, PauliString, PauliOp
from qens.noise.base import ErrorModel


class LeakageError(ErrorModel):
    """Leakage error modeling transitions to non-computational states.

    Models two processes:
    - Leakage: qubit transitions from {|0>, |1>} to |2> with probability p_leak
    - Relaxation: qubit returns from |2> to {|0>, |1>} with probability p_relax

    In the Pauli frame approximation, a leaked qubit is treated as producing
    a random Pauli error (maximally mixed within the computational subspace).
    """

    def __init__(self, p_leak: float = 0.001, p_relax: float = 0.1) -> None:
        if not (0.0 <= p_leak <= 1.0 and 0.0 <= p_relax <= 1.0):
            raise ValueError("Probabilities must be in [0, 1]")
        self.p_leak = p_leak
        self.p_relax = p_relax
        self._leaked: set[int] = set()

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)

        for q in affected_qubits:
            if q in self._leaked:
                # Leaked qubit: try to relax back
                if rng.random() < self.p_relax:
                    self._leaked.discard(q)
                    # Relaxation produces a random Pauli
                    error[q] = rng.choice(
                        [PauliOp.I, PauliOp.X, PauliOp.Y, PauliOp.Z]
                    )
                else:
                    # Still leaked: maximally depolarizing effect
                    error[q] = rng.choice(
                        [PauliOp.I, PauliOp.X, PauliOp.Y, PauliOp.Z]
                    )
            else:
                # Computational qubit: may leak
                if rng.random() < self.p_leak:
                    self._leaked.add(q)
                    error[q] = rng.choice(
                        [PauliOp.I, PauliOp.X, PauliOp.Y, PauliOp.Z]
                    )

        return error

    def reset(self) -> None:
        """Reset leakage tracking state."""
        self._leaked.clear()

    @property
    def leaked_qubits(self) -> set[int]:
        return set(self._leaked)

    def __repr__(self) -> str:
        return f"LeakageError(p_leak={self.p_leak}, p_relax={self.p_relax})"
