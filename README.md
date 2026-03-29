<p align="center">
  <img src="images/logo/widelogo.svg" width="600" alt="QENS">
</p>

<p align="center">
  <strong>Quantum Error & Noise Simulator.</strong> A Python-native toolkit for simulating quantum errors, decoding syndromes, and visualizing error-correcting codes.
</p>

QENS provides a layered API for researchers, educators, and engineers working with quantum error correction. It ships with built-in support for surface codes, repetition codes, and color codes, multiple decoder implementations, and publication-quality visualization -- all with only `numpy` and `matplotlib` as dependencies.

## Installation

```bash
pip install qens
```

For development (includes pytest, mypy, ruff):

```bash
git clone https://github.com/quipo/qens.git
cd qens
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Quickstart

```python
import qens

code = qens.RepetitionCode(distance=5)
noise = qens.DepolarizingError(p=0.05)
decoder = qens.LookupTableDecoder(code)

result = qens.ThresholdExperiment.single_point(
    code=code, noise_model=noise, decoder=decoder, shots=10_000, seed=42
)

print(f"Logical error rate: {result.logical_error_rate:.4f}")
```

## <img src="images/logo/iconlogo.svg" width="28" alt="" align="top"> Tutorials

Interactive Jupyter notebooks — the fastest way to get hands-on:

| Notebook | Description |
|----------|-------------|
| [01 — Quickstart](docs/notebooks/01_quickstart.ipynb) | End-to-end first simulation: code → noise → decoder → Monte Carlo → threshold |
| [02 — Syndrome Extraction](docs/notebooks/02_syndrome_extraction.ipynb) | How stabilizers detect errors; CSS structure; logical errors; noisy extraction |
| [03 — Decoder Comparison](docs/notebooks/03_decoder_comparison.ipynb) | Benchmarking lookup / MWPM / union-find: LER, timing, metadata |

## <img src="images/logo/iconlogo.svg" width="28" alt="" align="top"> Documentation

Full documentation is in the [`docs/`](docs/) directory:

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Installation, first simulation, project structure |
| [Core Concepts](docs/concepts.md) | QEC background, Pauli errors, CSS codes, Pauli frame model |
| [Error Models](docs/error-models.md) | All 10 noise models with examples |
| [QEC Codes](docs/codes.md) | Repetition, surface, and color codes |
| [Decoders](docs/decoders.md) | Lookup, MWPM, and union-find decoders |
| [Syndrome Extraction Guide](docs/syndrome-extraction.md) | Stabilizer measurement, XOR linearity, CSS syndromes, logical errors |
| [Decoder Comparison Guide](docs/decoder-comparison.md) | When to use each decoder and how they trade off |
| [Simulation](docs/simulation.md) | Monte Carlo sampling, threshold sweeps, Pauli frame simulator |
| [Visualization](docs/visualization.md) | Circuit diagrams, lattice views, decoding graphs, plots |
| [Extending QENS](docs/extending.md) | Custom error models, codes, decoders, visualizers |
| [API Reference](docs/api-reference.md) | Complete reference for every class and function |
| [Architecture](docs/architecture.md) | Package design, dependency graph, simulation pipeline |

## <img src="images/logo/iconlogo.svg" width="28" alt="" align="top"> Feature Highlights

- **Circuits** -- Fluent builder API for quantum circuits (`Circuit(3).h(0).cx(0, 1).measure_all()`)
- **Error Models** -- 10 built-in noise models (depolarizing, bit-flip, phase-flip, measurement, crosstalk, leakage, correlated Pauli, and more) with composition support. See [Error Models](docs/error-models.md).
- **QEC Codes** -- Repetition, surface, and color codes with stabilizers, check matrices, and syndrome circuits. See [QEC Codes](docs/codes.md).
- **Decoders** -- Lookup table, MWPM, and union-find decoders. See [Decoders](docs/decoders.md).
- **Simulation** -- Monte Carlo sampling, threshold sweeps, and Pauli frame simulation. See [Simulation](docs/simulation.md).
- **Visualization** -- Circuit diagrams, lattice views, decoding graphs, and statistical plots. See [Visualization](docs/visualization.md).
- **Extensible** -- ABC + Registry pattern for adding custom error models, codes, and decoders. See [Extending QENS](docs/extending.md).

### Lattice Views

<p align="center">
  <img src="images/clean_d5.png" width="220" alt="Surface code d=5">
  <img src="images/surface_d3_syndrome.png" width="180" alt="Surface code d=3 with syndrome">
  <img src="images/surface_d3_errors.png" width="180" alt="Surface code d=3 with errors">
  <img src="images/rep_d5_lattice.png" width="180" alt="Repetition code d=5">
</p>

### Color Codes

<p align="center">
  <img src="images/color_488_d3.png" width="250" alt="Color code 4.8.8 d=3">
  <img src="images/color_666_d3.png" width="250" alt="Color code 6.6.6 d=3">
</p>

### Circuits & Decoding

<p align="center">
  <img src="images/syndrome_circuit.png" width="400" alt="Syndrome extraction circuit">
</p>
<p align="center">
  <img src="images/decoding_graph.png" width="300" alt="MWPM decoding graph">
</p>

### Statistical Plots

<p align="center">
  <img src="images/threshold_plot.png" width="300" alt="Threshold plot">
  <img src="images/logical_rates.png" width="280" alt="Logical error rates">
</p>

## <img src="images/logo/iconlogo.svg" width="28" alt="" align="top"> Architecture

```
qens/
  core/        Types, Circuit, Gate, NoiseChannel, Registry
  noise/       ErrorModel ABC + 8 built-in models + ComposedNoiseModel
  codes/       QECCode ABC + RepetitionCode, SurfaceCode, ColorCode
  decoders/    Decoder ABC + Lookup, UnionFind, MWPM
  simulation/  NoisySampler, PauliFrameSimulator, ThresholdExperiment
  viz/         Circuit diagrams, lattice views, decoding graphs, stats plots
  utils/       Pauli algebra, GF(2) sparse matrices, seeded RNG
```

## Examples

For interactive walkthroughs, open the [tutorial notebooks](docs/notebooks/).

Script-based examples for quick CLI use:

```bash
python3 examples/03_custom_noise_model.py       # Composed noise + visualization
python3 examples/04_visualization_gallery.py    # All visualization types
```

## Testing

```bash
pytest                    # 194 tests
ruff check src/qens/      # Lint
```

## License

MIT
