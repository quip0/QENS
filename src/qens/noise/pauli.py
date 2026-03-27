from __future__ import annotations

from typing import Sequence

import numpy as np

from qens.core.types import QubitIndex, PauliString, PauliOp
from qens.core.noise_channel import NoiseChannel
from qens.noise.base import ErrorModel


class BitFlipError(ErrorModel):
    """Bit-flip (X) error with probability p per qubit."""

    def __init__(self, p: float) -> None:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"Probability must be in [0, 1], got {p}")
        self.p = p

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        for q in affected_qubits:
            if rng.random() < self.p:
                error[q] = PauliOp.X
        return error

    def to_channel(self, affected_qubits: Sequence[QubitIndex]) -> NoiseChannel:
        sqrt_1mp = np.sqrt(1 - self.p)
        sqrt_p = np.sqrt(self.p)
        e0 = sqrt_1mp * np.eye(2, dtype=np.complex128)
        e1 = sqrt_p * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        return NoiseChannel(kraus_ops=[e0, e1])

    def __repr__(self) -> str:
        return f"BitFlipError(p={self.p})"


class PhaseFlipError(ErrorModel):
    """Phase-flip (Z) error with probability p per qubit."""

    def __init__(self, p: float) -> None:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"Probability must be in [0, 1], got {p}")
        self.p = p

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        for q in affected_qubits:
            if rng.random() < self.p:
                error[q] = PauliOp.Z
        return error

    def to_channel(self, affected_qubits: Sequence[QubitIndex]) -> NoiseChannel:
        sqrt_1mp = np.sqrt(1 - self.p)
        sqrt_p = np.sqrt(self.p)
        e0 = sqrt_1mp * np.eye(2, dtype=np.complex128)
        e1 = sqrt_p * np.array([[1, 0], [0, -1]], dtype=np.complex128)
        return NoiseChannel(kraus_ops=[e0, e1])

    def __repr__(self) -> str:
        return f"PhaseFlipError(p={self.p})"


class DepolarizingError(ErrorModel):
    """Depolarizing error: applies X, Y, or Z each with probability p/3."""

    def __init__(self, p: float) -> None:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"Probability must be in [0, 1], got {p}")
        self.p = p

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        p_each = self.p / 3.0
        for q in affected_qubits:
            r = rng.random()
            if r < p_each:
                error[q] = PauliOp.X
            elif r < 2 * p_each:
                error[q] = PauliOp.Y
            elif r < 3 * p_each:
                error[q] = PauliOp.Z
        return error

    def to_channel(self, affected_qubits: Sequence[QubitIndex]) -> NoiseChannel:
        p3 = self.p / 3.0
        e0 = np.sqrt(1 - self.p) * np.eye(2, dtype=np.complex128)
        ex = np.sqrt(p3) * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        ey = np.sqrt(p3) * np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
        ez = np.sqrt(p3) * np.array([[1, 0], [0, -1]], dtype=np.complex128)
        return NoiseChannel(kraus_ops=[e0, ex, ey, ez])

    def __repr__(self) -> str:
        return f"DepolarizingError(p={self.p})"


class PauliYError(ErrorModel):
    """Y error with probability p per qubit."""

    def __init__(self, p: float) -> None:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"Probability must be in [0, 1], got {p}")
        self.p = p

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        for q in affected_qubits:
            if rng.random() < self.p:
                error[q] = PauliOp.Y
        return error

    def to_channel(self, affected_qubits: Sequence[QubitIndex]) -> NoiseChannel:
        sqrt_1mp = np.sqrt(1 - self.p)
        sqrt_p = np.sqrt(self.p)
        e0 = sqrt_1mp * np.eye(2, dtype=np.complex128)
        e1 = sqrt_p * np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
        return NoiseChannel(kraus_ops=[e0, e1])

    def __repr__(self) -> str:
        return f"PauliYError(p={self.p})"
