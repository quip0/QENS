"""Smoke tests for qens.viz.lattice_view."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import numpy as np

from qens.codes.repetition import RepetitionCode
from qens.viz.lattice_view import draw_lattice
from qens.viz.base import FigureHandle


class TestDrawLattice:
    def test_returns_figure_handle(self):
        code = RepetitionCode(3)
        handle = draw_lattice(code)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_syndrome(self):
        code = RepetitionCode(3)
        syndrome = np.array([1, 0], dtype=np.uint8)
        handle = draw_lattice(code, syndrome=syndrome)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_error(self):
        code = RepetitionCode(3)
        error = np.array([1, 0, 0], dtype=np.uint8)
        handle = draw_lattice(code, error=error)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_title(self):
        code = RepetitionCode(3)
        handle = draw_lattice(code, title="Test Lattice")
        assert isinstance(handle, FigureHandle)
        handle.close()
