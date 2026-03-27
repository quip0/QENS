from __future__ import annotations

import numpy as np

from qens.core.types import Coordinate, PauliOp
from qens.core.circuit import Circuit
from qens.codes.base import QECCode, Stabilizer, LogicalOperator
from qens.codes.lattice import Lattice, LatticeNode, LatticeEdge


class RepetitionCode(QECCode):
    """Distance-d repetition code.

    A 1D chain of d data qubits with d-1 ancilla qubits measuring
    ZZ stabilizers between adjacent pairs. Corrects bit-flip (X) errors.

    Qubit layout (d=5):
        D0 - A0 - D1 - A1 - D2 - A2 - D3 - A3 - D4
    """

    def __init__(self, distance: int) -> None:
        if distance < 2:
            raise ValueError("Distance must be >= 2")
        self._distance = distance
        self._lattice = self._build_lattice()

    @property
    def name(self) -> str:
        return f"Repetition-{self._distance}"

    @property
    def num_data_qubits(self) -> int:
        return self._distance

    @property
    def num_ancilla_qubits(self) -> int:
        return self._distance - 1

    @property
    def code_distance(self) -> int:
        return self._distance

    @property
    def lattice(self) -> Lattice:
        return self._lattice

    def _build_lattice(self) -> Lattice:
        lattice = Lattice()
        d = self._distance
        # Data qubits: indices 0..d-1
        for i in range(d):
            lattice.add_node(LatticeNode(i, (0, 2 * i), "data"))
        # Ancilla qubits: indices d..2d-2
        for i in range(d - 1):
            lattice.add_node(LatticeNode(d + i, (0, 2 * i + 1), "ancilla_z"))
            lattice.add_edge(LatticeEdge(i, d + i))
            lattice.add_edge(LatticeEdge(i + 1, d + i))
        return lattice

    def stabilizer_generators(self) -> list[Stabilizer]:
        d = self._distance
        stabilizers = []
        for i in range(d - 1):
            ps = np.zeros(d, dtype=np.uint8)
            ps[i] = PauliOp.Z
            ps[i + 1] = PauliOp.Z
            stabilizers.append(Stabilizer(ps, [i, i + 1], "Z"))
        return stabilizers

    def logical_operators(self) -> list[LogicalOperator]:
        d = self._distance
        # Logical X: X on all data qubits
        x_l = np.full(d, PauliOp.X, dtype=np.uint8)
        # Logical Z: Z on any single data qubit (e.g., qubit 0)
        z_l = np.zeros(d, dtype=np.uint8)
        z_l[0] = PauliOp.Z
        return [
            LogicalOperator(x_l, "X_L"),
            LogicalOperator(z_l, "Z_L"),
        ]

    def check_matrix(self) -> np.ndarray:
        d = self._distance
        H = np.zeros((d - 1, d), dtype=np.uint8)
        for i in range(d - 1):
            H[i, i] = 1
            H[i, i + 1] = 1
        return H

    def syndrome_circuit(self, rounds: int = 1) -> Circuit:
        d = self._distance
        n_total = d + (d - 1)  # data + ancilla qubits
        circuit = Circuit(n_total)

        for _ in range(rounds):
            # Reset ancillas
            for a in range(d - 1):
                circuit.reset(d + a)
            # CNOT from each data pair to ancilla
            for a in range(d - 1):
                circuit.cx(a, d + a)
                circuit.cx(a + 1, d + a)
            # Measure ancillas
            for a in range(d - 1):
                circuit.measure(d + a)

        return circuit

    def qubit_coordinates(self) -> dict[int, Coordinate]:
        coords: dict[int, Coordinate] = {}
        for node in self._lattice.nodes:
            coords[node.index] = node.coordinate
        return coords
