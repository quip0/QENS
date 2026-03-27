"""Tests for qens.codes.color."""
from __future__ import annotations

import numpy as np
import pytest

from qens.codes.color import ColorCode


class TestColorCode3:
    def test_creates_valid_code(self, color3):
        assert color3.num_data_qubits > 0
        assert color3.num_ancilla_qubits > 0
        assert color3.code_distance == 3

    def test_css_property_same_support(self, color3):
        """X and Z stabilizers should act on the same plaquette supports."""
        stabs = color3.stabilizer_generators()
        # Stabilizers come in X/Z pairs on the same plaquette
        x_stabs = [s for s in stabs if s.stabilizer_type == "X"]
        z_stabs = [s for s in stabs if s.stabilizer_type == "Z"]
        assert len(x_stabs) == len(z_stabs), "Should have equal X and Z stabilizers"
        # Each X stabilizer support should appear as a Z stabilizer support
        x_supports = [frozenset(s.qubits) for s in x_stabs]
        z_supports = [frozenset(s.qubits) for s in z_stabs]
        assert sorted(x_supports, key=sorted) == sorted(z_supports, key=sorted)

    def test_supports_transversal_clifford(self, color3):
        assert color3.supports_transversal_clifford is True

    def test_check_matrix_shape(self, color3):
        H = color3.check_matrix()
        stabs = color3.stabilizer_generators()
        assert H.shape == (len(stabs), color3.num_data_qubits)

    def test_logical_operators(self, color3):
        logicals = color3.logical_operators()
        assert len(logicals) == 2

    def test_name(self, color3):
        assert "Color" in color3.name

    def test_syndrome_circuit(self, color3):
        circuit = color3.syndrome_circuit(rounds=1)
        assert circuit.num_qubits == color3.num_qubits
        assert circuit.depth > 0


class TestColorCodeEdgeCases:
    def test_distance_less_than_3_raises(self):
        with pytest.raises(ValueError):
            ColorCode(2)

    def test_even_distance_raises(self):
        with pytest.raises(ValueError, match="odd"):
            ColorCode(4)

    def test_invalid_lattice_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            ColorCode(3, lattice_type="9.9.9")

    def test_666_lattice(self):
        code = ColorCode(3, lattice_type="6.6.6")
        assert code.num_data_qubits > 0
        assert code.lattice_type == "6.6.6"
