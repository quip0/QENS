"""Tests for qens.core.circuit."""
from __future__ import annotations

import pytest

from qens.core.circuit import Gate, Moment, Circuit


class TestGate:
    def test_creation(self):
        g = Gate("H", (0,))
        assert g.name == "H"
        assert g.qubits == (0,)
        assert g.params == {}

    def test_frozen(self):
        g = Gate("CX", (0, 1))
        with pytest.raises(AttributeError):
            g.name = "CZ"  # type: ignore[misc]

    def test_with_params(self):
        g = Gate("RZ", (0,), params={"theta": 0.5})
        assert g.params["theta"] == pytest.approx(0.5)

    def test_repr(self):
        g = Gate("X", (2,))
        assert "X" in repr(g)
        assert "2" in repr(g)


class TestMoment:
    def test_empty(self):
        m = Moment()
        assert m.gates == []
        assert m.qubits_used == set()

    def test_add_gate(self):
        m = Moment()
        m.add(Gate("H", (0,)))
        assert len(m.gates) == 1
        assert 0 in m.qubits_used

    def test_parallel_gates(self):
        m = Moment()
        m.add(Gate("H", (0,)))
        m.add(Gate("H", (1,)))
        assert m.qubits_used == {0, 1}


class TestCircuit:
    def test_empty_circuit(self):
        c = Circuit(3)
        assert c.num_qubits == 3
        assert c.depth == 0
        assert c.moments == []

    def test_fluent_h(self):
        c = Circuit(2).h(0)
        assert c.depth == 1
        assert c.moments[0].gates[0].name == "H"

    def test_fluent_chaining(self):
        c = Circuit(3).h(0).cx(0, 1).cx(0, 2)
        assert isinstance(c, Circuit)
        assert c.num_qubits == 3

    def test_depth_parallel_gates(self):
        c = Circuit(3)
        c.append_gate(Gate("H", (0,)))
        c.append_gate(Gate("H", (1,)))  # non-overlapping, same moment
        assert c.depth == 1

    def test_depth_sequential_gates(self):
        c = Circuit(2)
        c.append_gate(Gate("H", (0,)))
        c.append_gate(Gate("CX", (0, 1)))  # overlaps qubit 0
        assert c.depth == 2

    def test_measure_all(self):
        c = Circuit(3).measure_all()
        assert c.depth == 1
        moment = c.moments[0]
        assert len(moment.gates) == 3
        assert all(g.name == "M" for g in moment.gates)

    def test_measure_single(self):
        c = Circuit(2).measure(1)
        assert c.moments[0].gates[0].qubits == (1,)

    def test_x_gate(self):
        c = Circuit(1).x(0)
        assert c.moments[0].gates[0].name == "X"

    def test_z_gate(self):
        c = Circuit(1).z(0)
        assert c.moments[0].gates[0].name == "Z"

    def test_cz_gate(self):
        c = Circuit(2).cz(0, 1)
        g = c.moments[0].gates[0]
        assert g.name == "CZ"
        assert g.qubits == (0, 1)

    def test_reset(self):
        c = Circuit(1).reset(0)
        assert c.moments[0].gates[0].name == "R"

    def test_append_moment(self):
        c = Circuit(2)
        m = Moment()
        m.add(Gate("H", (0,)))
        m.add(Gate("H", (1,)))
        c.append_moment(m)
        assert c.depth == 1

    def test_repr(self):
        c = Circuit(3).h(0)
        r = repr(c)
        assert "3" in r
        assert "1" in r
