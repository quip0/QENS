"""Smoke tests for qens.viz.stats plotting functions."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import numpy as np

from qens.simulation.result import ThresholdResult
from qens.viz.stats import plot_threshold, plot_histogram, plot_logical_rates
from qens.viz.base import FigureHandle


class TestPlotThreshold:
    def test_returns_figure_handle(self):
        result = ThresholdResult(
            distances=[3, 5],
            physical_error_rates=[0.01, 0.05, 0.1],
            logical_error_rates=np.array([
                [0.001, 0.01, 0.05],
                [0.0005, 0.005, 0.03],
            ]),
            shots_per_point=1000,
        )
        handle = plot_threshold(result)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_linear_scale(self):
        result = ThresholdResult(
            distances=[3],
            physical_error_rates=[0.01, 0.05],
            logical_error_rates=np.array([[0.001, 0.01]]),
            shots_per_point=100,
        )
        handle = plot_threshold(result, log_scale=False)
        assert isinstance(handle, FigureHandle)
        handle.close()


class TestPlotHistogram:
    def test_returns_figure_handle(self):
        data = np.random.default_rng(42).normal(0, 1, size=200)
        handle = plot_histogram(data, bins=20)
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_title(self):
        handle = plot_histogram([1, 2, 3, 4, 5], title="Test Hist")
        assert isinstance(handle, FigureHandle)
        handle.close()


class TestPlotLogicalRates:
    def test_returns_figure_handle(self):
        handle = plot_logical_rates(
            distances=[3, 5, 7],
            logical_rates=[0.05, 0.02, 0.01],
        )
        assert isinstance(handle, FigureHandle)
        handle.close()

    def test_with_title(self):
        handle = plot_logical_rates(
            distances=[3],
            logical_rates=[0.1],
            title="Test Rates",
        )
        assert isinstance(handle, FigureHandle)
        handle.close()
