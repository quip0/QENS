"""Tests for qens.simulation.frame (PauliFrameSimulator)."""
from __future__ import annotations

import numpy as np

from qens.core.types import PauliOp
from qens.core.circuit import Gate
from qens.simulation.frame import PauliFrameSimulator


class TestPauliFrameSimulator:
    def test_initial_frame_is_identity(self):
        sim = PauliFrameSimulator(3)
        assert np.all(sim.frame == PauliOp.I)

    def test_apply_error(self):
        sim = PauliFrameSimulator(3)
        error = np.array([PauliOp.X, PauliOp.I, PauliOp.Z], dtype=np.uint8)
        sim.apply_error(error)
        assert sim.frame[0] == PauliOp.X
        assert sim.frame[1] == PauliOp.I
        assert sim.frame[2] == PauliOp.Z

    def test_hadamard_x_to_z(self):
        sim = PauliFrameSimulator(1)
        error = np.array([PauliOp.X], dtype=np.uint8)
        sim.apply_error(error)
        sim.propagate_gate(Gate("H", (0,)))
        assert sim.frame[0] == PauliOp.Z

    def test_hadamard_z_to_x(self):
        sim = PauliFrameSimulator(1)
        error = np.array([PauliOp.Z], dtype=np.uint8)
        sim.apply_error(error)
        sim.propagate_gate(Gate("H", (0,)))
        assert sim.frame[0] == PauliOp.X

    def test_hadamard_y_stays_y(self):
        sim = PauliFrameSimulator(1)
        error = np.array([PauliOp.Y], dtype=np.uint8)
        sim.apply_error(error)
        sim.propagate_gate(Gate("H", (0,)))
        assert sim.frame[0] == PauliOp.Y

    def test_cx_x_propagates_forward(self):
        """X on control propagates to target: XI -> XX"""
        sim = PauliFrameSimulator(2)
        error = np.array([PauliOp.X, PauliOp.I], dtype=np.uint8)
        sim.apply_error(error)
        sim.propagate_gate(Gate("CX", (0, 1)))
        assert sim.frame[0] == PauliOp.X
        assert sim.frame[1] == PauliOp.X

    def test_cx_z_propagates_backward(self):
        """Z on target propagates to control: IZ -> ZZ"""
        sim = PauliFrameSimulator(2)
        error = np.array([PauliOp.I, PauliOp.Z], dtype=np.uint8)
        sim.apply_error(error)
        sim.propagate_gate(Gate("CX", (0, 1)))
        assert sim.frame[0] == PauliOp.Z
        assert sim.frame[1] == PauliOp.Z

    def test_cz_x_adds_z(self):
        """CZ: X on q0 adds Z to q1"""
        sim = PauliFrameSimulator(2)
        error = np.array([PauliOp.X, PauliOp.I], dtype=np.uint8)
        sim.apply_error(error)
        sim.propagate_gate(Gate("CZ", (0, 1)))
        assert sim.frame[0] == PauliOp.X
        assert sim.frame[1] == PauliOp.Z

    def test_cz_symmetric(self):
        """CZ: X on q1 adds Z to q0"""
        sim = PauliFrameSimulator(2)
        error = np.array([PauliOp.I, PauliOp.X], dtype=np.uint8)
        sim.apply_error(error)
        sim.propagate_gate(Gate("CZ", (0, 1)))
        assert sim.frame[0] == PauliOp.Z
        assert sim.frame[1] == PauliOp.X

    def test_reset_clears_frame(self):
        sim = PauliFrameSimulator(2)
        error = np.array([PauliOp.X, PauliOp.Z], dtype=np.uint8)
        sim.apply_error(error)
        sim.reset()
        assert np.all(sim.frame == PauliOp.I)

    def test_measure_x_error(self):
        sim = PauliFrameSimulator(1)
        error = np.array([PauliOp.X], dtype=np.uint8)
        sim.apply_error(error)
        assert sim.measure(0) == 1

    def test_measure_z_error(self):
        sim = PauliFrameSimulator(1)
        error = np.array([PauliOp.Z], dtype=np.uint8)
        sim.apply_error(error)
        assert sim.measure(0) == 0

    def test_measure_y_error(self):
        sim = PauliFrameSimulator(1)
        error = np.array([PauliOp.Y], dtype=np.uint8)
        sim.apply_error(error)
        assert sim.measure(0) == 1

    def test_measure_no_error(self):
        sim = PauliFrameSimulator(1)
        assert sim.measure(0) == 0

    def test_propagate_circuit(self):
        from qens.core.circuit import Circuit
        sim = PauliFrameSimulator(2)
        error = np.array([PauliOp.X, PauliOp.I], dtype=np.uint8)
        sim.apply_error(error)
        circuit = Circuit(2).h(0).cx(0, 1)
        sim.propagate_circuit(circuit)
        # X -> H -> Z, then CX with Z on control: ZI -> ZI (Z on ctrl doesn't propagate)
        assert sim.frame[0] == PauliOp.Z
        assert sim.frame[1] == PauliOp.I
