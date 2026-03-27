"""Tests for qens.noise.measurement."""
from __future__ import annotations

import numpy as np

from qens.core.circuit import Gate
from qens.noise.measurement import MeasurementError


class TestMeasurementError:
    def test_applies_to_measurement_gate(self):
        model = MeasurementError(p_0to1=0.01)
        assert model.applies_to(Gate("M", (0,))) is True

    def test_does_not_apply_to_other_gates(self):
        model = MeasurementError(p_0to1=0.01)
        assert model.applies_to(Gate("H", (0,))) is False
        assert model.applies_to(Gate("CX", (0, 1))) is False
        assert model.applies_to(Gate("X", (0,))) is False
        assert model.applies_to(Gate("R", (0,))) is False

    def test_symmetric_noise(self):
        model = MeasurementError(p_0to1=0.05)
        assert model.p_0to1 == 0.05
        assert model.p_1to0 == 0.05

    def test_asymmetric_noise(self):
        model = MeasurementError(p_0to1=0.01, p_1to0=0.05)
        assert model.p_0to1 == 0.01
        assert model.p_1to0 == 0.05

    def test_sample_errors_shape(self):
        rng = np.random.default_rng(42)
        model = MeasurementError(p_0to1=0.1)
        err = model.sample_errors(3, [0, 1, 2], rng)
        assert err.shape == (3,)
        assert err.dtype == np.uint8

    def test_repr(self):
        r = repr(MeasurementError(p_0to1=0.01, p_1to0=0.02))
        assert "MeasurementError" in r
