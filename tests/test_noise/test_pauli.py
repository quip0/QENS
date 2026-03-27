"""Tests for qens.noise.pauli error models."""
from __future__ import annotations

import numpy as np
import pytest

from qens.core.types import PauliOp
from qens.noise.pauli import (
    BitFlipError,
    PhaseFlipError,
    DepolarizingError,
    PauliYError,
)


class TestBitFlipError:
    def test_correct_shape(self, rng):
        model = BitFlipError(p=0.1)
        err = model.sample_errors(5, [0, 1, 2, 3, 4], rng)
        assert err.shape == (5,)
        assert err.dtype == np.uint8

    def test_statistical_frequency(self):
        rng = np.random.default_rng(42)
        p = 0.1
        model = BitFlipError(p=p)
        n = 10000
        count = 0
        for _ in range(n):
            err = model.sample_errors(1, [0], rng)
            if err[0] == PauliOp.X:
                count += 1
        freq = count / n
        sigma = np.sqrt(p * (1 - p) / n)
        assert freq == pytest.approx(p, abs=3 * sigma)

    def test_only_x_errors(self, rng):
        model = BitFlipError(p=0.5)
        for _ in range(200):
            err = model.sample_errors(3, [0, 1, 2], rng)
            for v in err:
                assert v in (PauliOp.I, PauliOp.X)

    def test_kraus_validates(self):
        model = BitFlipError(p=0.1)
        ch = model.to_channel([0])
        assert ch.validate()

    def test_invalid_probability_raises(self):
        with pytest.raises(ValueError):
            BitFlipError(p=-0.1)
        with pytest.raises(ValueError):
            BitFlipError(p=1.5)

    def test_repr(self):
        assert "BitFlipError" in repr(BitFlipError(p=0.1))


class TestPhaseFlipError:
    def test_correct_shape(self, rng):
        model = PhaseFlipError(p=0.1)
        err = model.sample_errors(4, [0, 1, 2, 3], rng)
        assert err.shape == (4,)

    def test_statistical_frequency(self):
        rng = np.random.default_rng(42)
        p = 0.15
        model = PhaseFlipError(p=p)
        n = 10000
        count = 0
        for _ in range(n):
            err = model.sample_errors(1, [0], rng)
            if err[0] == PauliOp.Z:
                count += 1
        freq = count / n
        sigma = np.sqrt(p * (1 - p) / n)
        assert freq == pytest.approx(p, abs=3 * sigma)

    def test_only_z_errors(self, rng):
        model = PhaseFlipError(p=0.5)
        for _ in range(200):
            err = model.sample_errors(2, [0, 1], rng)
            for v in err:
                assert v in (PauliOp.I, PauliOp.Z)

    def test_kraus_validates(self):
        model = PhaseFlipError(p=0.2)
        ch = model.to_channel([0])
        assert ch.validate()

    def test_invalid_probability_raises(self):
        with pytest.raises(ValueError):
            PhaseFlipError(p=-0.01)
        with pytest.raises(ValueError):
            PhaseFlipError(p=2.0)


class TestDepolarizingError:
    def test_correct_shape(self, rng):
        model = DepolarizingError(p=0.1)
        err = model.sample_errors(6, list(range(6)), rng)
        assert err.shape == (6,)

    def test_statistical_frequency(self):
        rng = np.random.default_rng(42)
        p = 0.3
        model = DepolarizingError(p=p)
        n = 10000
        counts = {PauliOp.I: 0, PauliOp.X: 0, PauliOp.Y: 0, PauliOp.Z: 0}
        for _ in range(n):
            err = model.sample_errors(1, [0], rng)
            counts[PauliOp(err[0])] += 1
        p_each = p / 3.0
        p_identity = 1 - p
        sigma_id = np.sqrt(p_identity * (1 - p_identity) / n)
        sigma_each = np.sqrt(p_each * (1 - p_each) / n)
        assert counts[PauliOp.I] / n == pytest.approx(p_identity, abs=3 * sigma_id)
        assert counts[PauliOp.X] / n == pytest.approx(p_each, abs=3 * sigma_each)
        assert counts[PauliOp.Y] / n == pytest.approx(p_each, abs=3 * sigma_each)
        assert counts[PauliOp.Z] / n == pytest.approx(p_each, abs=3 * sigma_each)

    def test_kraus_validates(self):
        model = DepolarizingError(p=0.05)
        ch = model.to_channel([0])
        assert ch.validate()
        assert ch.num_kraus == 4

    def test_invalid_probability_raises(self):
        with pytest.raises(ValueError):
            DepolarizingError(p=-0.01)
        with pytest.raises(ValueError):
            DepolarizingError(p=1.1)

    def test_zero_probability_no_errors(self):
        rng = np.random.default_rng(42)
        model = DepolarizingError(p=0.0)
        for _ in range(100):
            err = model.sample_errors(5, list(range(5)), rng)
            assert np.all(err == PauliOp.I)


class TestPauliYError:
    def test_correct_shape(self, rng):
        model = PauliYError(p=0.1)
        err = model.sample_errors(3, [0, 1, 2], rng)
        assert err.shape == (3,)

    def test_statistical_frequency(self):
        rng = np.random.default_rng(42)
        p = 0.2
        model = PauliYError(p=p)
        n = 10000
        count = 0
        for _ in range(n):
            err = model.sample_errors(1, [0], rng)
            if err[0] == PauliOp.Y:
                count += 1
        freq = count / n
        sigma = np.sqrt(p * (1 - p) / n)
        assert freq == pytest.approx(p, abs=3 * sigma)

    def test_only_y_errors(self, rng):
        model = PauliYError(p=0.5)
        for _ in range(200):
            err = model.sample_errors(2, [0, 1], rng)
            for v in err:
                assert v in (PauliOp.I, PauliOp.Y)

    def test_kraus_validates(self):
        model = PauliYError(p=0.1)
        ch = model.to_channel([0])
        assert ch.validate()

    def test_invalid_probability_raises(self):
        with pytest.raises(ValueError):
            PauliYError(p=-0.5)
