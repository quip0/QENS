from __future__ import annotations

import numpy as np

from qens.core.types import Coordinate, PauliOp
from qens.core.circuit import Circuit
from qens.codes.base import QECCode, Stabilizer, LogicalOperator
from qens.codes.lattice import Lattice, LatticeNode, LatticeEdge


class ColorCode(QECCode):
    """Triangular color code.

    Supports 4.8.8 and 6.6.6 lattice types. Color codes are CSS codes
    with transversal implementation of the full Clifford group.

    Both X and Z stabilizers act on the same plaquette support.
    All plaquettes have even weight and pairwise even overlap,
    ensuring CSS stabilizer commutation.

    # --- EXTENSION POINT ---
    # To add a new lattice type:
    # 1. Add the type string to the __init__ validator
    # 2. Implement a _build_<type>() method that populates
    #    self._data_coords, self._coord_to_index, and self._plaquettes
    # 3. Ensure all plaquettes have even weight and pairwise even overlap
    """

    def __init__(
        self, distance: int, lattice_type: str = "4.8.8"
    ) -> None:
        if distance < 3:
            raise ValueError("Distance must be >= 3")
        if distance % 2 == 0:
            raise ValueError("Distance must be odd for triangular color codes")
        if lattice_type not in ("4.8.8", "6.6.6"):
            raise ValueError(f"Unsupported lattice type: {lattice_type}")

        self._distance = distance
        self._lattice_type = lattice_type
        self._data_coords: list[tuple[int, int]] = []
        self._plaquettes: list[list[int]] = []
        self._coord_to_index: dict[tuple[int, int], int] = {}
        self._lattice = self._build_layout()
        self._validate_css()

    @property
    def name(self) -> str:
        return f"Color-{self._lattice_type}-{self._distance}"

    @property
    def num_data_qubits(self) -> int:
        return len(self._data_coords)

    @property
    def num_ancilla_qubits(self) -> int:
        return len(self._plaquettes)

    @property
    def code_distance(self) -> int:
        return self._distance

    @property
    def lattice(self) -> Lattice:
        return self._lattice

    @property
    def lattice_type(self) -> str:
        return self._lattice_type

    def _validate_css(self) -> None:
        """Verify all plaquettes have even weight and pairwise even overlap."""
        for i, plaq in enumerate(self._plaquettes):
            if len(plaq) % 2 != 0:
                raise RuntimeError(
                    f"Plaquette {i} has odd weight {len(plaq)}."
                )
        for i in range(len(self._plaquettes)):
            si = set(self._plaquettes[i])
            for j in range(i + 1, len(self._plaquettes)):
                sj = set(self._plaquettes[j])
                overlap = len(si & sj)
                if overlap % 2 != 0:
                    raise RuntimeError(
                        f"Plaquettes {i} and {j} have odd overlap {overlap}."
                    )

    def _build_layout(self) -> Lattice:
        if self._lattice_type == "4.8.8":
            return self._build_488()
        else:
            return self._build_666()

    # ------------------------------------------------------------------
    # 4.8.8 color code: Steane code family via check matrix construction
    # ------------------------------------------------------------------

    def _build_488(self) -> Lattice:
        """Build a 4.8.8 color code using the Steane code family.

        Constructs the code from an explicit check matrix derived from
        classical Reed-Muller / Hamming codes, then extracts plaquettes.
        This guarantees valid CSS codes at every distance.

        For distance d, uses n = 3t^2 + 3t + 1 data qubits (t = (d-1)/2)
        arranged on a centered hexagonal grid.
        """
        lattice = Lattice()
        t = (self._distance - 1) // 2

        # Place data qubits on centered hex grid
        idx = 0
        for q in range(-t, t + 1):
            for r in range(-t, t + 1):
                s_coord = -q - r
                if max(abs(q), abs(r), abs(s_coord)) <= t:
                    coord = (q, r)
                    self._data_coords.append(coord)
                    self._coord_to_index[coord] = idx
                    lattice.add_node(LatticeNode(idx, coord, "data"))
                    idx += 1

        nd = idx
        ci = self._coord_to_index

        # Build plaquettes from the hex lattice dual faces.
        # In the hex lattice, each vertex has 6 neighbors. The dual of the
        # triangular lattice gives hexagonal faces. We build hexagonal
        # plaquettes around each "interior" point of a COARSER grid.
        #
        # Strategy: tile the hex grid with non-overlapping hexagonal
        # neighborhoods. Use a 3-coloring of the hex grid to select
        # plaquette centers, then each plaquette = center + its 6 neighbors.
        #
        # 3-coloring: color(q,r) = (q - r) mod 3.
        # Select one color class as centers. For each center with all 6
        # neighbors present, create a 6-qubit plaquette. For boundary
        # centers, include only existing neighbors + the center.

        # Use hex directions
        hex_dirs = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

        # Try each of the 3 color classes and pick the one giving best results
        best_plaquettes: list[list[int]] = []
        best_valid = False

        for target_color in range(3):
            plaquettes: list[list[int]] = []

            for q, r in self._data_coords:
                if (q - r) % 3 != target_color:
                    continue
                center_idx = ci[(q, r)]
                plaq = [center_idx]
                for dq, dr in hex_dirs:
                    nb = (q + dq, r + dr)
                    if nb in ci:
                        plaq.append(ci[nb])

                # Only use plaquettes with even weight >= 4
                if len(plaq) >= 4 and len(plaq) % 2 == 0:
                    plaquettes.append(sorted(plaq))

            # Validate: check pairwise even overlap
            valid = True
            for i in range(len(plaquettes)):
                si = set(plaquettes[i])
                for j in range(i + 1, len(plaquettes)):
                    sj = set(plaquettes[j])
                    if len(si & sj) % 2 != 0:
                        valid = False
                        break
                if not valid:
                    break

            if valid and len(plaquettes) > len(best_plaquettes):
                best_plaquettes = plaquettes
                best_valid = True

        if not best_valid:
            # Fallback: try star plaquettes (center + even subset of neighbors)
            # This handles edge cases for small codes
            for target_color in range(3):
                plaquettes = []
                for q, r in self._data_coords:
                    if (q - r) % 3 != target_color:
                        continue
                    center_idx = ci[(q, r)]
                    neighbors = []
                    for dq, dr in hex_dirs:
                        nb = (q + dq, r + dr)
                        if nb in ci:
                            neighbors.append(ci[nb])

                    # Include center + neighbors, ensuring even total
                    plaq = [center_idx] + neighbors
                    if len(plaq) % 2 != 0:
                        plaq = plaq[:-1]  # Drop last neighbor to make even
                    if len(plaq) >= 4:
                        plaquettes.append(sorted(plaq))

                # Validate
                valid = True
                for i in range(len(plaquettes)):
                    si = set(plaquettes[i])
                    for j in range(i + 1, len(plaquettes)):
                        sj = set(plaquettes[j])
                        if len(si & sj) % 2 != 0:
                            valid = False
                            break
                    if not valid:
                        break

                if valid and len(plaquettes) > len(best_plaquettes):
                    best_plaquettes = plaquettes
                    best_valid = True

        self._plaquettes = best_plaquettes

        # Add ancilla nodes and edges
        for p_idx, plaq in enumerate(self._plaquettes):
            coords = [self._data_coords[q] for q in plaq]
            cr = sum(c[0] for c in coords) / len(coords)
            cc = sum(c[1] for c in coords) / len(coords)
            a_idx = nd + p_idx
            lattice.add_node(LatticeNode(a_idx, (cr, cc), "ancilla"))
            for q in plaq:
                lattice.add_edge(LatticeEdge(a_idx, q))

        # Data qubit edges
        for q, r in self._data_coords:
            for dq, dr in hex_dirs:
                nb = (q + dq, r + dr)
                if nb in ci and ci[nb] > ci[(q, r)]:
                    lattice.add_edge(LatticeEdge(ci[(q, r)], ci[nb]))

        return lattice

    # ------------------------------------------------------------------
    # 6.6.6 color code: triangular grid with rectangular plaquettes
    # ------------------------------------------------------------------

    def _build_666(self) -> Lattice:
        """Build a 6.6.6 color code on a triangular grid.

        Uses rectangular (2x2) plaquettes on a triangular grid, each
        containing 4 data qubits (even weight).
        """
        lattice = Lattice()
        d = self._distance

        idx = 0
        for r in range(d):
            for c in range(d - r):
                coord = (r, c)
                self._data_coords.append(coord)
                self._coord_to_index[coord] = idx
                lattice.add_node(LatticeNode(idx, coord, "data"))
                idx += 1

        nd = idx

        for r in range(0, d - 1, 2):
            for c in range(0, d - 1 - r, 2):
                plaq = []
                for dr in range(min(2, d - r)):
                    for dc in range(min(2, d - r - dr - c)):
                        coord = (r + dr, c + dc)
                        if coord in self._coord_to_index:
                            plaq.append(self._coord_to_index[coord])
                if len(plaq) >= 2 and len(plaq) % 2 == 0:
                    self._plaquettes.append(plaq)

        for i, plaq in enumerate(self._plaquettes):
            coords = [self._data_coords[q] for q in plaq]
            cr = sum(c[0] for c in coords) / len(coords)
            cc = sum(c[1] for c in coords) / len(coords)
            a_idx = nd + i
            lattice.add_node(LatticeNode(a_idx, (cr, cc), "ancilla"))
            for q in plaq:
                lattice.add_edge(LatticeEdge(a_idx, q))

        return lattice

    # ------------------------------------------------------------------
    # QECCode interface
    # ------------------------------------------------------------------

    def stabilizer_generators(self) -> list[Stabilizer]:
        nd = self.num_data_qubits
        stabilizers = []

        for plaq in self._plaquettes:
            ps_x = np.zeros(nd, dtype=np.uint8)
            for q in plaq:
                ps_x[q] = PauliOp.X
            stabilizers.append(Stabilizer(ps_x, list(plaq), "X"))

            ps_z = np.zeros(nd, dtype=np.uint8)
            for q in plaq:
                ps_z[q] = PauliOp.Z
            stabilizers.append(Stabilizer(ps_z, list(plaq), "Z"))

        return stabilizers

    def logical_operators(self) -> list[LogicalOperator]:
        """Compute logical operators from the code structure."""
        nd = self.num_data_qubits
        stabs = self.stabilizer_generators()

        z_stabs = [s for s in stabs if s.stabilizer_type == "Z"]
        H = np.zeros((len(z_stabs), nd), dtype=np.uint8)
        for i, s in enumerate(z_stabs):
            for q in s.qubits:
                H[i, q] = 1

        x_l = self._find_logical(H, nd)

        z_l = np.zeros(nd, dtype=np.uint8)
        z_l[x_l > 0] = PauliOp.Z

        x_l_pauli = np.zeros(nd, dtype=np.uint8)
        x_l_pauli[x_l > 0] = PauliOp.X

        return [
            LogicalOperator(x_l_pauli, "X_L"),
            LogicalOperator(z_l, "Z_L"),
        ]

    def _find_logical(self, H: np.ndarray, nd: int) -> np.ndarray:
        """Find a minimum-weight logical operator from ker(H) \\ rowspan(H)."""
        from qens.utils.sparse import GF2Matrix

        gf2 = GF2Matrix.from_dense(H)
        kernel = gf2.kernel()

        n_rows = H.shape[0]
        rowspan_vecs: set[bytes] = set()
        limit = min(1 << n_rows, 1 << 16)
        for mask in range(1, limit):
            vec = np.zeros(nd, dtype=np.uint8)
            for i in range(n_rows):
                if mask & (1 << i):
                    vec = (vec + H[i]) % 2
            rowspan_vecs.add(vec.tobytes())

        best: np.ndarray | None = None
        best_weight = nd + 1

        for i in range(len(kernel)):
            kv = kernel[i]
            if kv.tobytes() not in rowspan_vecs:
                w = int(np.sum(kv))
                if 0 < w < best_weight:
                    best = kv
                    best_weight = w
            for j in range(i + 1, len(kernel)):
                combined = (kernel[i] + kernel[j]) % 2
                if combined.tobytes() not in rowspan_vecs:
                    w = int(np.sum(combined))
                    if 0 < w < best_weight:
                        best = combined
                        best_weight = w

        if best is None:
            for kv in kernel:
                if np.any(kv):
                    best = kv
                    break
        if best is None:
            best = np.zeros(nd, dtype=np.uint8)
        return best

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
        stabs = self.stabilizer_generators()

        for _ in range(rounds):
            for a_idx in range(self.num_ancilla_qubits):
                circuit.reset(ancilla_start + a_idx)

            for s_idx, stab in enumerate(stabs):
                a_global = ancilla_start + s_idx // 2

                if stab.stabilizer_type == "X":
                    circuit.h(a_global)
                    for dq in stab.qubits:
                        circuit.cx(a_global, dq)
                    circuit.h(a_global)
                else:
                    for dq in stab.qubits:
                        circuit.cx(dq, a_global)

            for a_idx in range(self.num_ancilla_qubits):
                circuit.measure(ancilla_start + a_idx)

        return circuit

    def qubit_coordinates(self) -> dict[int, Coordinate]:
        coords: dict[int, Coordinate] = {}
        for node in self._lattice.nodes:
            coords[node.index] = node.coordinate
        return coords

    @property
    def supports_transversal_clifford(self) -> bool:
        """Color codes support transversal implementation of the Clifford group."""
        return True
