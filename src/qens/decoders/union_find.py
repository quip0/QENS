from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from qens.core.types import Syndrome, PauliOp
from qens.decoders.base import Decoder, DecoderResult

if TYPE_CHECKING:
    from qens.codes.base import QECCode


class _UFNode:
    """Union-Find node with weighted union and path compression."""
    __slots__ = ("parent", "rank", "size", "boundary")

    def __init__(self, boundary: bool = False) -> None:
        self.parent: int = -1  # -1 means self is root
        self.rank: int = 0
        self.size: int = 1
        self.boundary: bool = boundary


class UnionFindDecoder(Decoder):
    """Union-Find decoder for topological codes.

    Uses a growth + fusion strategy:
    1. Build a decoding graph from the code's check matrix
    2. Grow clusters around syndrome defects
    3. Fuse clusters using weighted union-find
    4. Extract correction from fused cluster structure

    Based on: Delfosse & Nickerson, "Almost-linear time decoding algorithm
    for topological codes" (2021).
    """

    def __init__(self, code: QECCode) -> None:
        super().__init__(code)
        self._graph_nodes: list[int] = []
        self._graph_edges: list[tuple[int, int, float]] = []
        self._boundary_nodes: set[int] = set()
        self._num_stabilizers = 0

    def precompute(self) -> None:
        """Build the decoding graph from the code's check matrix."""
        stabs = self._code.stabilizer_generators()
        self._num_stabilizers = len(stabs)

        # Build adjacency: two stabilizers are connected if they share a data qubit
        stab_qubits: list[set[int]] = [set(s.qubits) for s in stabs]

        self._graph_nodes = list(range(len(stabs)))

        # Add a virtual boundary node
        boundary_idx = len(stabs)
        self._boundary_nodes = {boundary_idx}

        edges: list[tuple[int, int, float]] = []
        # Edges between stabilizers that share data qubits
        for i in range(len(stabs)):
            for j in range(i + 1, len(stabs)):
                # Only connect same-type stabilizers
                if stabs[i].stabilizer_type != stabs[j].stabilizer_type:
                    continue
                shared = stab_qubits[i] & stab_qubits[j]
                if shared:
                    edges.append((i, j, 1.0))

            # Connect boundary stabilizers to the virtual boundary
            # A stabilizer is on the boundary if it has weight < 4 (for surface codes)
            if len(stabs[i].qubits) < 4:
                edges.append((i, boundary_idx, 0.5))

        self._graph_edges = edges
        super().precompute()

    def _find(self, nodes: list[_UFNode], x: int) -> int:
        """Find root with path compression."""
        root = x
        while nodes[root].parent != -1:
            root = nodes[root].parent
        # Path compression
        while nodes[x].parent != -1:
            nodes[x].parent, x = root, nodes[x].parent
        return root

    def _union(self, nodes: list[_UFNode], a: int, b: int) -> int:
        """Union by rank, returns new root."""
        ra, rb = self._find(nodes, a), self._find(nodes, b)
        if ra == rb:
            return ra
        if nodes[ra].rank < nodes[rb].rank:
            ra, rb = rb, ra
        nodes[rb].parent = ra
        nodes[ra].size += nodes[rb].size
        nodes[ra].boundary = nodes[ra].boundary or nodes[rb].boundary
        if nodes[ra].rank == nodes[rb].rank:
            nodes[ra].rank += 1
        return ra

    def decode(self, syndrome: Syndrome) -> DecoderResult:
        if not self._precomputed:
            self.precompute()

        nd = self._code.num_data_qubits
        n_stabs = self._num_stabilizers
        correction = np.zeros(nd, dtype=np.uint8)

        # Find defect locations (non-zero syndrome bits)
        defects = set(np.nonzero(syndrome)[0].tolist())
        if not defects:
            return DecoderResult(correction=correction, success=True)

        # Initialize UF nodes: one per stabilizer + boundary
        num_nodes = n_stabs + 1
        nodes = [_UFNode() for _ in range(num_nodes)]
        for b in self._boundary_nodes:
            if b < num_nodes:
                nodes[b].boundary = True

        # Sort edges by weight
        sorted_edges = sorted(self._graph_edges, key=lambda e: e[2])

        # Growth phase: fuse clusters along edges
        for u, v, w in sorted_edges:
            ru, rv = self._find(nodes, u), self._find(nodes, v)
            if ru == rv:
                continue

            # Count defects in each cluster
            u_has_defect = any(
                self._find(nodes, d) == ru for d in defects
            )
            v_has_defect = any(
                self._find(nodes, d) == rv for d in defects
            )

            # Fuse if both clusters have odd parity or one touches boundary
            u_odd = u_has_defect
            v_odd = v_has_defect

            if u_odd or v_odd:
                self._union(nodes, u, v)

        # Peeling phase: extract correction along edges connecting defects
        # Simple approach: for each defect pair that got fused, find a path
        # and flip the corresponding data qubits
        stabs = self._code.stabilizer_generators()

        # Build correction from matched defects
        # For each edge that connects two defects in the same cluster,
        # add the corresponding data qubit to the correction
        for u, v, w in sorted_edges:
            if u >= n_stabs or v >= n_stabs:
                continue
            if self._find(nodes, u) == self._find(nodes, v):
                if u in defects or v in defects:
                    shared = set(stabs[u].qubits) & set(stabs[v].qubits)
                    for q in shared:
                        stab_type = stabs[u].stabilizer_type
                        pauli = PauliOp.X if stab_type == "Z" else PauliOp.Z
                        correction[q] ^= pauli

        success = not self._code.is_logical_error(correction)
        return DecoderResult(
            correction=correction,
            success=success,
            metadata={"num_defects": len(defects)},
        )

    def build_decoding_graph(self) -> dict[str, Any]:
        if not self._precomputed:
            self.precompute()
        return {
            "nodes": self._graph_nodes,
            "edges": [(u, v, w) for u, v, w in self._graph_edges],
            "boundary_nodes": list(self._boundary_nodes),
        }
