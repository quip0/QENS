"""Tests for qens.noise.correlated."""
from __future__ import annotations

import numpy as np

from qens.core.types import PauliOp
from qens.noise.correlated import CorrelatedPauliError


class TestCorrelatedPauliError:
    def test_sample_errors_shape(self, rng):
        model = CorrelatedPauliError(
            joint_errors={(0, 1): [(0.1, PauliOp.X, PauliOp.X)]}
        )
        err = model.sample_errors(3, [0, 1, 2], rng)
        assert err.shape == (3,)
        assert err.dtype == np.uint8

    def test_correlated_errors_apply(self):
        # With probability 1.0, should always apply XX
        rng = np.random.default_rng(42)
        model = CorrelatedPauliError(
            joint_errors={(0, 1): [(1.0, PauliOp.X, PauliOp.X)]}
        )
        err = model.sample_errors(3, [0, 1, 2], rng)
        assert err[0] == PauliOp.X
        assert err[1] == PauliOp.X
        assert err[2] == PauliOp.I

    def test_no_errors_when_probability_zero(self, rng):
        model = CorrelatedPauliError(
            joint_errors={(0, 1): [(0.0, PauliOp.X, PauliOp.X)]}
        )
        for _ in range(50):
            err = model.sample_errors(3, [0, 1, 2], rng)
            assert np.all(err == PauliOp.I)

    def test_empty_joint_errors(self, rng):
        model = CorrelatedPauliError(joint_errors={})
        err = model.sample_errors(3, [0, 1, 2], rng)
        assert np.all(err == 0)

    def test_repr(self):
        model = CorrelatedPauliError(
            joint_errors={(0, 1): [(0.1, PauliOp.X, PauliOp.Z)]}
        )
        assert "CorrelatedPauliError" in repr(model)
