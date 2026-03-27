"""Smoke tests for qens.viz.circuit_diagram."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

from qens.core.circuit import Circuit
from qens.viz.circuit_diagram import draw_circuit
from qens.viz.base import FigureHandle


class TestDrawCircuit:
    def test_returns_figure_handle(self):
        circuit = Circuit(3).h(0).cx(0, 1).measure_all()
        handle = draw_circuit(circuit)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_error_locations(self):
        circuit = Circuit(2).h(0).cx(0, 1).measure_all()
        handle = draw_circuit(circuit, error_locations=[(0, 0)])
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_empty_circuit(self):
        circuit = Circuit(1)
        handle = draw_circuit(circuit)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_various_gates(self):
        circuit = Circuit(3).h(0).x(1).z(2).cx(0, 1).cz(1, 2).reset(0).measure_all()
        handle = draw_circuit(circuit)
        assert isinstance(handle, FigureHandle)
        handle.close()
