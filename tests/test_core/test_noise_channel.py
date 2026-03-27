"""Tests for qens.core.noise_channel."""
from __future__ import annotations

import numpy as np
import pytest

from qens.core.noise_channel import NoiseChannel


class TestNoiseChannel:
    def test_identity_channel_validates(self):
        e0 = np.eye(2, dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[e0])
        assert ch.validate()

    def test_bit_flip_channel_validates(self):
        p = 0.1
        e0 = np.sqrt(1 - p) * np.eye(2, dtype=np.complex128)
        e1 = np.sqrt(p) * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[e0, e1])
        assert ch.validate()

    def test_invalid_channel_fails_validation(self):
        bad = np.array([[2, 0], [0, 2]], dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[bad])
        assert not ch.validate()

    def test_empty_channel_fails_validation(self):
        ch = NoiseChannel(kraus_ops=[])
        assert not ch.validate()

    def test_num_kraus(self):
        e0 = np.eye(2, dtype=np.complex128)
        e1 = np.zeros((2, 2), dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[e0, e1])
        assert ch.num_kraus == 2

    def test_probabilities_identity(self):
        e0 = np.eye(2, dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[e0])
        probs = ch.probabilities()
        assert probs[0] == pytest.approx(1.0)

    def test_probabilities_sum_to_one(self):
        p = 0.3
        e0 = np.sqrt(1 - p) * np.eye(2, dtype=np.complex128)
        e1 = np.sqrt(p) * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[e0, e1])
        probs = ch.probabilities()
        assert probs.sum() == pytest.approx(1.0)
        assert probs[0] == pytest.approx(1 - p)
        assert probs[1] == pytest.approx(p)

    def test_sample_returns_valid_index(self):
        p = 0.5
        e0 = np.sqrt(1 - p) * np.eye(2, dtype=np.complex128)
        e1 = np.sqrt(p) * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[e0, e1])
        rng = np.random.default_rng(42)
        for _ in range(100):
            idx = ch.sample(rng)
            assert idx in (0, 1)

    def test_sample_statistical(self):
        p = 0.3
        e0 = np.sqrt(1 - p) * np.eye(2, dtype=np.complex128)
        e1 = np.sqrt(p) * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        ch = NoiseChannel(kraus_ops=[e0, e1])
        rng = np.random.default_rng(42)
        n = 10000
        counts = [0, 0]
        for _ in range(n):
            counts[ch.sample(rng)] += 1
        freq = counts[1] / n
        sigma = np.sqrt(p * (1 - p) / n)
        assert freq == pytest.approx(p, abs=3 * sigma)
