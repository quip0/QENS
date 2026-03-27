from __future__ import annotations

import enum
from typing import TypeAlias

import numpy as np
import numpy.typing as npt


class PauliOp(enum.IntEnum):
    """Single-qubit Pauli operators."""
    I = 0
    X = 1
    Y = 2
    Z = 3


class Outcome(enum.IntEnum):
    """Measurement outcome."""
    ZERO = 0
    ONE = 1


# A Pauli string on n qubits: array of PauliOp ordinals, shape (n,)
PauliString: TypeAlias = npt.NDArray[np.uint8]

# Syndrome: binary array, shape (num_stabilizers,)
Syndrome: TypeAlias = npt.NDArray[np.uint8]

# A Kraus operator: complex matrix, shape (d, d)
KrausMatrix: TypeAlias = npt.NDArray[np.complex128]

# Qubit index
QubitIndex: TypeAlias = int

# Coordinates on a lattice (row, col) or (row, col, time)
# Allows float values for ancilla centroids in color codes
Coordinate: TypeAlias = tuple[int | float, ...]
