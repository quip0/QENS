# QENS Documentation

**Quantum Error and Noise Simulation SDK** -- simulate quantum errors, decode syndromes, and visualize error-correcting codes in pure Python.

Version 0.1.0 | [GitHub](https://github.com/quip0/QENS) | [MIT License](../LICENSE)

---

## Key Features

- **Error simulation** -- 8 built-in noise models covering Pauli, measurement, gate, correlated, and leakage errors, with composition support
- **QEC codes** -- Surface codes, repetition codes, and color codes with stabilizer generators, check matrices, and syndrome circuits
- **Decoders** -- Lookup table, minimum-weight perfect matching, and union-find decoders in pure Python
- **Visualization** -- Publication-quality circuit diagrams, lattice views, decoding graphs, and statistical plots
- **Extensible** -- ABC + Registry pattern at every layer; add custom components without modifying the core
- **Minimal dependencies** -- Only `numpy` and `matplotlib`; Python 3.11+

---

## Quick Example

```python
import qens

code = qens.SurfaceCode(distance=3)
noise = qens.DepolarizingError(p=0.01)
decoder = qens.MWPMDecoder(code)
result = qens.ThresholdExperiment.single_point(code=code, noise_model=noise, decoder=decoder, shots=10_000)
print(f"Logical error rate: {result.logical_error_rate:.4f}")
```

---

## Documentation Map

### Getting Started

- [Getting Started](getting-started.md) -- Installation, first simulation, project structure

### Background

- [Core Concepts](concepts.md) -- Quantum error correction, Pauli errors, CSS codes, Pauli frame simulation

### User Guides

- [Error Models](error-models.md) -- Pauli, measurement, gate, correlated, leakage, and composed noise models
- [QEC Codes](codes.md) -- Repetition, surface, and color codes; stabilizers, syndromes, and lattices
- [Decoders](decoders.md) -- Lookup table, MWPM, and union-find decoders
- [Simulation](simulation.md) -- Monte Carlo sampling, threshold sweeps, Pauli frame simulator
- [Visualization](visualization.md) -- Circuit diagrams, lattice views, decoding graphs, statistical plots

### Developer Guides

- [Extending QENS](extending.md) -- Custom error models, codes, decoders, and visualizers
- [API Reference](api-reference.md) -- Complete reference for every class, function, and type
- [Architecture](architecture.md) -- Package structure, design patterns, dependency graph, simulation pipeline

### Project

- [Contributing](../CONTRIBUTING.md) -- How to report bugs, submit patches, and run tests
- [Changelog](../CHANGELOG.md) -- Release history
