from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from qens.core.types import QubitIndex


@dataclass(frozen=True)
class Gate:
    """A named gate applied to specific qubits."""
    name: str
    qubits: tuple[QubitIndex, ...]
    params: dict[str, float] = field(default_factory=dict)

    def __repr__(self) -> str:
        p = f", {self.params}" if self.params else ""
        return f"Gate({self.name}, {self.qubits}{p})"


@dataclass
class Moment:
    """A time-slice of parallel gates."""
    gates: list[Gate] = field(default_factory=list)

    def add(self, gate: Gate) -> None:
        self.gates.append(gate)

    @property
    def qubits_used(self) -> set[QubitIndex]:
        result: set[QubitIndex] = set()
        for g in self.gates:
            result.update(g.qubits)
        return result


class Circuit:
    """An ordered sequence of moments representing a quantum circuit.

    Supports a fluent builder API for convenience:
        circuit = Circuit(3).h(0).cx(0, 1).cx(0, 2).measure_all()
    """

    def __init__(self, num_qubits: int) -> None:
        self._num_qubits = num_qubits
        self._moments: list[Moment] = []

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def moments(self) -> list[Moment]:
        return list(self._moments)

    @property
    def depth(self) -> int:
        return len(self._moments)

    def append_gate(self, gate: Gate) -> None:
        """Append a gate. Creates a new moment if the last one uses overlapping qubits."""
        for q in gate.qubits:
            if not (0 <= q < self._num_qubits):
                raise ValueError(
                    f"Qubit index {q} is out of range for circuit with {self._num_qubits} qubits"
                )
        gate_qubits = set(gate.qubits)
        if self._moments and not gate_qubits & self._moments[-1].qubits_used:
            self._moments[-1].add(gate)
        else:
            moment = Moment()
            moment.add(gate)
            self._moments.append(moment)

    def append_moment(self, moment: Moment) -> None:
        self._moments.append(moment)

    # -- Fluent helpers --

    def h(self, qubit: QubitIndex) -> Self:
        self.append_gate(Gate("H", (qubit,)))
        return self

    def x(self, qubit: QubitIndex) -> Self:
        self.append_gate(Gate("X", (qubit,)))
        return self

    def z(self, qubit: QubitIndex) -> Self:
        self.append_gate(Gate("Z", (qubit,)))
        return self

    def cx(self, control: QubitIndex, target: QubitIndex) -> Self:
        self.append_gate(Gate("CX", (control, target)))
        return self

    def cz(self, q0: QubitIndex, q1: QubitIndex) -> Self:
        self.append_gate(Gate("CZ", (q0, q1)))
        return self

    def measure(self, qubit: QubitIndex) -> Self:
        self.append_gate(Gate("M", (qubit,)))
        return self

    def measure_all(self) -> Self:
        moment = Moment()
        for q in range(self._num_qubits):
            moment.add(Gate("M", (q,)))
        self._moments.append(moment)
        return self

    def reset(self, qubit: QubitIndex) -> Self:
        self.append_gate(Gate("R", (qubit,)))
        return self

    def __repr__(self) -> str:
        return f"Circuit(num_qubits={self._num_qubits}, depth={self.depth})"
