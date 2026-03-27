# Getting Started

This guide walks you through installing QENS and running your first quantum error correction simulation.

---

## Prerequisites

- Python 3.11 or later
- pip

---

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/quip0/QENS.git
cd QENS
pip install -e .
```

For development (adds pytest, mypy, ruff):

```bash
pip install -e ".[dev]"
```

Verify the installation:

```bash
python3 -c "import qens; print(qens.__version__)"
# 0.1.0
```

---

## Your First Simulation

This example runs a Monte Carlo simulation of the repetition code under depolarizing noise.

### Step 1: Import QENS

```python
import qens
```

The top-level `qens` module re-exports all commonly used classes. For advanced usage, import directly from submodules like `qens.noise.pauli`.

### Step 2: Create a Code

```python
code = qens.RepetitionCode(distance=5)
```

A repetition code encodes one logical qubit into `d` physical qubits arranged in a 1D chain. A distance-5 code can correct up to 2 errors.

```python
print(code.num_data_qubits)     # 5
print(code.num_ancilla_qubits)  # 4
print(code.code_distance)       # 5
```

### Step 3: Define a Noise Model

```python
noise = qens.DepolarizingError(p=0.05)
```

Depolarizing noise applies X, Y, or Z errors independently on each qubit, each with probability `p/3`. At `p=0.05`, about 1.7% of qubits experience each type of error per round.

### Step 4: Choose a Decoder

```python
decoder = qens.LookupTableDecoder(code)
```

The lookup table decoder precomputes the optimal correction for every possible syndrome. It is exact but only practical for small codes (distance 7 or below).

### Step 5: Run the Simulation

```python
result = qens.ThresholdExperiment.single_point(
    code=code,
    noise_model=noise,
    decoder=decoder,
    shots=10_000,
    seed=42,
)
```

This runs 10,000 Monte Carlo shots. Each shot samples a random error, computes the syndrome, decodes it, and checks whether the combined error and correction is a logical error.

### Step 6: Inspect Results

```python
print(f"Shots:              {result.num_shots}")
print(f"Logical errors:     {result.logical_error_count}")
print(f"Logical error rate: {result.logical_error_rate:.4f}")
```

The `SimulationResult` also provides per-shot access:

```python
syndrome_0 = result.sample_syndrome(0)  # First shot's syndrome
error_0 = result.sample_error(0)        # First shot's error
```

### Step 7: Visualize

```python
fig = qens.draw_lattice(code, title="Repetition Code (d=5)")
fig.save("lattice.png")
fig.close()
```

For headless environments, add `matplotlib.use('Agg')` before any QENS imports.

---

## Your First Threshold Sweep

A threshold experiment sweeps physical error rates across multiple code distances to find the error threshold -- the physical error rate below which larger codes perform better.

```python
import qens

experiment = qens.ThresholdExperiment(
    code_class=qens.SurfaceCode,
    distances=[3, 5, 7],
    physical_error_rates=[0.001, 0.005, 0.01, 0.02],
    noise_model_factory=lambda p: qens.DepolarizingError(p=p),
    decoder_class=qens.MWPMDecoder,
    shots_per_point=10_000,
    seed=42,
)

result = experiment.run()
```

Plot the results:

```python
fig = qens.plot_threshold(result, title="Surface Code Threshold")
fig.save("threshold.png")
fig.close()
```

The `ThresholdResult` contains a 2D numpy array of logical error rates indexed by `[distance_index, error_rate_index]`:

```python
for i, d in enumerate(result.distances):
    for j, p in enumerate(result.physical_error_rates):
        print(f"d={d}, p={p:.3f}: logical_rate={result.logical_error_rates[i, j]:.4f}")
```

---

## Running Tests

```bash
pytest
```

This runs 194 tests covering all modules in under 1 second. To also check linting:

```bash
ruff check src/qens/
```

---

## Project Structure

```
src/qens/
    __init__.py          Top-level public API
    _version.py          Version string

    core/                Types, circuit builder, noise channels, plugin registry
    noise/               Error model ABC and 8 built-in implementations
    codes/               QEC code ABC and 3 built-in code families
    decoders/            Decoder ABC and 3 built-in decoder implementations
    simulation/          Monte Carlo sampler, Pauli frame simulator, threshold experiments
    viz/                 Circuit diagrams, lattice views, decoding graphs, statistical plots
    utils/               Pauli algebra, GF(2) matrices, random number generation
```

---

## Next Steps

- [Core Concepts](concepts.md) -- Background on quantum error correction
- [Error Models](error-models.md) -- All noise model types and composition
- [QEC Codes](codes.md) -- Surface, repetition, and color codes
- [Decoders](decoders.md) -- Choosing and using decoders
- [Simulation](simulation.md) -- Running large-scale simulations
- [Visualization](visualization.md) -- Creating publication-quality figures
- [Extending QENS](extending.md) -- Adding custom components
