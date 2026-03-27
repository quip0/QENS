from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np

from qens.core.types import QubitIndex, PauliString
from qens.core.noise_channel import NoiseChannel
from qens.core.circuit import Gate


class ErrorModel(ABC):
    """Base class for all error models in QENS.

    Subclass this to create custom noise models. At minimum, implement
    ``sample_errors``. Optionally override ``to_channel`` for Kraus
    representation, and ``applies_to`` to filter which gates this
    model targets.

    # --- EXTENSION POINT ---
    # To add a new error model:
    # 1. Subclass ErrorModel
    # 2. Implement sample_errors() to return Pauli errors on affected qubits
    # 3. Optionally implement to_channel() for density-matrix simulation
    # 4. Register with: noise_registry.register("my_model", MyModel)
    """

    @abstractmethod
    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        """Sample a Pauli error on the given qubits.

        Returns:
            PauliString of length num_qubits (I on unaffected qubits).
        """
        ...

    def to_channel(self, affected_qubits: Sequence[QubitIndex]) -> NoiseChannel:
        """Return the Kraus representation of this error model.

        Optional: used for density-matrix-level simulation.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not provide a Kraus representation."
        )

    def applies_to(self, gate: Gate) -> bool:
        """Return True if this error model should be applied after ``gate``.

        Default: applies to all gates. Override to filter.
        """
        return True

    @abstractmethod
    def __repr__(self) -> str: ...
