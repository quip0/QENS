"""Integration test: mini threshold sweep with surface code."""
from __future__ import annotations

import numpy as np

from qens.codes.surface import SurfaceCode
from qens.noise.pauli import DepolarizingError
from qens.decoders.mwpm import MWPMDecoder
from qens.simulation.experiment import ThresholdExperiment


class TestSurfaceThresholdSweep:
    def test_result_shape(self):
        experiment = ThresholdExperiment(
            code_class=SurfaceCode,
            distances=[3],
            physical_error_rates=[0.01, 0.05],
            noise_model_factory=lambda p: DepolarizingError(p=p),
            decoder_class=MWPMDecoder,
            shots_per_point=50,
            seed=42,
        )
        result = experiment.run()
        assert result.logical_error_rates.shape == (1, 2)
        assert result.distances == [3]
        assert result.physical_error_rates == [0.01, 0.05]
        assert result.shots_per_point == 50
        # All rates should be valid probabilities
        assert np.all(result.logical_error_rates >= 0.0)
        assert np.all(result.logical_error_rates <= 1.0)
