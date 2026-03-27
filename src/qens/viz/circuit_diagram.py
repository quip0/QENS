from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from qens.core.circuit import Circuit, Gate
from qens.noise.base import ErrorModel
from qens.viz.base import FigureHandle
from qens.viz.style import QENSStyle, get_style


def draw_circuit(
    circuit: Circuit,
    noise_model: ErrorModel | None = None,
    error_locations: list[tuple[int, int]] | None = None,
    highlight_errors: bool = False,
    style: QENSStyle | None = None,
    figsize: tuple[float, float] | None = None,
    **kwargs: Any,
) -> FigureHandle:
    """Draw a quantum circuit diagram with optional error annotations.

    Args:
        circuit: The circuit to draw.
        noise_model: If provided and highlight_errors=True, annotates gates
            where this model applies.
        error_locations: Explicit list of (moment_idx, qubit_idx) error locations.
        highlight_errors: Whether to highlight error-prone gates.
        style: Visual style overrides.
        figsize: Figure size (width, height) in inches.

    Returns:
        FigureHandle wrapping the circuit diagram.
    """
    s = style or get_style()
    nq = circuit.num_qubits
    depth = circuit.depth

    # More generous spacing for readability
    col_spacing = 1.4
    row_spacing = 0.8

    if figsize is None:
        figsize = (max(8, depth * col_spacing + 3), max(4, nq * row_spacing + 1.5))

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_xlim(-1.0, depth * col_spacing + 0.8)
    ax.set_ylim(-0.6, (nq - 1) * row_spacing + 0.6)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(s.background_color)

    # Draw qubit wires
    for q in range(nq):
        y = q * row_spacing
        ax.plot(
            [-0.3, depth * col_spacing + 0.3], [y, y],
            color=s.wire_color, linewidth=1.2, zorder=0,
        )
        ax.text(
            -0.7, y, f"q{q}",
            ha="right", va="center",
            fontsize=s.font_size, color=s.text_color, fontweight="bold",
        )

    # Determine error locations from noise model
    error_set: set[tuple[int, int]] = set()
    if error_locations:
        error_set = set(error_locations)
    elif highlight_errors and noise_model is not None:
        for m_idx, moment in enumerate(circuit.moments):
            for gate in moment.gates:
                if noise_model.applies_to(gate):
                    for q in gate.qubits:
                        error_set.add((m_idx, q))

    # Draw gates
    for m_idx, moment in enumerate(circuit.moments):
        x = m_idx * col_spacing
        for gate in moment.gates:
            _draw_gate(ax, gate, x, error_set, m_idx, s, row_spacing)

    # Legend
    if error_set:
        legend_elements = [
            mpatches.Patch(facecolor=s.error_x_color, alpha=0.3,
                           edgecolor=s.error_x_color, label="Error-prone"),
            mpatches.Patch(facecolor=s.gate_color, alpha=0.8,
                           edgecolor=s.gate_color, label="Clean gate"),
        ]
        ax.legend(handles=legend_elements, loc="upper right",
                  fontsize=s.font_size, framealpha=0.95,
                  edgecolor=s.grid_color, fancybox=True)

    fig.tight_layout()
    return FigureHandle(fig=fig, axes=ax)


def _draw_gate(
    ax: Any,
    gate: Gate,
    x: float,
    error_set: set[tuple[int, int]],
    m_idx: int,
    s: QENSStyle,
    row_spacing: float = 0.8,
) -> None:
    """Draw a single gate on the circuit diagram."""
    has_error = any((m_idx, q) in error_set for q in gate.qubits)
    gate_radius = 0.25

    if gate.name == "M":
        # Measurement symbol
        q = gate.qubits[0]
        y = q * row_spacing
        circle = plt.Circle((x, y), gate_radius, fill=True,
                             facecolor=s.measurement_color, alpha=0.9,
                             edgecolor=s.measurement_color, linewidth=1.5, zorder=2)
        ax.add_patch(circle)
        ax.text(x, y, "M", ha="center", va="center",
                fontsize=s.font_size, color="white", fontweight="bold", zorder=3)
        if has_error:
            highlight = plt.Circle((x, y), gate_radius + 0.1, fill=True,
                                   facecolor=s.error_x_color, alpha=0.2,
                                   edgecolor=s.error_x_color, linewidth=1.0, zorder=1)
            ax.add_patch(highlight)

    elif gate.name == "R":
        q = gate.qubits[0]
        y = q * row_spacing
        ax.text(x, y, "|0\u27E9", ha="center", va="center",
                fontsize=s.font_size, color=s.text_color, zorder=3,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#ECF0F1",
                          edgecolor=s.wire_color, alpha=0.95, linewidth=1.2))

    elif gate.name in ("CX", "CNOT"):
        ctrl, tgt = gate.qubits
        ctrl_y, tgt_y = ctrl * row_spacing, tgt * row_spacing
        # Control dot
        ax.plot(x, ctrl_y, "o", color=s.gate_color, markersize=8, zorder=3)
        # Target circle with plus
        circle = plt.Circle((x, tgt_y), gate_radius, fill=False,
                             edgecolor=s.gate_color, linewidth=2.0, zorder=3)
        ax.add_patch(circle)
        ax.plot([x, x], [tgt_y - gate_radius, tgt_y + gate_radius],
                color=s.gate_color, linewidth=2.0, zorder=3)
        # Connecting line
        ax.plot([x, x], [ctrl_y, tgt_y], color=s.gate_color,
                linewidth=2.0, zorder=2)
        if has_error:
            for q in gate.qubits:
                qy = q * row_spacing
                highlight = plt.Circle((x, qy), gate_radius + 0.1, fill=True,
                                       facecolor=s.error_x_color, alpha=0.2,
                                       edgecolor="none", zorder=1)
                ax.add_patch(highlight)

    elif gate.name == "CZ":
        q0, q1 = gate.qubits
        y0, y1 = q0 * row_spacing, q1 * row_spacing
        ax.plot(x, y0, "o", color=s.gate_color, markersize=8, zorder=3)
        ax.plot(x, y1, "o", color=s.gate_color, markersize=8, zorder=3)
        ax.plot([x, x], [y0, y1], color=s.gate_color,
                linewidth=2.0, zorder=2)
        if has_error:
            for q in gate.qubits:
                qy = q * row_spacing
                highlight = plt.Circle((x, qy), gate_radius + 0.1, fill=True,
                                       facecolor=s.error_x_color, alpha=0.2,
                                       edgecolor="none", zorder=1)
                ax.add_patch(highlight)

    else:
        # Generic single-qubit gate box
        q = gate.qubits[0]
        y = q * row_spacing
        box_size = 0.3
        rect = mpatches.FancyBboxPatch(
            (x - box_size, y - box_size), box_size * 2, box_size * 2,
            boxstyle="round,pad=0.06",
            facecolor="white" if not has_error else s.error_x_color,
            edgecolor=s.gate_color,
            alpha=0.95 if not has_error else 0.4,
            linewidth=2.0, zorder=2,
        )
        ax.add_patch(rect)
        ax.text(x, y, gate.name, ha="center", va="center",
                fontsize=s.font_size, color=s.gate_color,
                fontweight="bold", zorder=3)
