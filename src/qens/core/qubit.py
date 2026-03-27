from __future__ import annotations

import enum
from dataclasses import dataclass

from qens.core.types import Coordinate, QubitIndex


class QubitRole(enum.Enum):
    """Role of a qubit within an error-correcting code."""
    DATA = "data"
    ANCILLA_X = "ancilla_x"
    ANCILLA_Z = "ancilla_z"


@dataclass(frozen=True)
class Qubit:
    """A qubit with an index, coordinate, and role."""
    index: QubitIndex
    coordinate: Coordinate
    role: QubitRole = QubitRole.DATA

    def __repr__(self) -> str:
        return f"Qubit({self.index}, {self.coordinate}, {self.role.value})"
