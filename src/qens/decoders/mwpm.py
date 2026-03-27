from __future__ import annotations

from typing import TYPE_CHECKING, Any
from collections import defaultdict
import heapq

import numpy as np

from qens.core.types import Syndrome, PauliOp
from qens.decoders.base import Decoder, DecoderResult

if TYPE_CHECKING:
    from qens.codes.base import QECCode


class MWPMDecoder(Decoder):
    """Minimum Weight Perfect Matching decoder.

    Pure Python implementation using a greedy matching heuristic on the
    decoding graph. For exact MWPM on larger codes, consider wrapping
    PyMatching as an external backend.

    The decoder builds a complete graph on syndrome defects with edge
    weights equal to the shortest path distance in the decoding graph,
    then finds a minimum weight perfect matching.
    """

    def __init__(self, code: QECCode) -> None:
        super().__init__(code)
        self._adjacency: dict[int, list[tuple[int, float, int]]] = defaultdict(list)
        self._stab_to_data: dict[tuple[int, int], list[int]] = {}
        self._n_stabs = 0
        self._boundary_node = -1

    def precompute(self) -> None:
        stabs = self._code.stabilizer_generators()
        self._n_stabs = len(stabs)
        self._boundary_node = self._n_stabs  # virtual boundary node

        stab_qubits: list[set[int]] = [set(s.qubits) for s in stabs]

        # Build decoding graph adjacency
        # Edges between same-type stabilizers sharing data qubits
        for i in range(len(stabs)):
            for j in range(i + 1, len(stabs)):
                if stabs[i].stabilizer_type != stabs[j].stabilizer_type:
                    continue
                shared = stab_qubits[i] & stab_qubits[j]
                if shared:
                    # Store which data qubits are along this edge
                    data_q = min(shared)  # Pick one representative
                    self._adjacency[i].append((j, 1.0, data_q))
                    self._adjacency[j].append((i, 1.0, data_q))
                    self._stab_to_data[(i, j)] = sorted(shared)
                    self._stab_to_data[(j, i)] = sorted(shared)

            # Boundary connections for weight-2 stabilizers
            if len(stabs[i].qubits) < 4:
                data_q = stabs[i].qubits[0]
                self._adjacency[i].append((self._boundary_node, 0.5, data_q))
                self._adjacency[self._boundary_node].append((i, 0.5, data_q))

        super().precompute()

    def _shortest_paths(
        self, source: int, targets: set[int]
    ) -> dict[int, tuple[float, list[int]]]:
        """Dijkstra from source to all targets. Returns {target: (dist, path)}."""
        dist: dict[int, float] = {source: 0.0}
        prev: dict[int, int] = {}
        visited: set[int] = set()
        heap: list[tuple[float, int]] = [(0.0, source)]

        while heap and targets - visited:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            for v, w, _ in self._adjacency[u]:
                nd = d + w
                if v not in dist or nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(heap, (nd, v))

        results: dict[int, tuple[float, list[int]]] = {}
        for t in targets:
            if t in dist:
                path = []
                node = t
                while node != source:
                    path.append(node)
                    node = prev[node]
                path.append(source)
                path.reverse()
                results[t] = (dist[t], path)
        return results

    def _greedy_matching(
        self, defects: list[int]
    ) -> list[tuple[int, int, float, list[int]]]:
        """Greedy minimum weight matching on defects.

        Returns list of (defect_a, defect_b, weight, path) tuples.
        """
        if not defects:
            return []

        # Include boundary node as a potential match target
        all_nodes = defects + [self._boundary_node]

        # Compute pairwise distances
        dist_matrix: dict[tuple[int, int], tuple[float, list[int]]] = {}
        for i, src in enumerate(all_nodes):
            targets = set(all_nodes[i + 1:])
            if targets:
                paths = self._shortest_paths(src, targets)
                for tgt, (d, p) in paths.items():
                    dist_matrix[(src, tgt)] = (d, p)
                    dist_matrix[(tgt, src)] = (d, list(reversed(p)))

        # Greedy matching: repeatedly pick the closest unmatched pair
        unmatched = set(defects)
        matching: list[tuple[int, int, float, list[int]]] = []

        while unmatched:
            best_dist = float("inf")
            best_pair = None
            best_path: list[int] = []

            for a in unmatched:
                for b in unmatched:
                    if a >= b:
                        continue
                    if (a, b) in dist_matrix:
                        d, p = dist_matrix[(a, b)]
                        if d < best_dist:
                            best_dist = d
                            best_pair = (a, b)
                            best_path = p

                # Also try matching to boundary
                if (a, self._boundary_node) in dist_matrix:
                    d, p = dist_matrix[(a, self._boundary_node)]
                    if d < best_dist:
                        best_dist = d
                        best_pair = (a, self._boundary_node)
                        best_path = p

            if best_pair is None:
                break

            a, b = best_pair
            matching.append((a, b, best_dist, best_path))
            unmatched.discard(a)
            unmatched.discard(b)

        return matching

    def decode(self, syndrome: Syndrome) -> DecoderResult:
        if not self._precomputed:
            self.precompute()

        nd = self._code.num_data_qubits
        correction = np.zeros(nd, dtype=np.uint8)

        defects = np.nonzero(syndrome)[0].tolist()
        if not defects:
            return DecoderResult(correction=correction, success=True)

        matching = self._greedy_matching(defects)

        stabs = self._code.stabilizer_generators()

        # Apply correction along each matched path
        for a, b, weight, path in matching:
            for k in range(len(path) - 1):
                u, v = path[k], path[k + 1]
                if u == self._boundary_node or v == self._boundary_node:
                    # Boundary edge: correct with the boundary stabilizer's qubit
                    stab_idx = u if v == self._boundary_node else v
                    if stab_idx < len(stabs):
                        q = stabs[stab_idx].qubits[0]
                        stab_type = stabs[stab_idx].stabilizer_type
                        pauli = PauliOp.X if stab_type == "Z" else PauliOp.Z
                        correction[q] ^= pauli
                else:
                    key = (u, v)
                    if key in self._stab_to_data:
                        q = self._stab_to_data[key][0]
                        stab_type = stabs[u].stabilizer_type
                        pauli = PauliOp.X if stab_type == "Z" else PauliOp.Z
                        correction[q] ^= pauli

        success = not self._code.is_logical_error(correction)
        return DecoderResult(
            correction=correction,
            success=success,
            metadata={
                "num_defects": len(defects),
                "matching": [(a, b, w) for a, b, w, _ in matching],
            },
        )

    def build_decoding_graph(self) -> dict[str, Any]:
        if not self._precomputed:
            self.precompute()
        nodes = list(range(self._n_stabs + 1))
        edges = []
        seen: set[tuple[int, int]] = set()
        for u, neighbors in self._adjacency.items():
            for v, w, dq in neighbors:
                pair = (min(u, v), max(u, v))
                if pair not in seen:
                    seen.add(pair)
                    edges.append({"from": u, "to": v, "weight": w, "data_qubit": dq})
        return {
            "nodes": nodes,
            "edges": edges,
            "boundary_nodes": [self._boundary_node],
        }
