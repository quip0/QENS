"""End-to-end integration test: RepetitionCode + noise + decoder pipeline."""
from __future__ import annotations

import pytest

from qens.codes.repetition import RepetitionCode
from qens.noise.pauli import BitFlipError, DepolarizingError
from qens.decoders.lookup import LookupTableDecoder
from qens.simulation.sampler import NoisySampler


class TestRepetitionEndToEnd:
    def test_logical_rate_below_physical(self):
        """With a working decoder, logical error rate should be below physical rate."""
        p_phys = 0.05
        code = RepetitionCode(5)
        noise = BitFlipError(p=p_phys)
        decoder = LookupTableDecoder(code)
        decoder.precompute()
        sampler = NoisySampler(seed=42)
        result = sampler.run(code, noise, decoder, shots=1000)

        assert result.num_shots == 1000
        assert len(result.logical_errors) == 1000
        # The logical error rate should be below the physical rate for bit-flip noise
        assert result.logical_error_rate < p_phys

    def test_pipeline_produces_valid_result(self):
        """Full pipeline with depolarizing noise produces valid output."""
        p_phys = 0.01
        code = RepetitionCode(3)
        noise = DepolarizingError(p=p_phys)
        decoder = LookupTableDecoder(code)
        decoder.precompute()
        sampler = NoisySampler(seed=42)
        result = sampler.run(code, noise, decoder, shots=1000)

        assert result.num_shots == 1000
        assert len(result.logical_errors) == 1000
        assert 0.0 <= result.logical_error_rate <= 1.0
