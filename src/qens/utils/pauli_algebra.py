from __future__ import annotations

import numpy as np
import numpy.typing as npt

# Pauli multiplication table: result[a][b] = (product, phase_exponent)
# Phase is i^exponent. Operators encoded as I=0, X=1, Y=2, Z=3.
# XY = iZ, YX = -iZ, XZ = -iY, ZX = iY, YZ = iX, ZY = -iX
_MULT_TABLE: dict[tuple[int, int], tuple[int, int]] = {
    (0, 0): (0, 0), (0, 1): (1, 0), (0, 2): (2, 0), (0, 3): (3, 0),
    (1, 0): (1, 0), (1, 1): (0, 0), (1, 2): (3, 1), (1, 3): (2, 3),
    (2, 0): (2, 0), (2, 1): (3, 3), (2, 2): (0, 0), (2, 3): (1, 1),
    (3, 0): (3, 0), (3, 1): (2, 1), (3, 2): (1, 3), (3, 3): (0, 0),
}

# Commutation: 0 = commutes, 1 = anticommutes
_COMMUTATION_TABLE: dict[tuple[int, int], int] = {
    (0, 0): 0, (0, 1): 0, (0, 2): 0, (0, 3): 0,
    (1, 0): 0, (1, 1): 0, (1, 2): 1, (1, 3): 1,
    (2, 0): 0, (2, 1): 1, (2, 2): 0, (2, 3): 1,
    (3, 0): 0, (3, 1): 1, (3, 2): 1, (3, 3): 0,
}


def pauli_multiply(a: int, b: int) -> tuple[int, int]:
    """Multiply two single-qubit Pauli operators.

    Args:
        a: First Pauli (0=I, 1=X, 2=Y, 3=Z).
        b: Second Pauli (0=I, 1=X, 2=Y, 3=Z).

    Returns:
        (result_pauli, phase_exponent) where the full result is i^phase * result_pauli.
    """
    return _MULT_TABLE[(a, b)]


def pauli_commutes(a: int, b: int) -> bool:
    """Check if two single-qubit Paulis commute."""
    return _COMMUTATION_TABLE[(a, b)] == 0


def pauli_string_multiply(
    ps1: npt.NDArray[np.uint8],
    ps2: npt.NDArray[np.uint8],
) -> tuple[npt.NDArray[np.uint8], int]:
    """Multiply two Pauli strings element-wise.

    Args:
        ps1: Array of Pauli operators (0=I, 1=X, 2=Y, 3=Z), shape (n,).
        ps2: Array of Pauli operators, shape (n,).

    Returns:
        (result_string, total_phase_exponent_mod_4).
    """
    n = len(ps1)
    result = np.empty(n, dtype=np.uint8)
    total_phase = 0
    for i in range(n):
        prod, phase = _MULT_TABLE[(int(ps1[i]), int(ps2[i]))]
        result[i] = prod
        total_phase += phase
    return result, total_phase % 4


def symplectic_inner_product(
    ps1: npt.NDArray[np.uint8],
    ps2: npt.NDArray[np.uint8],
) -> int:
    """Compute the symplectic inner product of two Pauli strings.

    Returns 0 if the strings commute, 1 if they anticommute.
    """
    total = 0
    for i in range(len(ps1)):
        total += _COMMUTATION_TABLE[(int(ps1[i]), int(ps2[i]))]
    return total % 2
