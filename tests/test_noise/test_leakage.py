"""Tests for qens.noise.leakage."""
from __future__ import annotations

import numpy as np

from qens.noise.leakage import LeakageError


class TestLeakageError:
    def test_sample_errors_shape(self, rng):
        model = LeakageError(p_leak=0.1, p_relax=0.5)
        err = model.sample_errors(4, [0, 1, 2, 3], rng)
        assert err.shape == (4,)
        assert err.dtype == np.uint8

    def test_leakage_tracking(self):
        rng = np.random.default_rng(42)
        model = LeakageError(p_leak=1.0, p_relax=0.0)
        model.sample_errors(3, [0, 1], rng)
        assert 0 in model.leaked_qubits
        assert 1 in model.leaked_qubits
        assert 2 not in model.leaked_qubits

    def test_relaxation_tracking(self):
        rng = np.random.default_rng(42)
        model = LeakageError(p_leak=1.0, p_relax=1.0)
        # First call: leak qubits 0,1
        model.sample_errors(2, [0, 1], rng)
        # Second call: since p_relax=1.0, they should relax
        model.sample_errors(2, [0, 1], rng)
        assert len(model.leaked_qubits) == 0

    def test_reset_clears_leaked(self):
        rng = np.random.default_rng(42)
        model = LeakageError(p_leak=1.0, p_relax=0.0)
        model.sample_errors(2, [0, 1], rng)
        assert len(model.leaked_qubits) > 0
        model.reset()
        assert len(model.leaked_qubits) == 0

    def test_no_leakage_at_zero_prob(self):
        rng = np.random.default_rng(42)
        model = LeakageError(p_leak=0.0, p_relax=0.0)
        for _ in range(50):
            model.sample_errors(3, [0, 1, 2], rng)
        assert len(model.leaked_qubits) == 0

    def test_repr(self):
        assert "LeakageError" in repr(LeakageError(p_leak=0.01, p_relax=0.1))
