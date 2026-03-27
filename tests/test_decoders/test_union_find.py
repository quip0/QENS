"""Tests for qens.decoders.union_find."""
from __future__ import annotations

import numpy as np

from qens.core.types import PauliOp
from qens.codes.repetition import RepetitionCode
from qens.decoders.union_find import UnionFindDecoder


class TestUnionFindDecoder:
    def test_decode_trivial_syndrome(self, rep3):
        decoder = UnionFindDecoder(rep3)
        decoder.precompute()
        syndrome = np.zeros(2, dtype=np.uint8)
        result = decoder.decode(syndrome)
        assert result.success is True
        assert np.all(result.correction == 0)

    def test_decode_single_error(self, rep3):
        decoder = UnionFindDecoder(rep3)
        decoder.precompute()
        error = np.zeros(3, dtype=np.uint8)
        error[0] = PauliOp.X
        syndrome = rep3.compute_syndrome(error)
        result = decoder.decode(syndrome)
        assert result.correction is not None
        assert "num_defects" in result.metadata

    def test_build_decoding_graph(self, rep3):
        decoder = UnionFindDecoder(rep3)
        decoder.precompute()
        graph = decoder.build_decoding_graph()
        assert "nodes" in graph
        assert "edges" in graph
        assert "boundary_nodes" in graph

    def test_precompute_flag(self, rep3):
        decoder = UnionFindDecoder(rep3)
        assert not decoder._precomputed
        decoder.precompute()
        assert decoder._precomputed

    def test_auto_precompute_on_decode(self, rep3):
        decoder = UnionFindDecoder(rep3)
        syndrome = np.zeros(2, dtype=np.uint8)
        decoder.decode(syndrome)
        assert decoder._precomputed
