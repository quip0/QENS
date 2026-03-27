"""Tests for qens.codes.repetition."""
from __future__ import annotations

import numpy as np
import pytest

from qens.core.types import PauliOp
from qens.codes.repetition import RepetitionCode
from qens.utils.pauli_algebra import symplectic_inner_product


class TestRepetitionCode3:
    def test_num_data_qubits(self, rep3):
        assert rep3.num_data_qubits == 3

    def test_num_ancilla_qubits(self, rep3):
        assert rep3.num_ancilla_qubits == 2

    def test_num_stabilizers(self, rep3):
        assert len(rep3.stabilizer_generators()) == 2

    def test_check_matrix(self, rep3):
        H = rep3.check_matrix()
        expected = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
        np.testing.assert_array_equal(H, expected)

    def test_code_distance(self, rep3):
        assert rep3.code_distance == 3

    def test_stabilizers_commute(self, rep3):
        stabs = rep3.stabilizer_generators()
        for i in range(len(stabs)):
            for j in range(i + 1, len(stabs)):
                assert symplectic_inner_product(
                    stabs[i].pauli_string, stabs[j].pauli_string
                ) == 0

    def test_syndrome_single_x_error(self, rep3):
        # X error on qubit 0 should trigger stabilizer 0 only
        error = np.zeros(3, dtype=np.uint8)
        error[0] = PauliOp.X
        syndrome = rep3.compute_syndrome(error)
        assert syndrome[0] == 1
        assert syndrome[1] == 0

    def test_syndrome_single_x_error_middle(self, rep3):
        # X error on qubit 1 should trigger both stabilizers
        error = np.zeros(3, dtype=np.uint8)
        error[1] = PauliOp.X
        syndrome = rep3.compute_syndrome(error)
        assert syndrome[0] == 1
        assert syndrome[1] == 1

    def test_syndrome_circuit_depth(self, rep3):
        circuit = rep3.syndrome_circuit(rounds=1)
        assert circuit.num_qubits == 5  # 3 data + 2 ancilla
        assert circuit.depth > 0


class TestRepetitionCode5:
    def test_num_data_qubits(self, rep5):
        assert rep5.num_data_qubits == 5

    def test_num_ancilla_qubits(self, rep5):
        assert rep5.num_ancilla_qubits == 4

    def test_num_stabilizers(self, rep5):
        assert len(rep5.stabilizer_generators()) == 4

    def test_code_distance(self, rep5):
        assert rep5.code_distance == 5

    def test_stabilizers_commute(self, rep5):
        stabs = rep5.stabilizer_generators()
        for i in range(len(stabs)):
            for j in range(i + 1, len(stabs)):
                assert symplectic_inner_product(
                    stabs[i].pauli_string, stabs[j].pauli_string
                ) == 0

    def test_check_matrix_shape(self, rep5):
        H = rep5.check_matrix()
        assert H.shape == (4, 5)


class TestRepetitionCodeEdgeCases:
    def test_distance_2(self):
        code = RepetitionCode(2)
        assert code.num_data_qubits == 2
        assert code.num_ancilla_qubits == 1

    def test_distance_less_than_2_raises(self):
        with pytest.raises(ValueError):
            RepetitionCode(1)

    def test_logical_operators(self, rep3):
        logicals = rep3.logical_operators()
        assert len(logicals) == 2
        labels = {l.label for l in logicals}
        assert "X_L" in labels
        assert "Z_L" in labels
