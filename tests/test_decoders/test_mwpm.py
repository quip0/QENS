"""Tests for qens.decoders.mwpm."""
from __future__ import annotations

import numpy as np

from qens.core.types import PauliOp
from qens.codes.repetition import RepetitionCode
from qens.decoders.mwpm import MWPMDecoder


class TestMWPMDecoder:
    def test_decode_trivial_syndrome_d3(self, rep3):
        decoder = MWPMDecoder(rep3)
        decoder.precompute()
        syndrome = np.zeros(2, dtype=np.uint8)
        result = decoder.decode(syndrome)
        assert result.success is True
        assert np.all(result.correction == 0)

    def test_decode_single_error_d3(self, rep3):
        decoder = MWPMDecoder(rep3)
        decoder.precompute()
        error = np.zeros(3, dtype=np.uint8)
        error[0] = PauliOp.X
        syndrome = rep3.compute_syndrome(error)
        result = decoder.decode(syndrome)
        assert result.correction is not None
        assert "num_defects" in result.metadata

    def test_decode_trivial_syndrome_d5(self, rep5):
        decoder = MWPMDecoder(rep5)
        decoder.precompute()
        syndrome = np.zeros(4, dtype=np.uint8)
        result = decoder.decode(syndrome)
        assert result.success is True
        assert np.all(result.correction == 0)

    def test_decode_single_error_d5(self, rep5):
        decoder = MWPMDecoder(rep5)
        decoder.precompute()
        error = np.zeros(5, dtype=np.uint8)
        error[2] = PauliOp.X  # middle qubit
        syndrome = rep5.compute_syndrome(error)
        result = decoder.decode(syndrome)
        assert result.correction is not None

    def test_build_decoding_graph(self, rep3):
        decoder = MWPMDecoder(rep3)
        decoder.precompute()
        graph = decoder.build_decoding_graph()
        assert "nodes" in graph
        assert "edges" in graph
        assert "boundary_nodes" in graph
        assert len(graph["nodes"]) > 0

    def test_precompute_flag(self, rep3):
        decoder = MWPMDecoder(rep3)
        assert not decoder._precomputed
        decoder.precompute()
        assert decoder._precomputed
