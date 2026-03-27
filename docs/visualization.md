<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Visualization Guide

This guide covers the visualization functions in QENS: circuit diagrams,
lattice views, decoding graph plots, and statistical charts. All functions
return a `FigureHandle` that wraps a matplotlib figure for consistent
save/show/close operations.

---

## Overview

QENS provides six visualization functions:

| Function | Description |
|---|---|
| `draw_circuit` | Quantum circuit diagram with optional error annotations. |
| `draw_lattice` | Code lattice with optional syndrome and error overlays. |
| `draw_decoding_graph` | Decoding graph with defects and matching edges. |
| `plot_threshold` | Logical vs. physical error rate threshold plot. |
| `plot_logical_rates` | Bar chart of logical error rates by distance. |
| `plot_histogram` | General-purpose histogram for simulation statistics. |

All functions are importable from the top-level package:

```python
from qens import (
    draw_circuit, draw_lattice, draw_decoding_graph,
    plot_threshold, plot_logical_rates, plot_histogram,
)
```

### FigureHandle

Every visualization function returns a `FigureHandle` with three methods:

| Method | Description |
|---|---|
| `save(path, dpi=150, **kwargs)` | Save the figure to a file. |
| `show()` | Display the figure interactively (calls `plt.show()`). |
| `close()` | Close the figure and free memory (calls `plt.close(fig)`). |

The underlying matplotlib objects are accessible as `fig.fig` (the `Figure`)
and `fig.axes` (the `Axes`).

### Headless Environments

If you are running in a headless environment (e.g., a server or CI), set the
matplotlib backend before importing QENS visualization functions:

```python
import matplotlib
matplotlib.use("Agg")

from qens import draw_circuit, draw_lattice
```

---

## Circuit Diagrams

```python
draw_circuit(
    circuit,
    noise_model=None,
    error_locations=None,
    highlight_errors=False,
    style=None,
    figsize=None,
)
```

Draws a quantum circuit with qubit wires, gate symbols, and optional error
annotations.

**Gate symbols:**

- **H, X, Z** -- Drawn as labeled boxes on the wire.
- **CX (CNOT)** -- Control dot connected by a vertical line to a target
  circle-with-plus.
- **CZ** -- Two dots connected by a vertical line.
- **M** -- Filled circle with "M" label.
- **R (reset)** -- Labeled `|0>` box.

### Basic Circuit

```python
import matplotlib
matplotlib.use("Agg")

from qens.core.circuit import Circuit
from qens import draw_circuit

# Build a simple circuit
circuit = Circuit(3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure_all()

fig = draw_circuit(circuit)
fig.save("basic_circuit.png")
fig.close()
```

### Circuit with Noise Annotations

When you pass a `noise_model` and set `highlight_errors=True`, gates where the
noise model applies are highlighted with a red halo. The model's `applies_to`
method determines which gates are annotated.

```python
import matplotlib
matplotlib.use("Agg")

from qens.core.circuit import Circuit
from qens.noise.pauli import DepolarizingError
from qens import draw_circuit

circuit = Circuit(3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure_all()

noise = DepolarizingError(p=0.01)
fig = draw_circuit(circuit, noise_model=noise, highlight_errors=True)
fig.save("noisy_circuit.png")
fig.close()
```

### Explicit Error Locations

You can manually specify which (moment, qubit) pairs to highlight:

```python
import matplotlib
matplotlib.use("Agg")

from qens.core.circuit import Circuit
from qens import draw_circuit

circuit = Circuit(3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure_all()

# Highlight specific locations
error_locs = [(1, 0), (1, 1), (2, 1), (2, 2)]
fig = draw_circuit(circuit, error_locations=error_locs)
fig.save("circuit_with_errors.png")
fig.close()
```

---

## Lattice Views

```python
draw_lattice(
    code,
    syndrome=None,
    error=None,
    style=None,
    figsize=None,
    show_labels=True,
    title=None,
)
```

Draws the code lattice, showing data qubits as circles and ancilla qubits as
squares. Edges between connected qubits are drawn as lines.

**Overlays:**

- **Syndrome** -- Active ancilla qubits (syndrome bit = 1) are highlighted in
  red with an enlarged marker.
- **Error** -- Data qubits are colored by error type: X = red, Y = purple,
  Z = blue.

A legend is automatically generated based on the overlays present.

### Basic Lattice

```python
import matplotlib
matplotlib.use("Agg")

from qens.codes.repetition import RepetitionCode
from qens import draw_lattice

code = RepetitionCode(distance=5)
fig = draw_lattice(code, title="Repetition Code d=5")
fig.save("rep_lattice.png")
fig.close()
```

### Surface Code Lattice

```python
import matplotlib
matplotlib.use("Agg")

from qens.codes.surface import SurfaceCode
from qens import draw_lattice

code = SurfaceCode(distance=3)
fig = draw_lattice(code, title="Surface Code d=3")
fig.save("surface_lattice.png")
fig.close()
```

### Lattice with Syndrome Overlay

```python
import matplotlib
matplotlib.use("Agg")

import numpy as np
from qens.codes.surface import SurfaceCode
from qens.core.types import PauliOp
from qens import draw_lattice

code = SurfaceCode(distance=3)

# Inject an X error on the center qubit
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[4] = PauliOp.X

syndrome = code.compute_syndrome(error)

fig = draw_lattice(code, syndrome=syndrome, title="d=3 Surface Code with Syndrome")
fig.save("lattice_with_syndrome.png")
fig.close()
```

### Lattice with Error Overlay

```python
import matplotlib
matplotlib.use("Agg")

import numpy as np
from qens.codes.surface import SurfaceCode
from qens.core.types import PauliOp
from qens import draw_lattice

code = SurfaceCode(distance=3)

# Multi-type error
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[0] = PauliOp.X  # red
error[4] = PauliOp.Y  # purple
error[8] = PauliOp.Z  # blue

syndrome = code.compute_syndrome(error)

fig = draw_lattice(code, syndrome=syndrome, error=error, title="Error Overlay")
fig.save("lattice_with_errors.png")
fig.close()
```

---

## Decoding Graphs

```python
draw_decoding_graph(
    decoder,
    syndrome=None,
    correction=None,
    decode_result=None,
    show_matching=True,
    style=None,
    figsize=None,
    title=None,
)
```

Visualizes the decoding graph structure. The graph is obtained by calling
`decoder.build_decoding_graph()`.

**Elements drawn:**

- **Stabilizer nodes** -- Small circles, positioned at the centroid of their
  support qubits.
- **Boundary node** -- Diamond marker at the edge of the graph.
- **Graph edges** -- Light gray lines between connected stabilizers.
- **Defects** -- Non-zero syndrome bits highlighted as larger red circles.
- **Matching edges** -- When a `decode_result` with `"matching"` in its
  metadata is provided and `show_matching=True`, matched pairs are connected
  by thick orange lines.

### Example: Decode and Visualize

```python
import matplotlib
matplotlib.use("Agg")

import numpy as np
from qens.codes.surface import SurfaceCode
from qens.decoders.mwpm import MWPMDecoder
from qens.core.types import PauliOp
from qens import draw_decoding_graph

code = SurfaceCode(distance=3)
decoder = MWPMDecoder(code)
decoder.precompute()

# Inject an error
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[3] = PauliOp.X

# Decode
syndrome = code.compute_syndrome(error)
result = decoder.decode(syndrome)

# Visualize with matching
fig = draw_decoding_graph(
    decoder,
    syndrome=syndrome,
    decode_result=result,
    show_matching=True,
    title="MWPM Decoding Graph",
)
fig.save("decoding_graph.png")
fig.close()
```

---

## Statistical Plots

### Threshold Plot

```python
plot_threshold(
    result,
    style=None,
    figsize=(8, 6),
    log_scale=True,
    title=None,
)
```

The standard QEC threshold plot: logical error rate versus physical error rate,
with one line per code distance. At the threshold, lines for different
distances should cross. Below threshold, larger codes perform better; above
threshold, larger codes perform worse.

```python
import matplotlib
matplotlib.use("Agg")

from qens.codes.repetition import RepetitionCode
from qens.decoders.lookup import LookupTableDecoder
from qens.noise.pauli import BitFlipError
from qens.simulation.experiment import ThresholdExperiment
from qens import plot_threshold

experiment = ThresholdExperiment(
    code_class=RepetitionCode,
    distances=[3, 5, 7],
    physical_error_rates=[0.01, 0.02, 0.05, 0.1, 0.15, 0.2],
    noise_model_factory=lambda p: BitFlipError(p=p),
    decoder_class=LookupTableDecoder,
    shots_per_point=2_000,
    seed=42,
)

result = experiment.run()

fig = plot_threshold(result, title="Repetition Code Threshold")
fig.save("threshold.png")
fig.close()
```

### Logical Rates Bar Chart

```python
plot_logical_rates(
    distances,
    logical_rates,
    style=None,
    figsize=(6, 4),
    title=None,
)
```

A bar chart comparing logical error rates across different code distances at a
fixed physical error rate.

```python
import matplotlib
matplotlib.use("Agg")

from qens import plot_logical_rates

distances = [3, 5, 7, 9]
rates = [0.12, 0.05, 0.02, 0.008]

fig = plot_logical_rates(distances, rates, title="Logical Error Rate at p=0.01")
fig.save("logical_rates.png")
fig.close()
```

### Histogram

```python
plot_histogram(
    data,
    bins=30,
    style=None,
    figsize=(6, 4),
    xlabel="Value",
    title=None,
)
```

A general-purpose histogram for any simulation data.

```python
import matplotlib
matplotlib.use("Agg")

import numpy as np
from qens.codes.surface import SurfaceCode
from qens.noise.pauli import DepolarizingError
from qens.simulation.sampler import NoisySampler
from qens import plot_histogram

code = SurfaceCode(distance=3)
noise = DepolarizingError(p=0.05)
sampler = NoisySampler(seed=42)
result = sampler.sample_errors(code, noise, shots=1_000)

# Compute error weights
weights = [int(np.sum(result.sample_error(i) > 0)) for i in range(result.num_shots)]

fig = plot_histogram(weights, bins=10, xlabel="Error weight", title="Error Weight Distribution")
fig.save("error_weight_histogram.png")
fig.close()
```

---

## Customizing Style

All visualization functions accept an optional `style` parameter. The
`QENSStyle` dataclass controls every visual attribute.

### QENSStyle Fields

| Field | Default | Description |
|---|---|---|
| `data_qubit_color` | `"#4A90D9"` | Fill color for data qubit markers. |
| `ancilla_x_color` | `"#E74C3C"` | Fill color for X-type ancilla markers. |
| `ancilla_z_color` | `"#2ECC71"` | Fill color for Z-type ancilla markers. |
| `ancilla_color` | `"#F39C12"` | Fill color for generic ancilla markers. |
| `error_x_color` | `"#E74C3C"` | Color for X errors. |
| `error_y_color` | `"#9B59B6"` | Color for Y errors. |
| `error_z_color` | `"#3498DB"` | Color for Z errors. |
| `no_error_color` | `"#ECF0F1"` | Color for qubits with no error. |
| `syndrome_active` | `"#E74C3C"` | Color for active syndrome bits. |
| `syndrome_inactive` | `"#BDC3C7"` | Color for inactive syndrome bits. |
| `matching_edge_color` | `"#E67E22"` | Color for matching edges in decoding graphs. |
| `graph_edge_color` | `"#95A5A6"` | Color for graph edges and stabilizer nodes. |
| `boundary_node_color` | `"#1ABC9C"` | Color for boundary nodes. |
| `defect_color` | `"#E74C3C"` | Color for syndrome defects. |
| `gate_color` | `"#2C3E50"` | Color for gate boxes and CNOT symbols. |
| `wire_color` | `"#7F8C8D"` | Color for circuit wires. |
| `measurement_color` | `"#8E44AD"` | Color for measurement symbols. |
| `background_color` | `"#FFFFFF"` | Figure background color. |
| `text_color` | `"#2C3E50"` | Color for text labels. |
| `grid_color` | `"#ECF0F1"` | Color for grid lines and lattice edges. |
| `qubit_size` | `300.0` | Marker size for data qubits. |
| `ancilla_size` | `200.0` | Marker size for ancilla qubits. |
| `edge_width` | `1.5` | Line width for lattice edges. |
| `font_size` | `9.0` | Base font size for labels. |
| `distance_colors` | 8-color tuple | Color cycle for threshold plot distance lines. |

### Example: Dark Theme

```python
import matplotlib
matplotlib.use("Agg")

from qens.viz.style import QENSStyle
from qens.codes.surface import SurfaceCode
from qens import draw_lattice

dark_style = QENSStyle(
    background_color="#1A1A2E",
    text_color="#E0E0E0",
    data_qubit_color="#4FC3F7",
    ancilla_x_color="#EF5350",
    ancilla_z_color="#66BB6A",
    grid_color="#333355",
    gate_color="#E0E0E0",
    wire_color="#555577",
    qubit_size=350.0,
    font_size=10.0,
)

code = SurfaceCode(distance=3)
fig = draw_lattice(code, style=dark_style, title="Dark Theme Lattice")
fig.save("dark_lattice.png")
fig.close()
```

### Getting the Default Style

```python
from qens.viz.style import get_style

default = get_style()
print(f"Background: {default.background_color}")
# #FFFFFF
print(f"Font size: {default.font_size}")
# 9.0
```

---

## Saving and Exporting

The `FigureHandle.save()` method delegates to `matplotlib.figure.Figure.savefig`
with `bbox_inches="tight"` for clean output.

### Supported Formats

| Extension | Format | Notes |
|---|---|---|
| `.png` | Raster PNG | Default. Good for web and documentation. |
| `.pdf` | Vector PDF | Ideal for publications and LaTeX. |
| `.svg` | Scalable SVG | Good for web with resizing needs. |

### DPI Control

The default DPI is 150. Pass `dpi=` for custom resolution:

```python
fig.save("high_res.png", dpi=300)    # Publication quality
fig.save("screen.png", dpi=96)       # Screen resolution
fig.save("vector.pdf")               # Vector, DPI irrelevant
fig.save("scalable.svg")             # Vector, DPI irrelevant
```

### Memory Management

Always call `fig.close()` after saving, especially in loops or batch
processing, to free matplotlib memory:

```python
import matplotlib
matplotlib.use("Agg")

from qens.codes.repetition import RepetitionCode
from qens import draw_lattice

for d in [3, 5, 7, 9]:
    code = RepetitionCode(distance=d)
    fig = draw_lattice(code, title=f"Repetition d={d}")
    fig.save(f"rep_d{d}.png")
    fig.close()  # Free memory after each figure
```

---

## Next Steps

- [Error Models](error-models.md) -- Noise models whose effects you can
  visualize on circuits and lattices.
- [Codes](codes.md) -- QEC codes with lattice structures for visualization.
- [Decoders](decoders.md) -- Decoders whose graphs and matchings can be
  plotted.
- [Simulation](simulation.md) -- Generate the data for threshold plots and
  histograms.
