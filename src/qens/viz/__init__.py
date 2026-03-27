from qens.core.registry import Registry
from qens.viz.base import Visualizer, FigureHandle
from qens.viz.circuit_diagram import draw_circuit
from qens.viz.lattice_view import draw_lattice
from qens.viz.decoding_graph import draw_decoding_graph
from qens.viz.stats import plot_threshold, plot_logical_rates, plot_histogram
from qens.viz.style import QENSStyle, get_style

viz_registry = Registry[Visualizer]()

# --- EXTENSION POINT ---
# To register a custom visualizer:
#   from qens.viz import viz_registry
#   viz_registry.register("my_viz", MyCustomVisualizer)

__all__ = [
    "Visualizer",
    "FigureHandle",
    "draw_circuit",
    "draw_lattice",
    "draw_decoding_graph",
    "plot_threshold",
    "plot_logical_rates",
    "plot_histogram",
    "QENSStyle",
    "get_style",
    "viz_registry",
]
