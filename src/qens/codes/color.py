from __future__ import annotations

import math
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
        self._data_coords: list[tuple[float, ...]] = []
        self._plaquettes: list[list[int]] = []
        self._coord_to_index: dict[tuple[float, ...], int] = {}
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
        """Verify all plaquettes have even weight."""
        for i, plaq in enumerate(self._plaquettes):
            if len(plaq) % 2 != 0:
                raise RuntimeError(
                    f"Plaquette {i} has odd weight {len(plaq)}."
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
        """Build a 4.8.8 color code on a centered hexagonal grid.

        For distance d, uses n = 3t^2 + 3t + 1 data qubits (t = (d-1)/2).
        Plaquettes are hexagonal neighborhoods (neighbors only, excluding
        center) for every vertex that has an even number of neighbors >= 4.
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
        hex_dirs = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

        # Build plaquettes using the color class that yields the most
        # non-overlapping, even-weight plaquettes.  Each plaquette is
        # the set of neighbors of a center vertex (center excluded).
        # Within one color class, same-class vertices are never adjacent,
        # so their neighborhoods overlap in at most 2 qubits (even).
        best_plaquettes: list[list[int]] = []
        for target_color in range(3):
            plaquettes: list[list[int]] = []
            for q, r in self._data_coords:
                if (q - r) % 3 != target_color:
                    continue
                neighbors = []
                for dq, dr in hex_dirs:
                    nb = (q + dq, r + dr)
                    if nb in ci:
                        neighbors.append(ci[nb])
                if len(neighbors) >= 4 and len(neighbors) % 2 == 0:
                    plaquettes.append(sorted(neighbors))
            if len(plaquettes) > len(best_plaquettes):
                best_plaquettes = plaquettes
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
    # 6.6.6 color code: honeycomb lattice in a triangular region
    # ------------------------------------------------------------------

    def _build_666(self) -> Lattice:
        """Build a 6.6.6 color code on a honeycomb lattice in a triangle.

        Places flat-top hexagonal cells in a triangular region.
        Data qubits sit at hexagon vertices; each hex cell is a plaquette.
        Boundary cells clipped to the triangle become 4-qubit plaquettes.
        """
        lattice = Lattice()
        d = self._distance
        t = (d - 1) // 2
        sqrt3 = math.sqrt(3)
        S = 3 * t  # triangle side length

        # Triangle: A=(0,0), B=(S,0), C=(S/2, S*sqrt3/2)
        def in_tri(x: float, y: float, eps: float = 1e-6) -> bool:
            return (y >= -eps
                    and sqrt3 * x - y >= -eps
                    and sqrt3 * (S - x) - y >= -eps)

        # Flat-top hex vertices (edge length 1) around center (cx, cy)
        def hex_verts(cx: float, cy: float) -> list[tuple[float, float]]:
            return [
                (cx + 1, cy),
                (cx + 0.5, cy + sqrt3 / 2),
                (cx - 0.5, cy + sqrt3 / 2),
                (cx - 1, cy),
                (cx - 0.5, cy - sqrt3 / 2),
                (cx + 0.5, cy - sqrt3 / 2),
            ]

        # Hex cell centers form a triangular lattice with basis
        # a1 = (1.5, sqrt3/2), a2 = (0, sqrt3).
        # Bottom row has centers at cy = sqrt3/2 so bottom edges sit at y=0.
        cells: list[tuple[float, float]] = []
        for i in range(-t - 1, 3 * t + 2):
            for j in range(-t - 1, 2 * t + 2):
                cx = 1.5 * i
                cy = sqrt3 * (i / 2.0 + j)
                if in_tri(cx, cy, eps=1.2):
                    cells.append((cx, cy))

        # Collect unique vertices inside the triangle
        vtx_map: dict[tuple[float, float], int] = {}
        coord_list: list[tuple[float, float]] = []
        idx = 0

        cell_vertex_indices: list[list[int]] = []

        for cx, cy in cells:
            verts = hex_verts(cx, cy)
            cell_v: list[int] = []
            for vx, vy in verts:
                if not in_tri(vx, vy, eps=0.02):
                    continue
                key = (round(vx, 4), round(vy, 4))
                if key not in vtx_map:
                    vtx_map[key] = idx
                    coord_list.append((vx, vy))
                    idx += 1
                if vtx_map[key] not in cell_v:
                    cell_v.append(vtx_map[key])
            cell_vertex_indices.append(cell_v)

        # Each cell with even weight >= 4 becomes a plaquette
        seen_plaq: set[tuple[int, ...]] = set()
        for cv in cell_vertex_indices:
            if len(cv) >= 4 and len(cv) % 2 == 0:
                key = tuple(sorted(cv))
                if key not in seen_plaq:
                    seen_plaq.add(key)
                    self._plaquettes.append(sorted(cv))

        # Store data coords
        self._data_coords = coord_list  # type: ignore[assignment]
        self._coord_to_index = {  # type: ignore[assignment]
            (round(x, 4), round(y, 4)): i for i, (x, y) in enumerate(coord_list)
        }

        nd = len(coord_list)
        for i, (x, y) in enumerate(coord_list):
            lattice.add_node(LatticeNode(i, (x, y), "data"))

        # Ancilla nodes at plaquette centroids
        for p_idx, plaq in enumerate(self._plaquettes):
            pcoords = [coord_list[q] for q in plaq]
            cr = sum(c[0] for c in pcoords) / len(pcoords)
            cc = sum(c[1] for c in pcoords) / len(pcoords)
            a_idx = nd + p_idx
            lattice.add_node(LatticeNode(a_idx, (cr, cc), "ancilla"))
            for q in plaq:
                lattice.add_edge(LatticeEdge(a_idx, q))

        # Data-data edges: connect vertices within distance ~1 (hex edge)
        for i in range(nd):
            for j in range(i + 1, nd):
                xi, yi = coord_list[i]
                xj, yj = coord_list[j]
                if math.hypot(xi - xj, yi - yj) < 1.05:
                    lattice.add_edge(LatticeEdge(i, j))

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
