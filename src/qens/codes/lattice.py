from __future__ import annotations

from dataclasses import dataclass

from qens.core.types import Coordinate


@dataclass(frozen=True)
class LatticeNode:
    """A node in a code lattice."""
    index: int
    coordinate: Coordinate
    role: str  # "data", "ancilla_x", "ancilla_z", "ancilla"

    def __repr__(self) -> str:
        return f"Node({self.index}, {self.coordinate}, {self.role})"


@dataclass(frozen=True)
class LatticeEdge:
    """An edge connecting two lattice nodes."""
    node_a: int
    node_b: int
    weight: float = 1.0

    def __repr__(self) -> str:
        return f"Edge({self.node_a}-{self.node_b})"


class Lattice:
    """A lattice structure for topological codes.

    Provides neighbor queries, coordinate lookups, and iteration
    over nodes/edges used by codes and visualizers.
    """

    def __init__(self) -> None:
        self._nodes: dict[int, LatticeNode] = {}
        self._edges: list[LatticeEdge] = []
        self._adjacency: dict[int, list[int]] = {}

    def add_node(self, node: LatticeNode) -> None:
        self._nodes[node.index] = node
        if node.index not in self._adjacency:
            self._adjacency[node.index] = []

    def add_edge(self, edge: LatticeEdge) -> None:
        self._edges.append(edge)
        self._adjacency.setdefault(edge.node_a, []).append(edge.node_b)
        self._adjacency.setdefault(edge.node_b, []).append(edge.node_a)

    def get_node(self, index: int) -> LatticeNode:
        return self._nodes[index]

    @property
    def nodes(self) -> list[LatticeNode]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[LatticeEdge]:
        return list(self._edges)

    def neighbors(self, index: int) -> list[int]:
        return list(self._adjacency.get(index, []))

    def data_nodes(self) -> list[LatticeNode]:
        return [n for n in self._nodes.values() if n.role == "data"]

    def ancilla_nodes(self) -> list[LatticeNode]:
        return [n for n in self._nodes.values() if n.role != "data"]

    def __repr__(self) -> str:
        return f"Lattice(nodes={len(self._nodes)}, edges={len(self._edges)})"
