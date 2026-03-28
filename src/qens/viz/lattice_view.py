from __future__ import annotations

import math
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon

from qens.core.types import Syndrome, PauliString, PauliOp
from qens.codes.base import QECCode
from qens.viz.base import FigureHandle
from qens.viz.style import QENSStyle, get_style


def _convex_hull_order(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Sort points in counter-clockwise order around their centroid."""
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return sorted(points, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def _expand_polygon(
    points: list[tuple[float, float]], factor: float = 0.25,
) -> list[tuple[float, float]]:
    """Expand a polygon outward from its centroid by *factor*."""
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return [(cx + (x - cx) * (1 + factor), cy + (y - cy) * (1 + factor))
            for x, y in points]


def _greedy_3color(plaquettes: list[list[int]]) -> list[int]:
    """Assign colors 0/1/2 to plaquettes so adjacent ones differ.

    Two plaquettes are adjacent if they share any data qubit.
    Prefers the least-used color to spread all 3 colors evenly.
    """
    n = len(plaquettes)
    adj: list[set[int]] = [set() for _ in range(n)]
    qubit_to_plaq: dict[int, list[int]] = {}
    for i, plaq in enumerate(plaquettes):
        for q in plaq:
            qubit_to_plaq.setdefault(q, []).append(i)
    for indices in qubit_to_plaq.values():
        for a in indices:
            for b in indices:
                if a != b:
                    adj[a].add(b)

    colors = [-1] * n
    counts = [0, 0, 0]
    for i in range(n):
        used = {colors[j] for j in adj[i] if colors[j] >= 0}
        available = [c for c in range(3) if c not in used]
        if available:
            colors[i] = min(available, key=lambda c: counts[c])
        else:
            colors[i] = 0
        counts[colors[i]] += 1
    return colors


def _plaquette_edges(
    plaquettes: list[list[int]],
    coords: dict[int, tuple],
    dist_threshold: float = 1.6,
) -> set[tuple[int, int]]:
    """Derive data-data edges from plaquette membership."""
    edges: set[tuple[int, int]] = set()
    for plaq in plaquettes:
        for i, a in enumerate(plaq):
            if a not in coords:
                continue
            ca = coords[a]
            for b in plaq[i + 1:]:
                if b not in coords:
                    continue
                cb = coords[b]
                d = math.hypot(ca[0] - cb[0], ca[1] - cb[1])
                if d < dist_threshold:
                    edges.add((min(a, b), max(a, b)))
    return edges


# ── Color code drawing (reference-style) ─────────────────────────────

def _draw_color_code(
    ax: plt.Axes,
    code: QECCode,
    coords: dict[int, tuple],
    plaquettes: list[list[int]],
    plaq_colors: list[int],
    s: QENSStyle,
    show_labels: bool,
    syndrome: Syndrome | None,
    error: PauliString | None,
) -> None:
    """Render a color code in the qiskit-qec style.

    Opaque polygon plaquette fills with black outlines, small black dots
    for data qubits, offset labels.
    """
    nd = code.num_data_qubits
    palette = s.color_code_plaquette_colors

    # 1. Draw plaquette polygons (opaque fill, black edge)
    for p_idx, plaq in enumerate(plaquettes):
        plaq_coords = []
        for q in plaq:
            if q in coords:
                plaq_coords.append((coords[q][1], coords[q][0]))
        if len(plaq_coords) < 3:
            continue

        ci = plaq_colors[p_idx] if p_idx < len(plaq_colors) else 0
        face = palette[ci]

        ordered = _convex_hull_order(plaq_coords)
        poly = Polygon(
            ordered, closed=True,
            facecolor=face, edgecolor="black", linewidth=1.0,
            zorder=1,
        )
        ax.add_patch(poly)

    # 2. Draw data qubits as small black dots (qiskit: s=50, color=black)
    for q_idx in range(nd):
        if q_idx not in coords:
            continue
        coord = coords[q_idx]
        x, y = coord[1], coord[0]

        if error is not None and q_idx < len(error) and error[q_idx] != PauliOp.I:
            p = int(error[q_idx])
            dot_color = {
                PauliOp.X: s.error_x_color,
                PauliOp.Y: s.error_y_color,
                PauliOp.Z: s.error_z_color,
            }.get(p, "black")
            dot_size = 50
        else:
            dot_color = "black"
            dot_size = 50

        ax.scatter(x, y, c=dot_color, s=dot_size, zorder=3,
                   edgecolors="black", linewidths=0.5)

        if show_labels:
            ax.annotate(
                str(q_idx), (x, y),
                textcoords="offset points", xytext=(5, 5),
                fontsize=7, fontweight="bold", color="black",
                zorder=4,
            )

    # 3. Syndrome overlay (red stars on active ancillas)
    if syndrome is not None:
        lattice = getattr(code, "_lattice", None) or getattr(code, "lattice", None)
        if lattice is not None:
            ancilla_nodes = lattice.ancilla_nodes()
            for i, node in enumerate(ancilla_nodes):
                if node.index not in coords:
                    continue
                if i < len(syndrome) and syndrome[i]:
                    coord = coords[node.index]
                    x, y = coord[1], coord[0]
                    ax.scatter(x, y, c="red", s=100, marker="*",
                               zorder=5, edgecolors="black", linewidths=0.8)


# ── Main entry point ─────────────────────────────────────────────────

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

    lattice = getattr(code, "_lattice", None) or getattr(code, "lattice", None)

    # Detect color code
    is_color_code = hasattr(code, "_plaquettes") and hasattr(code, "_data_coords")
    plaquettes: list[list[int]] = getattr(code, "_plaquettes", []) if is_color_code else []
    plaq_color_assignment: list[int] = []
    if is_color_code and plaquettes:
        plaq_color_assignment = _greedy_3color(plaquettes)

    # ── Figure setup ─────────────────────────────────────────────────
    all_x = [c[1] for c in coords.values()]
    all_y = [c[0] for c in coords.values()]
    nd = code.num_data_qubits

    if is_color_code:
        # Color code: larger figure, visible axes, no y-inversion
        margin = 1.0
        if figsize is None:
            span_x = max(all_x) - min(all_x) + 2 * margin
            span_y = max(all_y) - min(all_y) + 2 * margin
            scale = max(0.8, min(1.2, 10.0 / max(span_x, span_y)))
            figsize = (span_x * scale, span_y * scale)

        fig, ax = plt.subplots(1, 1, figsize=figsize)
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
        ax.set_aspect("equal")
        ax.tick_params(labelsize=7)
        fig.patch.set_facecolor("white")

        _draw_color_code(ax, code, coords, plaquettes, plaq_color_assignment,
                         s, show_labels, syndrome, error)

        if title:
            ax.set_title(title, fontsize=11, pad=10, fontweight="bold")
        else:
            ax.set_title(code.name, fontsize=11, pad=10, fontweight="bold")

        # Legend / key
        cc_palette = s.color_code_plaquette_colors
        legend_handles = [
            mpatches.Patch(facecolor="black", label="Data qubit"),
        ]
        used = set(plaq_color_assignment) if plaq_color_assignment else set()
        plaq_labels = {0: "Tomato plaquette", 1: "Green plaquette", 2: "Blue plaquette"}
        for ci in sorted(used):
            legend_handles.append(
                mpatches.Patch(facecolor=cc_palette[ci],
                               edgecolor="black", linewidth=0.5,
                               label=plaq_labels[ci]))
        if error is not None:
            legend_handles.extend([
                mpatches.Patch(facecolor=s.error_x_color, label="X error"),
                mpatches.Patch(facecolor=s.error_y_color, label="Y error"),
                mpatches.Patch(facecolor=s.error_z_color, label="Z error"),
            ])
        if syndrome is not None:
            legend_handles.append(
                plt.Line2D([0], [0], marker="*", color="w",
                           markerfacecolor="red", markeredgecolor="black",
                           markersize=8, label="Active syndrome"))
        ax.legend(handles=legend_handles, loc="upper left",
                  bbox_to_anchor=(1.01, 1.0), fontsize=7, framealpha=0.9,
                  edgecolor="#cccccc", fancybox=True,
                  handlelength=1.2, handletextpad=0.5,
                  borderpad=0.4, labelspacing=0.4)

        fig.tight_layout(rect=[0, 0, 0.82, 1])
        return FigureHandle(fig=fig, axes=ax)

    # ── Surface / other codes ────────────────────────────────────────
    margin = 0.8
    if figsize is None:
        span_x = max(all_x) - min(all_x) + 2 * margin
        span_y = max(all_y) - min(all_y) + 2 * margin
        scale = 0.35
        figsize = (max(2.5, span_x * scale), max(2.2, span_y * scale))

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Plaquette colors: tomato for X, yellowgreen for Z (qiskit convention)
    x_face = "tomato"
    z_face = "yellowgreen"

    # 1. Draw stabilizer plaquettes as filled polygons with black edges
    if lattice is not None:
        for node in lattice.ancilla_nodes():
            if node.index not in coords:
                continue
            coord = coords[node.index]
            cx, cy = coord[1], coord[0]

            if "x" in node.role:
                face_color = x_face
            elif "z" in node.role:
                face_color = z_face
            else:
                continue

            # Build polygon from neighboring data qubits
            neighbors = [
                n for n in lattice.neighbors(node.index) if n < nd and n in coords
            ]
            if len(neighbors) >= 2:
                pts = [(coords[n][1], coords[n][0]) for n in neighbors]
                pts = _convex_hull_order(pts)
                poly = Polygon(
                    pts, closed=True,
                    facecolor=face_color, alpha=0.45,
                    edgecolor="black", linewidth=0.6,
                    zorder=1,
                )
                ax.add_patch(poly)

    # 2. Draw edges
    if lattice is not None:
        for edge in lattice.edges:
            if edge.node_a in coords and edge.node_b in coords:
                ca, cb = coords[edge.node_a], coords[edge.node_b]
                ax.plot(
                    [ca[1], cb[1]], [ca[0], cb[0]],
                    color="#aaaaaa", linewidth=0.6,
                    zorder=0, alpha=0.5,
                )

    # 3. Draw data qubits as small black dots
    for q_idx in range(nd):
        if q_idx not in coords:
            continue
        coord = coords[q_idx]
        x, y = coord[1], coord[0]

        if error is not None and q_idx < len(error) and error[q_idx] != PauliOp.I:
            p = int(error[q_idx])
            dot_color = {
                PauliOp.X: s.error_x_color,
                PauliOp.Y: s.error_y_color,
                PauliOp.Z: s.error_z_color,
            }.get(p, "black")
            dot_size = 50
        else:
            dot_color = "black"
            dot_size = 30

        ax.scatter(x, y, c=dot_color, s=dot_size, zorder=3,
                   edgecolors="black", linewidths=0.4)

        if show_labels:
            ax.annotate(
                str(q_idx), (x, y),
                textcoords="offset points", xytext=(4, 4),
                fontsize=5, fontweight="bold", color="#333333", zorder=4,
            )

    # 4. Syndrome overlay: red star markers on active ancillas
    if syndrome is not None and lattice is not None:
        ancilla_nodes = lattice.ancilla_nodes()
        for i, node in enumerate(ancilla_nodes):
            if node.index not in coords:
                continue
            if i < len(syndrome) and syndrome[i]:
                coord = coords[node.index]
                x, y = coord[1], coord[0]
                ax.scatter(x, y, c="red", s=60, marker="*",
                           zorder=5, edgecolors="darkred", linewidths=0.3)

    # Title
    if title:
        ax.set_title(title, fontsize=7, color="black",
                     pad=4, fontweight="bold")
    else:
        ax.set_title(code.name, fontsize=7, color="black",
                     pad=4, fontweight="bold")

    # Legend / key
    legend_handles = [
        mpatches.Patch(facecolor="black", label="Data qubit"),
        mpatches.Patch(facecolor=x_face, alpha=0.6, edgecolor="black",
                       linewidth=0.5, label="X stabilizer"),
        mpatches.Patch(facecolor=z_face, alpha=0.6, edgecolor="black",
                       linewidth=0.5, label="Z stabilizer"),
    ]
    if error is not None:
        legend_handles.extend([
            mpatches.Patch(facecolor=s.error_x_color, label="X error"),
            mpatches.Patch(facecolor=s.error_y_color, label="Y error"),
            mpatches.Patch(facecolor=s.error_z_color, label="Z error"),
        ])
    if syndrome is not None:
        legend_handles.append(
            plt.Line2D([0], [0], marker="*", color="w",
                       markerfacecolor="red", markeredgecolor="darkred",
                       markersize=8, label="Active syndrome"))
    ax.legend(handles=legend_handles, loc="upper left",
              bbox_to_anchor=(1.01, 1.0), fontsize=5, framealpha=0.9,
              edgecolor="#cccccc", fancybox=True,
              handlelength=1.0, handletextpad=0.4,
              borderpad=0.3, labelspacing=0.3)

    fig.tight_layout(rect=[0, 0, 0.82, 1])
    return FigureHandle(fig=fig, axes=ax)
