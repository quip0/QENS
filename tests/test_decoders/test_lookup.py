"""Tests for qens.decoders.lookup."""
from __future__ import annotations

import numpy as np

from qens.core.types import PauliOp
from qens.codes.repetition import RepetitionCode
from qens.decoders.lookup import LookupTableDecoder


class TestLookupTableDecoder:
    def test_decode_trivial_syndrome(self, rep3):
        decoder = LookupTableDecoder(rep3)
        decoder.precompute()
        syndrome = np.zeros(2, dtype=np.uint8)
        result = decoder.decode(syndrome)
        assert result.success is True
        assert np.all(result.correction == 0)

    def test_decode_single_error(self, rep3):
        decoder = LookupTableDecoder(rep3)
        decoder.precompute()
        # X error on qubit 0 -> syndrome [1, 0]
        error = np.zeros(3, dtype=np.uint8)
        error[0] = PauliOp.X
        syndrome = rep3.compute_syndrome(error)
        result = decoder.decode(syndrome)
        assert result.correction is not None
        assert result.metadata.get("table_hit") is True

    def test_decode_middle_error(self, rep3):
        decoder = LookupTableDecoder(rep3)
        decoder.precompute()
        # X error on qubit 1 -> syndrome [1, 1]
        error = np.zeros(3, dtype=np.uint8)
        error[1] = PauliOp.X
        syndrome = rep3.compute_syndrome(error)
        result = decoder.decode(syndrome)
        assert result.correction is not None

    def test_precompute_flag(self, rep3):
        decoder = LookupTableDecoder(rep3)
        assert not decoder._precomputed
        decoder.precompute()
        assert decoder._precomputed

    def test_auto_precompute_on_decode(self, rep3):
        decoder = LookupTableDecoder(rep3)
        syndrome = np.zeros(2, dtype=np.uint8)
        result = decoder.decode(syndrome)
        assert decoder._precomputed
        assert result.success is True

    def test_code_property(self, rep3):
        decoder = LookupTableDecoder(rep3)
        assert decoder.code is rep3
