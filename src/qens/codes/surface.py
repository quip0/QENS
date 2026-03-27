from __future__ import annotations

import numpy as np

from qens.core.types import Coordinate, PauliOp
from qens.core.circuit import Circuit
from qens.codes.base import QECCode, Stabilizer, LogicalOperator
from qens.codes.lattice import Lattice, LatticeNode, LatticeEdge


class SurfaceCode(QECCode):
    """Rotated surface code of distance d.

    Data qubits live on the vertices of a d x d grid at integer coordinates.
    Stabilizer ancillas sit at the centers of faces (plaquettes).

    X-stabilizers act on one sublattice of faces, Z-stabilizers on the other.
    """

    def __init__(self, distance: int, rotated: bool = True) -> None:
        if distance < 2:
            raise ValueError("Distance must be >= 2")
        if distance % 2 == 0:
            raise ValueError("Distance must be odd for the standard surface code")
        self._distance = distance
        self._rotated = rotated

        # Data qubit index = r * d + c for coordinate (r, c)
        self._data_qubits: list[tuple[int, int]] = []
        # Each stabilizer stores its data qubit indices
        self._x_stabilizer_qubits: list[list[int]] = []
        self._z_stabilizer_qubits: list[list[int]] = []
        self._lattice = self._build_layout()

    def _data_index(self, r: int, c: int) -> int:
        return r * self._distance + c

    @property
    def name(self) -> str:
        variant = "Rotated" if self._rotated else "Unrotated"
        return f"{variant}Surface-{self._distance}"

    @property
    def num_data_qubits(self) -> int:
        return self._distance * self._distance

    @property
    def num_ancilla_qubits(self) -> int:
        return len(self._x_stabilizer_qubits) + len(self._z_stabilizer_qubits)

    @property
    def code_distance(self) -> int:
        return self._distance

    @property
    def lattice(self) -> Lattice:
        return self._lattice

    def _build_layout(self) -> Lattice:
        d = self._distance
        lattice = Lattice()
        idx = 0

        # Data qubits at integer coordinates (r, c) for r,c in [0, d-1]
        for r in range(d):
            for c in range(d):
                self._data_qubits.append((r, c))
                lattice.add_node(LatticeNode(idx, (r, c), "data"))
                idx += 1

        # Plaquette ancillas sit at half-integer positions (r+0.5, c+0.5)
        # The plaquette at (r+0.5, c+0.5) has corners: (r,c), (r,c+1), (r+1,c), (r+1,c+1)
        # But the surface code has boundaries, so edge plaquettes have fewer qubits.
        #
        # For the rotated surface code with d x d data qubits:
        # - X stabilizers on faces where (r + c) is even
        # - Z stabilizers on faces where (r + c) is odd
        # Faces range over r in [-1, d-1], c in [-1, d-1]
        # but only include faces with at least 2 data qubit corners.

        for fr in range(-1, d):
            for fc in range(-1, d):
                # Corners of the face at (fr+0.5, fc+0.5)
                corners = []
                for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    nr, nc = fr + dr, fc + dc
                    if 0 <= nr < d and 0 <= nc < d:
                        corners.append(self._data_index(nr, nc))

                if len(corners) < 2:
                    continue

                is_x_type = (fr + fc) % 2 == 0

                # Boundary conditions for the rotated surface code:
                # - X stabilizers don't appear on top/bottom boundaries
                # - Z stabilizers don't appear on left/right boundaries
                if is_x_type and (fr == -1 or fr == d - 1):
                    continue
                if not is_x_type and (fc == -1 or fc == d - 1):
                    continue

                # Use mapped coordinates for ancilla (doubled to avoid floats)
                a_coord = (2 * fr + 1, 2 * fc + 1)

                if is_x_type:
                    self._x_stabilizer_qubits.append(corners)
                    role = "ancilla_x"
                else:
                    self._z_stabilizer_qubits.append(corners)
                    role = "ancilla_z"

                lattice.add_node(LatticeNode(idx, a_coord, role))
                for dq in corners:
                    lattice.add_edge(LatticeEdge(idx, dq))
                idx += 1

        return lattice

    def stabilizer_generators(self) -> list[Stabilizer]:
        nd = self.num_data_qubits
        stabilizers = []

        for qubits in self._x_stabilizer_qubits:
            ps = np.zeros(nd, dtype=np.uint8)
            for q in qubits:
                ps[q] = PauliOp.X
            stabilizers.append(Stabilizer(ps, list(qubits), "X"))

        for qubits in self._z_stabilizer_qubits:
            ps = np.zeros(nd, dtype=np.uint8)
            for q in qubits:
                ps[q] = PauliOp.Z
            stabilizers.append(Stabilizer(ps, list(qubits), "Z"))

        return stabilizers

    def logical_operators(self) -> list[LogicalOperator]:
        d = self._distance
        nd = self.num_data_qubits

        # Logical X: X along the top row
        x_l = np.zeros(nd, dtype=np.uint8)
        for c in range(d):
            x_l[self._data_index(0, c)] = PauliOp.X

        # Logical Z: Z along the left column
        z_l = np.zeros(nd, dtype=np.uint8)
        for r in range(d):
            z_l[self._data_index(r, 0)] = PauliOp.Z

        return [
            LogicalOperator(x_l, "X_L"),
            LogicalOperator(z_l, "Z_L"),
        ]

    def check_matrix(self) -> np.ndarray:
        stabs = self.stabilizer_generators()
        nd = self.num_data_qubits
        H = np.zeros((len(stabs), nd), dtype=np.uint8)
        for i, stab in enumerate(stabs):
            for q in stab.qubits:
                H[i, q] = 1
        return H

    def syndrome_circuit(self, rounds: int = 1) -> Circuit:
        nd = self.num_data_qubits
        n_total = self.num_qubits
        circuit = Circuit(n_total)
        ancilla_start = nd

        for _ in range(rounds):
            # Reset all ancillas
            for a_idx in range(self.num_ancilla_qubits):
                circuit.reset(ancilla_start + a_idx)

            # X-stabilizer measurements
            for i, qubits in enumerate(self._x_stabilizer_qubits):
                a_global = ancilla_start + i
                circuit.h(a_global)
                for dq in qubits:
                    circuit.cx(a_global, dq)
                circuit.h(a_global)

            # Z-stabilizer measurements
            z_offset = len(self._x_stabilizer_qubits)
            for i, qubits in enumerate(self._z_stabilizer_qubits):
                a_global = ancilla_start + z_offset + i
                for dq in qubits:
                    circuit.cx(dq, a_global)

            # Measure all ancillas
            for a_idx in range(self.num_ancilla_qubits):
                circuit.measure(ancilla_start + a_idx)

        return circuit

    def qubit_coordinates(self) -> dict[int, Coordinate]:
        coords: dict[int, Coordinate] = {}
        for node in self._lattice.nodes:
            coords[node.index] = node.coordinate
        return coords
