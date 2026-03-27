from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from qens.core.types import KrausMatrix


@dataclass
class NoiseChannel:
    """A quantum noise channel in Kraus representation.

    Channel acts as: rho -> sum_k  E_k @ rho @ E_k^dagger
    Completeness: sum_k  E_k^dagger @ E_k == I
    """
    kraus_ops: list[KrausMatrix]

    @property
    def num_kraus(self) -> int:
        return len(self.kraus_ops)

    def validate(self, tol: float = 1e-10) -> bool:
        """Check the completeness relation sum_k E_k^dag E_k == I."""
        if not self.kraus_ops:
            return False
        d = self.kraus_ops[0].shape[0]
        total = np.zeros((d, d), dtype=np.complex128)
        for ek in self.kraus_ops:
            total += ek.conj().T @ ek
        return bool(np.allclose(total, np.eye(d), atol=tol))

    def probabilities(self) -> npt.NDArray[np.float64]:
        """Return the probability of each Kraus operator being applied.

        For a Pauli channel, this is Tr(E_k^dag E_k) / d.
        """
        probs = np.array([
            np.real(np.trace(ek.conj().T @ ek))
            for ek in self.kraus_ops
        ])
        return probs / probs.sum()

    def sample(self, rng: np.random.Generator) -> int:
        """Sample which Kraus operator is applied (by probability)."""
        probs = self.probabilities()
        return int(rng.choice(len(self.kraus_ops), p=probs))
