"""Integration test: verify color code transversal Clifford property."""
from __future__ import annotations

from qens.codes.color import ColorCode


class TestColorTransversal:
    def test_supports_transversal_clifford_d3(self):
        code = ColorCode(3)
        assert code.supports_transversal_clifford is True

    def test_supports_transversal_clifford_d5(self):
        code = ColorCode(5)
        assert code.supports_transversal_clifford is True

    def test_code_is_valid(self):
        code = ColorCode(3)
        assert code.num_data_qubits > 0
        assert code.num_ancilla_qubits > 0
        stabs = code.stabilizer_generators()
        assert len(stabs) > 0
