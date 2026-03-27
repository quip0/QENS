"""Tests for qens.simulation.sampler."""
from __future__ import annotations

import numpy as np

from qens.codes.repetition import RepetitionCode
from qens.noise.pauli import DepolarizingError
from qens.decoders.lookup import LookupTableDecoder
from qens.simulation.sampler import NoisySampler


class TestNoisySampler:
    def test_sample_errors_deterministic(self):
        code = RepetitionCode(3)
        noise = DepolarizingError(p=0.1)
        s1 = NoisySampler(seed=42)
        s2 = NoisySampler(seed=42)
        r1 = s1.sample_errors(code, noise, shots=10)
        r2 = s2.sample_errors(code, noise, shots=10)
        for i in range(10):
            np.testing.assert_array_equal(r1.errors[i], r2.errors[i])
            np.testing.assert_array_equal(r1.syndromes[i], r2.syndromes[i])

    def test_sample_errors_shape(self):
        code = RepetitionCode(3)
        noise = DepolarizingError(p=0.01)
        sampler = NoisySampler(seed=42)
        result = sampler.sample_errors(code, noise, shots=50)
        assert result.num_shots == 50
        assert len(result.errors) == 50
        assert len(result.syndromes) == 50
        assert result.errors[0].shape == (3,)
        assert result.syndromes[0].shape == (2,)

    def test_run_with_decoder(self):
        code = RepetitionCode(3)
        noise = DepolarizingError(p=0.01)
        decoder = LookupTableDecoder(code)
        sampler = NoisySampler(seed=42)
        result = sampler.run(code, noise, decoder, shots=100)
        assert result.num_shots == 100
        assert len(result.logical_errors) == 100
        assert len(result.corrections) == 100
        assert 0.0 <= result.logical_error_rate <= 1.0

    def test_run_deterministic(self):
        code = RepetitionCode(3)
        noise = DepolarizingError(p=0.05)
        decoder = LookupTableDecoder(code)
        s1 = NoisySampler(seed=123)
        s2 = NoisySampler(seed=123)
        r1 = s1.run(code, noise, decoder, shots=50)
        r2 = s2.run(code, noise, decoder, shots=50)
        assert r1.logical_errors == r2.logical_errors
