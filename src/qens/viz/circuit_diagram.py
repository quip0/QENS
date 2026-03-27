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

    if figsize is None:
        figsize = (max(6, depth * 1.2 + 2), max(3, nq * 0.6 + 1))

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_xlim(-0.5, depth + 0.5)
    ax.set_ylim(-0.5, nq - 0.5)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(s.background_color)

    # Draw qubit wires
    for q in range(nq):
        ax.plot(
            [-0.3, depth + 0.3], [q, q],
            color=s.wire_color, linewidth=1.0, zorder=0,
        )
        ax.text(
            -0.5, q, f"q{q}",
            ha="right", va="center",
            fontsize=s.font_size, color=s.text_color,
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
        x = m_idx
        for gate in moment.gates:
            _draw_gate(ax, gate, x, error_set, m_idx, s)

    # Legend
    if error_set:
        legend_elements = [
            mpatches.Patch(facecolor=s.error_x_color, alpha=0.3,
                           edgecolor=s.error_x_color, label="Error-prone"),
            mpatches.Patch(facecolor=s.gate_color, alpha=0.8,
                           edgecolor=s.gate_color, label="Clean gate"),
        ]
        ax.legend(handles=legend_elements, loc="upper right",
                  fontsize=s.font_size - 1, framealpha=0.9)

    fig.tight_layout()
    return FigureHandle(fig=fig, axes=ax)


def _draw_gate(
    ax: Any,
    gate: Gate,
    x: float,
    error_set: set[tuple[int, int]],
    m_idx: int,
    s: QENSStyle,
) -> None:
    """Draw a single gate on the circuit diagram."""
    has_error = any((m_idx, q) in error_set for q in gate.qubits)

    if gate.name == "M":
        # Measurement symbol
        q = gate.qubits[0]
        circle = plt.Circle((x, q), 0.2, fill=True,
                             facecolor=s.measurement_color, alpha=0.8,
                             edgecolor=s.measurement_color, zorder=2)
        ax.add_patch(circle)
        ax.text(x, q, "M", ha="center", va="center",
                fontsize=s.font_size - 1, color="white", fontweight="bold", zorder=3)
        if has_error:
            highlight = plt.Circle((x, q), 0.3, fill=True,
                                   facecolor=s.error_x_color, alpha=0.2,
                                   edgecolor=s.error_x_color, zorder=1)
            ax.add_patch(highlight)

    elif gate.name == "R":
        q = gate.qubits[0]
        ax.text(x, q, "|0>", ha="center", va="center",
                fontsize=s.font_size - 1, color=s.text_color, zorder=3,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="#ECF0F1",
                          edgecolor=s.wire_color, alpha=0.9))

    elif gate.name in ("CX", "CNOT"):
        ctrl, tgt = gate.qubits
        # Control dot
        ax.plot(x, ctrl, "o", color=s.gate_color, markersize=6, zorder=3)
        # Target circle with plus
        circle = plt.Circle((x, tgt), 0.2, fill=False,
                             edgecolor=s.gate_color, linewidth=1.5, zorder=3)
        ax.add_patch(circle)
        ax.plot([x, x], [tgt - 0.2, tgt + 0.2],
                color=s.gate_color, linewidth=1.5, zorder=3)
        # Connecting line
        ax.plot([x, x], [ctrl, tgt], color=s.gate_color,
                linewidth=1.5, zorder=2)
        if has_error:
            for q in gate.qubits:
                highlight = plt.Circle((x, q), 0.3, fill=True,
                                       facecolor=s.error_x_color, alpha=0.2,
                                       edgecolor="none", zorder=1)
                ax.add_patch(highlight)

    elif gate.name == "CZ":
        q0, q1 = gate.qubits
        ax.plot(x, q0, "o", color=s.gate_color, markersize=6, zorder=3)
        ax.plot(x, q1, "o", color=s.gate_color, markersize=6, zorder=3)
        ax.plot([x, x], [q0, q1], color=s.gate_color,
                linewidth=1.5, zorder=2)
        if has_error:
            for q in gate.qubits:
                highlight = plt.Circle((x, q), 0.3, fill=True,
                                       facecolor=s.error_x_color, alpha=0.2,
                                       edgecolor="none", zorder=1)
                ax.add_patch(highlight)

    else:
        # Generic single-qubit gate box
        q = gate.qubits[0]
        rect = mpatches.FancyBboxPatch(
            (x - 0.25, q - 0.25), 0.5, 0.5,
            boxstyle="round,pad=0.05",
            facecolor="white" if not has_error else s.error_x_color,
            edgecolor=s.gate_color,
            alpha=0.9 if not has_error else 0.4,
            linewidth=1.5, zorder=2,
        )
        ax.add_patch(rect)
        ax.text(x, q, gate.name, ha="center", va="center",
                fontsize=s.font_size, color=s.gate_color,
                fontweight="bold", zorder=3)
