from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from qens.core.types import Syndrome, PauliString, PauliOp
from qens.codes.base import QECCode
from qens.viz.base import FigureHandle
from qens.viz.style import QENSStyle, get_style


def draw_lattice(
    code: QECCode,
    syndrome: Syndrome | None = None,
    error: PauliString | None = None,
    style: QENSStyle | None = None,
    figsize: tuple[float, float] | None = None,
    show_labels: bool = True,
    title: str | None = None,
    **kwargs: Any,
) -> FigureHandle:
    """Draw the code lattice with optional syndrome and error overlays.

    Args:
        code: The QEC code whose lattice to draw.
        syndrome: If provided, highlights active syndrome bits.
        error: If provided, colors data qubits by error type.
        style: Visual style overrides.
        figsize: Figure size.
        show_labels: Whether to show qubit index labels.
        title: Optional figure title.

    Returns:
        FigureHandle wrapping the lattice visualization.
    """
    s = style or get_style()
    coords = code.qubit_coordinates()

    if not coords:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No coordinates available", ha="center", va="center")
        return FigureHandle(fig=fig, axes=ax)

    # Separate data and ancilla coordinates
    lattice = getattr(code, "_lattice", None) or getattr(code, "lattice", None)

    all_x = [c[1] for c in coords.values()]
    all_y = [c[0] for c in coords.values()]
    margin = 1.0

    if figsize is None:
        span_x = max(all_x) - min(all_x) + 2 * margin
        span_y = max(all_y) - min(all_y) + 2 * margin
        scale = 1.5
        figsize = (max(4, span_x * scale), max(4, span_y * scale))

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(s.background_color)

    # Draw edges
    if lattice is not None:
        for edge in lattice.edges:
            if edge.node_a in coords and edge.node_b in coords:
                ca, cb = coords[edge.node_a], coords[edge.node_b]
                ax.plot(
                    [ca[1], cb[1]], [ca[0], cb[0]],
                    color=s.grid_color, linewidth=s.edge_width,
                    zorder=0, alpha=0.6,
                )

    # Classify nodes
    nd = code.num_data_qubits

    # Draw data qubits
    for q_idx in range(nd):
        if q_idx not in coords:
            continue
        coord = coords[q_idx]
        x, y = coord[1], coord[0]

        # Determine color from error
        if error is not None and q_idx < len(error) and error[q_idx] != PauliOp.I:
            p = int(error[q_idx])
            color = {
                PauliOp.X: s.error_x_color,
                PauliOp.Y: s.error_y_color,
                PauliOp.Z: s.error_z_color,
            }.get(p, s.data_qubit_color)
        else:
            color = s.data_qubit_color

        ax.scatter(x, y, c=color, s=s.qubit_size, zorder=2,
                   edgecolors=s.text_color, linewidths=0.8)
        if show_labels:
            ax.text(x, y, str(q_idx), ha="center", va="center",
                    fontsize=s.font_size - 1, color="white",
                    fontweight="bold", zorder=3)

    # Draw ancilla qubits (stabilizer nodes)
    if lattice is not None:
        ancilla_nodes = lattice.ancilla_nodes()
        for i, node in enumerate(ancilla_nodes):
            if node.index not in coords:
                continue
            coord = coords[node.index]
            x, y = coord[1], coord[0]

            # Base color by ancilla type
            if "x" in node.role:
                base_color = s.ancilla_x_color
            elif "z" in node.role:
                base_color = s.ancilla_z_color
            else:
                base_color = s.ancilla_color

            # Highlight if syndrome is active
            if syndrome is not None and i < len(syndrome) and syndrome[i]:
                color = s.syndrome_active
                marker = "s"
                size = s.ancilla_size * 1.3
            else:
                color = base_color
                marker = "s"
                size = s.ancilla_size

            ax.scatter(x, y, c=color, s=size, marker=marker,
                       zorder=2, edgecolors=s.text_color, linewidths=0.8,
                       alpha=0.7)

    # Title
    if title:
        ax.set_title(title, fontsize=s.font_size + 2, color=s.text_color, pad=10)
    else:
        ax.set_title(code.name, fontsize=s.font_size + 2, color=s.text_color, pad=10)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=s.data_qubit_color, label="Data qubit"),
        mpatches.Patch(facecolor=s.ancilla_x_color, alpha=0.7, label="X stabilizer"),
        mpatches.Patch(facecolor=s.ancilla_z_color, alpha=0.7, label="Z stabilizer"),
    ]
    if syndrome is not None:
        legend_elements.append(
            mpatches.Patch(facecolor=s.syndrome_active, label="Active syndrome")
        )
    if error is not None:
        legend_elements.extend([
            mpatches.Patch(facecolor=s.error_x_color, label="X error"),
            mpatches.Patch(facecolor=s.error_y_color, label="Y error"),
            mpatches.Patch(facecolor=s.error_z_color, label="Z error"),
        ])
    ax.legend(handles=legend_elements, loc="upper right",
              fontsize=s.font_size - 1, framealpha=0.9)

    fig.tight_layout()
    return FigureHandle(fig=fig, axes=ax)
