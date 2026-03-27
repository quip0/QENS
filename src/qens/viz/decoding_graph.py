from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from qens.core.types import Syndrome, PauliString
from qens.decoders.base import Decoder, DecoderResult
from qens.viz.base import FigureHandle
from qens.viz.style import QENSStyle, get_style


def draw_decoding_graph(
    decoder: Decoder,
    syndrome: Syndrome | None = None,
    correction: PauliString | None = None,
    decode_result: DecoderResult | None = None,
    show_matching: bool = True,
    style: QENSStyle | None = None,
    figsize: tuple[float, float] | None = None,
    title: str | None = None,
    **kwargs: Any,
) -> FigureHandle:
    """Visualize the decoding graph with syndrome defects and matching.

    Args:
        decoder: Decoder whose graph structure to visualize.
        syndrome: Syndrome to overlay as defects.
        correction: Correction to highlight on the graph.
        decode_result: Full decode result (alternative to separate syndrome/correction).
        show_matching: Whether to show matching edges from decode metadata.
        style: Visual style overrides.
        figsize: Figure size.
        title: Optional figure title.

    Returns:
        FigureHandle wrapping the decoding graph visualization.
    """
    s = style or get_style()

    try:
        graph = decoder.build_decoding_graph()
    except NotImplementedError:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Decoder does not provide a decoding graph",
                ha="center", va="center", fontsize=s.font_size)
        ax.axis("off")
        return FigureHandle(fig=fig, axes=ax)

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    boundary_nodes = set(graph.get("boundary_nodes", []))

    if not nodes:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Empty graph", ha="center", va="center")
        ax.axis("off")
        return FigureHandle(fig=fig, axes=ax)

    # --- Node positioning ---
    # Use stabilizer qubit positions from the code lattice for grid alignment
    code = decoder.code
    code_coords = code.qubit_coordinates()
    stabs = code.stabilizer_generators()

    pos: dict[int, tuple[float, float]] = {}
    for i, stab in enumerate(stabs):
        if i in [n for n in nodes if n not in boundary_nodes]:
            qubit_coords = [code_coords.get(q, (0, 0)) for q in stab.qubits]
            if qubit_coords:
                avg_y = sum(c[0] for c in qubit_coords) / len(qubit_coords)
                avg_x = sum(c[1] for c in qubit_coords) / len(qubit_coords)
                pos[i] = (avg_x, avg_y)

    # Place boundary nodes clearly outside the lattice
    if boundary_nodes and pos:
        all_x = [p[0] for p in pos.values()]
        all_y = [p[1] for p in pos.values()]
        x_max, y_mid = max(all_x), np.mean(all_y)
        for j, bn in enumerate(sorted(boundary_nodes)):
            offset = (j - (len(boundary_nodes) - 1) / 2) * 0.8
            pos[bn] = (x_max + 2.0, y_mid + offset)

    if figsize is None:
        figsize = (10, 7)

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(s.background_color)

    # Defect set
    defects: set[int] = set()
    if syndrome is not None:
        defects = set(np.nonzero(syndrome)[0].tolist())

    # Collect matching edges for highlighting
    matching_set: set[frozenset[int]] = set()
    if show_matching and decode_result and "matching" in decode_result.metadata:
        for match in decode_result.metadata["matching"]:
            matching_set.add(frozenset((match[0], match[1])))

    # --- Draw edges ---
    for edge_data in edges:
        if isinstance(edge_data, dict):
            u, v = edge_data["from"], edge_data["to"]
            weight = edge_data.get("weight", 1.0)
        else:
            u, v = edge_data[0], edge_data[1]
            weight = 1.0

        if u not in pos or v not in pos:
            continue

        x0, y0 = pos[u]
        x1, y1 = pos[v]

        is_matched = frozenset((u, v)) in matching_set

        if is_matched:
            # Matching edge: bold orange
            ax.plot(
                [x0, x1], [y0, y1],
                color=s.matching_edge_color, linewidth=3.5,
                alpha=0.9, zorder=2, solid_capstyle="round",
            )
        else:
            # Normal edge: subtle, clean
            ax.plot(
                [x0, x1], [y0, y1],
                color=s.graph_edge_color, linewidth=1.5,
                alpha=0.35, zorder=0,
            )

        # Edge weight label at midpoint
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(
            mx, my, f"{weight:.1f}",
            ha="center", va="center",
            fontsize=s.font_size - 3,
            color=s.graph_edge_color,
            alpha=0.6, zorder=1,
            bbox=dict(
                boxstyle="round,pad=0.1",
                facecolor=s.background_color, edgecolor="none", alpha=0.8,
            ),
        )

    # --- Draw nodes ---
    for node in nodes:
        if node not in pos:
            continue
        x, y = pos[node]

        if node in boundary_nodes:
            color = s.boundary_node_color
            marker = "D"
            size = s.ancilla_size * 0.7
            edge_color = s.boundary_node_color
            lw = 2.0
        elif node in defects:
            color = s.defect_color
            marker = "o"
            size = s.qubit_size * 0.6
            edge_color = "#C0392B"
            lw = 2.0
        else:
            color = s.graph_edge_color
            marker = "o"
            size = s.ancilla_size * 0.5
            edge_color = s.text_color
            lw = 1.0

        ax.scatter(
            x, y, c=color, s=size, marker=marker,
            edgecolors=edge_color, linewidths=lw, zorder=5,
        )

        # Node index label
        label_color = "white" if node in defects else s.text_color
        ax.text(
            x, y, str(node), ha="center", va="center",
            fontsize=s.font_size - 2, color=label_color,
            fontweight="bold", zorder=6,
        )

    # Title
    title_text = title or f"Decoding Graph — {code.name}"
    if defects:
        title_text += f"  ({len(defects)} defect{'s' if len(defects) != 1 else ''})"
    ax.set_title(
        title_text,
        fontsize=s.font_size + 3, color=s.text_color, pad=14,
        fontweight="bold",
    )

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=s.graph_edge_color, label="Stabilizer node"),
        mpatches.Patch(facecolor=s.defect_color, label="Defect (syndrome=1)"),
        mpatches.Patch(facecolor=s.boundary_node_color, label="Boundary node"),
    ]
    if show_matching:
        legend_elements.append(
            mpatches.Patch(facecolor=s.matching_edge_color, label="Matching edge")
        )
    ax.legend(
        handles=legend_elements, loc="upper right",
        fontsize=s.font_size - 1, framealpha=0.95,
        edgecolor=s.grid_color, fancybox=True,
    )

    fig.tight_layout()
    return FigureHandle(fig=fig, axes=ax)
