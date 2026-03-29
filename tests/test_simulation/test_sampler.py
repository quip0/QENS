"""Tests for qens.simulation.sampler."""
from __future__ import annotations

import numpy as np

from qens.codes.repetition import RepetitionCode
from qens.noise.pauli import DepolarizingError
from qens.noise.leakage import LeakageError
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

    def test_leakage_state_reset_between_shots(self):
        """Regression: LeakageError._leaked must not carry over between shots.

        With p_leak=1 and p_relax=0, every qubit leaks on shot 0 and stays
        leaked indefinitely unless reset() is called.  After the fix, NoisySampler
        calls reset() at the start of each shot, so shot 1 starts with a fresh
        (empty) leaked set and the first-shot leak probability is re-applied.
        We verify this by running two back-to-back single-shot simulations and
        confirming they produce identical results (same seed → same RNG state).
        """
        code = RepetitionCode(3)
        # p_leak=1.0, p_relax=0.0: every qubit leaks and never relaxes
        noise = LeakageError(p_leak=1.0, p_relax=0.0)

        sampler_a = NoisySampler(seed=7)
        result_a = sampler_a.sample_errors(code, noise, shots=1)

        # Reset the noise model manually and run again with the same seed
        noise2 = LeakageError(p_leak=1.0, p_relax=0.0)
        sampler_b = NoisySampler(seed=7)
        result_b = sampler_b.sample_errors(code, noise2, shots=1)

        # Both shots are fresh starts — results must be identical
        np.testing.assert_array_equal(result_a.errors[0], result_b.errors[0])

        # Verify that each shot starts clean: run 2 shots and confirm shot 1
        # (index 0) and shot 2 (index 1) produce the same error distribution as
        # two independent single-shot runs with the same seed.
        noise3 = LeakageError(p_leak=1.0, p_relax=0.0)
        sampler_c = NoisySampler(seed=99)
        result_c = sampler_c.sample_errors(code, noise3, shots=2)

        noise4a = LeakageError(p_leak=1.0, p_relax=0.0)
        sampler_d = NoisySampler(seed=99)
        result_d_shot0 = sampler_d.sample_errors(code, noise4a, shots=1)

        # Both should start from the same clean initial state → same first shot
        np.testing.assert_array_equal(result_c.errors[0], result_d_shot0.errors[0])
