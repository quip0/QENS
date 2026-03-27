"""Tests for qens.codes.surface."""
from __future__ import annotations

import numpy as np
import pytest

from qens.core.types import PauliOp
from qens.codes.surface import SurfaceCode
from qens.utils.pauli_algebra import symplectic_inner_product


class TestSurfaceCode3:
    def test_num_data_qubits(self, surface3):
        assert surface3.num_data_qubits == 9

    def test_num_stabilizers(self, surface3):
        stabs = surface3.stabilizer_generators()
        assert len(stabs) == 8  # 4 X-type + 4 Z-type

    def test_x_and_z_stabilizer_counts(self, surface3):
        stabs = surface3.stabilizer_generators()
        x_count = sum(1 for s in stabs if s.stabilizer_type == "X")
        z_count = sum(1 for s in stabs if s.stabilizer_type == "Z")
        assert x_count == 4
        assert z_count == 4

    def test_all_stabilizers_commute(self, surface3):
        stabs = surface3.stabilizer_generators()
        for i in range(len(stabs)):
            for j in range(i + 1, len(stabs)):
                assert symplectic_inner_product(
                    stabs[i].pauli_string, stabs[j].pauli_string
                ) == 0, f"Stabilizers {i} and {j} anticommute"

    def test_syndrome_single_x_error_center(self, surface3):
        # X error on the center qubit (index 4) should trigger at least one Z stabilizer
        error = np.zeros(9, dtype=np.uint8)
        error[4] = PauliOp.X
        syndrome = surface3.compute_syndrome(error)
        assert np.any(syndrome), "Center X error should produce non-trivial syndrome"

    def test_logical_operators_exist(self, surface3):
        logicals = surface3.logical_operators()
        assert len(logicals) == 2
        labels = {l.label for l in logicals}
        assert "X_L" in labels
        assert "Z_L" in labels

    def test_logical_operators_anticommute(self, surface3):
        logicals = surface3.logical_operators()
        x_l = next(l for l in logicals if l.label == "X_L")
        z_l = next(l for l in logicals if l.label == "Z_L")
        sip = symplectic_inner_product(x_l.pauli_string, z_l.pauli_string)
        assert sip == 1, "Logical X and Z should anticommute"

    def test_code_distance(self, surface3):
        assert surface3.code_distance == 3

    def test_check_matrix_shape(self, surface3):
        H = surface3.check_matrix()
        assert H.shape[0] == 8
        assert H.shape[1] == 9

    def test_syndrome_circuit(self, surface3):
        circuit = surface3.syndrome_circuit(rounds=1)
        assert circuit.num_qubits == surface3.num_qubits
        assert circuit.depth > 0


class TestSurfaceCodeEdgeCases:
    def test_distance_must_be_odd(self):
        with pytest.raises(ValueError, match="odd"):
            SurfaceCode(4)

    def test_distance_less_than_2_raises(self):
        with pytest.raises(ValueError):
            SurfaceCode(1)
