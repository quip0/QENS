"""Tests for qens.simulation.experiment."""
from __future__ import annotations

import numpy as np
import pytest

from qens.codes.repetition import RepetitionCode
from qens.noise.pauli import DepolarizingError
from qens.decoders.lookup import LookupTableDecoder
from qens.simulation.experiment import ThresholdExperiment


class TestThresholdExperiment:
    def test_result_shape(self):
        experiment = ThresholdExperiment(
            code_class=RepetitionCode,
            distances=[3, 5],
            physical_error_rates=[0.01, 0.05],
            noise_model_factory=lambda p: DepolarizingError(p=p),
            decoder_class=LookupTableDecoder,
            shots_per_point=100,
            seed=42,
        )
        result = experiment.run()
        assert result.logical_error_rates.shape == (2, 2)
        assert result.distances == [3, 5]
        assert result.physical_error_rates == [0.01, 0.05]
        assert result.shots_per_point == 100

    def test_logical_rates_are_valid(self):
        experiment = ThresholdExperiment(
            code_class=RepetitionCode,
            distances=[3],
            physical_error_rates=[0.01],
            noise_model_factory=lambda p: DepolarizingError(p=p),
            decoder_class=LookupTableDecoder,
            shots_per_point=100,
            seed=42,
        )
        result = experiment.run()
        rate = result.logical_error_rates[0, 0]
        assert 0.0 <= rate <= 1.0

    def test_single_point(self):
        code = RepetitionCode(3)
        noise = DepolarizingError(p=0.01)
        decoder = LookupTableDecoder(code)
        result = ThresholdExperiment.single_point(
            code, noise, decoder, shots=100, seed=42,
        )
        assert result.num_shots == 100
        assert 0.0 <= result.logical_error_rate <= 1.0

    def test_progress_callback(self):
        calls = []
        experiment = ThresholdExperiment(
            code_class=RepetitionCode,
            distances=[3],
            physical_error_rates=[0.01, 0.02],
            noise_model_factory=lambda p: DepolarizingError(p=p),
            decoder_class=LookupTableDecoder,
            shots_per_point=50,
            seed=42,
        )
        experiment.run(progress_callback=lambda c, t: calls.append((c, t)))
        assert len(calls) == 2
        assert calls[-1] == (2, 2)
