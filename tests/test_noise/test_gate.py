"""Tests for qens.noise.gate error models."""
from __future__ import annotations

import numpy as np
import pytest

from qens.core.circuit import Gate
from qens.noise.gate import CoherentRotationError, CrosstalkError


class TestCoherentRotationError:
    def test_sample_errors_shape(self, rng):
        model = CoherentRotationError(angle_stddev=0.01)
        err = model.sample_errors(4, [0, 1, 2, 3], rng)
        assert err.shape == (4,)
        assert err.dtype == np.uint8

    def test_applies_to_non_measurement(self):
        model = CoherentRotationError()
        assert model.applies_to(Gate("H", (0,))) is True
        assert model.applies_to(Gate("CX", (0, 1))) is True
        assert model.applies_to(Gate("M", (0,))) is False

    def test_negative_stddev_raises(self):
        with pytest.raises(ValueError):
            CoherentRotationError(angle_stddev=-0.1)

    def test_zero_stddev_no_errors(self):
        rng = np.random.default_rng(42)
        model = CoherentRotationError(angle_stddev=0.0)
        # With zero stddev, angle is always 0, so sin^2(0) = 0 => no errors
        for _ in range(100):
            err = model.sample_errors(3, [0, 1, 2], rng)
            assert np.all(err == 0)

    def test_repr(self):
        assert "CoherentRotationError" in repr(CoherentRotationError(0.05))


class TestCrosstalkError:
    def test_sample_errors_shape(self, rng):
        model = CrosstalkError(coupling_map={(0, 1): 0.1})
        err = model.sample_errors(3, [0, 1, 2], rng)
        assert err.shape == (3,)

    def test_applies_to_gates(self):
        model = CrosstalkError()
        assert model.applies_to(Gate("CX", (0, 1))) is True
        assert model.applies_to(Gate("M", (0,))) is False
        assert model.applies_to(Gate("R", (0,))) is False

    def test_empty_coupling_map(self, rng):
        model = CrosstalkError()
        err = model.sample_errors(3, [0, 1, 2], rng)
        assert np.all(err == 0)

    def test_repr(self):
        assert "CrosstalkError" in repr(CrosstalkError({(0, 1): 0.1}))
