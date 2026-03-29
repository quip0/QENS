from __future__ import annotations

from typing import Callable

import numpy as np

from qens.codes.base import QECCode
from qens.noise.base import ErrorModel
from qens.decoders.base import Decoder
from qens.simulation.sampler import NoisySampler
from qens.simulation.result import SimulationResult, ThresholdResult


class ThresholdExperiment:
    """Sweep physical error rates across multiple code distances.

    This is the standard workflow for determining the error threshold
    of a QEC code family: for each distance and physical error rate,
    run many shots and measure the logical error rate.

    Usage:
        experiment = ThresholdExperiment(
            code_class=SurfaceCode,
            distances=[3, 5, 7],
            physical_error_rates=[0.001, 0.005, 0.01, 0.02],
            noise_model_factory=lambda p: DepolarizingError(p=p),
            decoder_class=MWPMDecoder,
            shots_per_point=10_000,
        )
        result = experiment.run()
    """

    def __init__(
        self,
        code_class: type[QECCode],
        distances: list[int],
        physical_error_rates: list[float],
        noise_model_factory: Callable[[float], ErrorModel],
        decoder_class: type[Decoder],
        shots_per_point: int = 10_000,
        seed: int | None = None,
    ) -> None:
        """Create a threshold sweep experiment.

        Args:
            code_class: The QECCode subclass to instantiate (e.g. SurfaceCode).
                        Called as ``code_class(d)`` for each distance ``d``.
            distances: List of code distances to sweep over (e.g. [3, 5, 7]).
            physical_error_rates: List of physical error rates to test
                                   (e.g. [0.001, 0.005, 0.01]).
            noise_model_factory: Callable that accepts a physical error rate and
                                  returns an :class:`ErrorModel` instance.
            decoder_class: The :class:`Decoder` subclass to use.  Instantiated as
                           ``decoder_class(code)`` for each distance.
            shots_per_point: Number of Monte Carlo shots per (distance, rate) pair.
                             Defaults to 10 000.
            seed: Optional RNG seed for reproducibility.
        """
        self.code_class = code_class
        self.distances = distances
        self.physical_error_rates = physical_error_rates
        self.noise_model_factory = noise_model_factory
        self.decoder_class = decoder_class
        self.shots_per_point = shots_per_point
        self.seed = seed

    def run(self, progress_callback: Callable[[int, int], None] | None = None) -> ThresholdResult:
        """Run the full threshold sweep.

        Args:
            progress_callback: Optional callback(completed, total) for progress tracking.

        Returns:
            ThresholdResult with logical error rates for each (distance, p) pair.
        """
        n_d = len(self.distances)
        n_p = len(self.physical_error_rates)
        total = n_d * n_p
        completed = 0

        logical_rates = np.zeros((n_d, n_p), dtype=np.float64)
        sampler = NoisySampler(seed=self.seed)

        for i, d in enumerate(self.distances):
            code = self.code_class(d)
            decoder = self.decoder_class(code)
            decoder.precompute()

            for j, p in enumerate(self.physical_error_rates):
                noise = self.noise_model_factory(p)
                result = sampler.run(code, noise, decoder, self.shots_per_point)
                logical_rates[i, j] = result.logical_error_rate

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        return ThresholdResult(
            distances=self.distances,
            physical_error_rates=self.physical_error_rates,
            logical_error_rates=logical_rates,
            shots_per_point=self.shots_per_point,
        )

    @staticmethod
    def single_point(
        code: QECCode,
        noise_model: ErrorModel,
        decoder: Decoder,
        shots: int,
        seed: int | None = None,
    ) -> SimulationResult:
        """Run a single simulation point (one code, one noise level)."""
        decoder.precompute()
        sampler = NoisySampler(seed=seed)
        return sampler.run(code, noise_model, decoder, shots)
