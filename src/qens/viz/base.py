from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.figure
import matplotlib.pyplot as plt


@dataclass
class FigureHandle:
    """Wrapper around a matplotlib figure for consistent save/show API."""

    fig: matplotlib.figure.Figure
    axes: Any  # matplotlib Axes or array of Axes

    def save(self, path: str, dpi: int = 200, **kwargs: Any) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=dpi, bbox_inches="tight", **kwargs)

    def show(self) -> None:
        plt.show()

    def close(self) -> None:
        plt.close(self.fig)

    def _repr_png_(self) -> bytes:
        buf = BytesIO()
        self.fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        return buf.getvalue()


class Visualizer(ABC):
    """Base class for all visualizers.

    # --- EXTENSION POINT ---
    # To add a new visualizer:
    # 1. Subclass Visualizer
    # 2. Implement draw() to produce a FigureHandle
    # 3. Register with: viz_registry.register("my_viz", MyVisualizer)
    """

    @abstractmethod
    def draw(self, **kwargs: Any) -> FigureHandle:
        """Produce a matplotlib figure."""
        ...
