from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from qens.simulation.result import ThresholdResult
from qens.viz.base import FigureHandle
from qens.viz.style import QENSStyle, get_style


def plot_threshold(
    result: ThresholdResult,
    style: QENSStyle | None = None,
    figsize: tuple[float, float] = (9, 7),
    log_scale: bool = True,
    title: str | None = None,
    **kwargs: Any,
) -> FigureHandle:
    """Plot logical error rate vs physical error rate for multiple distances.

    This is the standard threshold plot used in QEC research. Lines for
    different distances should cross at the threshold error rate.

    Args:
        result: ThresholdResult from a sweep experiment.
        style: Visual style overrides.
        figsize: Figure size.
        log_scale: Whether to use log scale for both axes.
        title: Optional title override.

    Returns:
        FigureHandle wrapping the threshold plot.
    """
    s = style or get_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.patch.set_facecolor(s.background_color)

    p_rates = result.physical_error_rates

    for i, d in enumerate(result.distances):
        color = s.distance_colors[i % len(s.distance_colors)]
        logical_rates = result.logical_error_rates[i]

        # Filter out zero rates for log scale
        mask = logical_rates > 0
        if log_scale and np.any(mask):
            ax.plot(
                np.array(p_rates)[mask], logical_rates[mask],
                "o-", color=color, label=f"d = {d}",
                markersize=8, linewidth=2.5,
            )
        else:
            ax.plot(
                p_rates, logical_rates,
                "o-", color=color, label=f"d = {d}",
                markersize=8, linewidth=2.5,
            )

    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")

    ax.set_xlabel("Physical error rate (p)", fontsize=s.font_size + 2,
                  color=s.text_color, labelpad=8)
    ax.set_ylabel("Logical error rate", fontsize=s.font_size + 2,
                  color=s.text_color, labelpad=8)
    ax.set_title(
        title or "Threshold Plot",
        fontsize=s.font_size + 4, color=s.text_color, pad=14,
        fontweight="bold",
    )
    ax.legend(fontsize=s.font_size + 1, framealpha=0.95,
              edgecolor=s.grid_color, fancybox=True)
    ax.grid(True, alpha=0.3, color=s.graph_edge_color, linewidth=0.8)
    ax.tick_params(colors=s.text_color, labelsize=s.font_size + 1)

    fig.tight_layout()
    return FigureHandle(fig=fig, axes=ax)


def plot_logical_rates(
    distances: list[int],
    logical_rates: list[float],
    style: QENSStyle | None = None,
    figsize: tuple[float, float] = (7, 5),
    title: str | None = None,
    **kwargs: Any,
) -> FigureHandle:
    """Bar chart of logical error rates across distances.

    Args:
        distances: Code distances.
        logical_rates: Corresponding logical error rates.
        style: Visual style overrides.
        figsize: Figure size.
        title: Optional title.

    Returns:
        FigureHandle.
    """
    s = style or get_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.patch.set_facecolor(s.background_color)

    colors = [s.distance_colors[i % len(s.distance_colors)] for i in range(len(distances))]
    ax.bar([str(d) for d in distances], logical_rates, color=colors, alpha=0.85)

    ax.set_xlabel("Code distance", fontsize=s.font_size + 2,
                  color=s.text_color, labelpad=8)
    ax.set_ylabel("Logical error rate", fontsize=s.font_size + 2,
                  color=s.text_color, labelpad=8)
    ax.set_title(
        title or "Logical Error Rate by Distance",
        fontsize=s.font_size + 4, color=s.text_color, pad=14,
        fontweight="bold",
    )
    ax.tick_params(colors=s.text_color, labelsize=s.font_size + 1)
    ax.grid(axis="y", alpha=0.3, color=s.graph_edge_color, linewidth=0.8)

    fig.tight_layout()
    return FigureHandle(fig=fig, axes=ax)


def plot_histogram(
    data: list[float] | np.ndarray,
    bins: int = 30,
    style: QENSStyle | None = None,
    figsize: tuple[float, float] = (7, 5),
    xlabel: str = "Value",
    title: str | None = None,
    **kwargs: Any,
) -> FigureHandle:
    """General-purpose histogram for simulation statistics.

    Args:
        data: Values to histogram.
        bins: Number of bins.
        style: Visual style overrides.
        figsize: Figure size.
        xlabel: X-axis label.
        title: Optional title.

    Returns:
        FigureHandle.
    """
    s = style or get_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.patch.set_facecolor(s.background_color)

    ax.hist(data, bins=bins, color=s.distance_colors[0], alpha=0.8,
            edgecolor=s.text_color, linewidth=0.8)

    ax.set_xlabel(xlabel, fontsize=s.font_size + 2,
                  color=s.text_color, labelpad=8)
    ax.set_ylabel("Count", fontsize=s.font_size + 2,
                  color=s.text_color, labelpad=8)
    ax.set_title(
        title or "Histogram",
        fontsize=s.font_size + 4, color=s.text_color, pad=14,
        fontweight="bold",
    )
    ax.tick_params(colors=s.text_color, labelsize=s.font_size + 1)
    ax.grid(axis="y", alpha=0.3, color=s.graph_edge_color, linewidth=0.8)

    fig.tight_layout()
    return FigureHandle(fig=fig, axes=ax)
