from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QENSStyle:
    """Color palette and style defaults for QENS visualizations."""

    # Qubit colors
    data_qubit_color: str = "#4A90D9"
    ancilla_x_color: str = "#E74C3C"
    ancilla_z_color: str = "#2ECC71"
    ancilla_color: str = "#F39C12"

    # Error colors
    error_x_color: str = "#E74C3C"
    error_y_color: str = "#9B59B6"
    error_z_color: str = "#3498DB"
    no_error_color: str = "#ECF0F1"

    # Syndrome colors
    syndrome_active: str = "#E74C3C"
    syndrome_inactive: str = "#BDC3C7"

    # Decoding graph colors
    matching_edge_color: str = "#E67E22"
    graph_edge_color: str = "#95A5A6"
    boundary_node_color: str = "#1ABC9C"
    defect_color: str = "#E74C3C"

    # Circuit colors
    gate_color: str = "#2C3E50"
    wire_color: str = "#7F8C8D"
    measurement_color: str = "#8E44AD"

    # Color code plaquette colors (3-coloring, qiskit convention)
    color_code_plaquette_colors: tuple[str, str, str] = (
        "tomato", "yellowgreen", "steelblue"
    )

    # General
    background_color: str = "#FFFFFF"
    text_color: str = "#2C3E50"
    grid_color: str = "#ECF0F1"

    # Sizes
    qubit_size: float = 450.0
    ancilla_size: float = 320.0
    edge_width: float = 2.0
    font_size: float = 11.0

    # Stats plot colors (for threshold curves at different distances)
    distance_colors: tuple[str, ...] = (
        "#E74C3C", "#3498DB", "#2ECC71", "#F39C12",
        "#9B59B6", "#1ABC9C", "#E67E22", "#34495E",
    )


DEFAULT_STYLE = QENSStyle()


def get_style() -> QENSStyle:
    """Return the current default style."""
    return DEFAULT_STYLE
