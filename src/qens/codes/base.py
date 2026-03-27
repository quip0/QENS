from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from qens.core.types import Syndrome, PauliString, Coordinate
from qens.core.circuit import Circuit
from qens.utils.pauli_algebra import symplectic_inner_product


@dataclass(frozen=True)
class Stabilizer:
    """A stabilizer generator: a Pauli string and its support qubits."""
    pauli_string: PauliString
    qubits: list[int]
    stabilizer_type: str  # "X" or "Z"


@dataclass(frozen=True)
class LogicalOperator:
    """A logical operator: Pauli string acting as logical X or Z."""
    pauli_string: PauliString
    label: str  # "X_L", "Z_L"


class QECCode(ABC):
    """Base class for quantum error-correcting codes.

    # --- EXTENSION POINT ---
    # To add a new QEC code:
    # 1. Subclass QECCode
    # 2. Implement all abstract methods
    # 3. The key method is stabilizer_generators() which defines the code
    # 4. Implement syndrome_circuit() to build measurement circuits
    # 5. Register with: code_registry.register("my_code", MyCode)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable code name, e.g. 'Surface-5'."""
        ...

    @property
    @abstractmethod
    def num_data_qubits(self) -> int: ...

    @property
    @abstractmethod
    def num_ancilla_qubits(self) -> int: ...

    @property
    def num_qubits(self) -> int:
        return self.num_data_qubits + self.num_ancilla_qubits

    @property
    @abstractmethod
    def code_distance(self) -> int: ...

    @abstractmethod
    def stabilizer_generators(self) -> list[Stabilizer]:
        """Return the list of stabilizer generators for this code."""
        ...

    @abstractmethod
    def logical_operators(self) -> list[LogicalOperator]:
        """Return logical X and Z operators."""
        ...

    @abstractmethod
    def check_matrix(self) -> np.ndarray:
        """Return the parity check matrix H.

        For CSS codes, returns the X-check matrix (detecting Z errors).
        Shape: (num_stabilizers, num_data_qubits).
        """
        ...

    @abstractmethod
    def syndrome_circuit(self, rounds: int = 1) -> Circuit:
        """Build the syndrome extraction circuit for ``rounds`` rounds."""
        ...

    @abstractmethod
    def qubit_coordinates(self) -> dict[int, Coordinate]:
        """Map qubit index -> (row, col) coordinate for visualization."""
        ...

    def compute_syndrome(self, error: PauliString) -> Syndrome:
        """Compute the syndrome for a given Pauli error using the check matrix."""
        stabs = self.stabilizer_generators()
        syndrome = np.zeros(len(stabs), dtype=np.uint8)
        for i, stab in enumerate(stabs):
            syndrome[i] = symplectic_inner_product(stab.pauli_string, error)
        return syndrome

    def is_logical_error(self, residual: PauliString) -> bool:
        """Check if a residual error (after correction) is a logical error.

        True if it commutes with all stabilizers but anticommutes with
        at least one logical operator.
        """
        # First check it commutes with all stabilizers (is in normalizer)
        syndrome = self.compute_syndrome(residual)
        if np.any(syndrome):
            return False  # Doesn't commute with all stabilizers

        # Check if it anticommutes with any logical operator
        for logical in self.logical_operators():
            if symplectic_inner_product(residual, logical.pauli_string) != 0:
                return True

        return False

    def __repr__(self) -> str:
        return f"{self.name} [[n={self.num_data_qubits}, d={self.code_distance}]]"
