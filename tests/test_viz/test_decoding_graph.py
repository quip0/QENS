"""Smoke tests for qens.viz.decoding_graph."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import numpy as np

from qens.codes.repetition import RepetitionCode
from qens.decoders.mwpm import MWPMDecoder
from qens.viz.decoding_graph import draw_decoding_graph
from qens.viz.base import FigureHandle


class TestDrawDecodingGraph:
    def test_returns_figure_handle(self):
        code = RepetitionCode(3)
        decoder = MWPMDecoder(code)
        decoder.precompute()
        handle = draw_decoding_graph(decoder)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_syndrome(self):
        code = RepetitionCode(3)
        decoder = MWPMDecoder(code)
        decoder.precompute()
        syndrome = np.array([1, 0], dtype=np.uint8)
        handle = draw_decoding_graph(decoder, syndrome=syndrome)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_title(self):
        code = RepetitionCode(3)
        decoder = MWPMDecoder(code)
        decoder.precompute()
        handle = draw_decoding_graph(decoder, title="Test Graph")
        assert isinstance(handle, FigureHandle)
        handle.close()
