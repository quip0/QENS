<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Architecture

This document describes the internal architecture of QENS for contributors and advanced users.

---

## Design Principles

1. **Pure Python + numpy.** No compiled extensions, Cython, or Rust bindings. The only runtime dependencies are numpy (numerics) and matplotlib (visualization). This keeps installation trivial and the code auditable.

2. **ABC + Registry for extensibility.** Every major subsystem (noise, codes, decoders, visualization) has an abstract base class defining the interface and a `Registry[T]` instance for runtime discovery. Users extend the SDK by subclassing and registering, not by modifying core code.

3. **Pauli frame simulation.** The core simulation engine tracks Pauli errors through Clifford circuits in O(n) time per gate, avoiding the exponential cost of statevector or density-matrix simulation. This enables simulation of codes with thousands of qubits.

4. **Layered API.** The top-level `qens` module re-exports beginner-friendly names (`RepetitionCode`, `DepolarizingError`, `draw_lattice`). Power users import directly from submodules (`qens.noise.pauli`, `qens.utils.sparse`) for fine-grained control.

5. **Type annotations throughout.** All public APIs have type annotations. Type aliases (`PauliString`, `Syndrome`, `Coordinate`) give semantic meaning to numpy arrays.

---

## Package Structure

```
src/qens/
    __init__.py              Public API re-exports
    _version.py              Single source of truth for version string

    core/
        types.py             PauliOp, Outcome, PauliString, Syndrome, KrausMatrix,
                             QubitIndex, Coordinate type aliases
        circuit.py           Gate, Moment, Circuit (fluent builder)
        qubit.py             Qubit, QubitRole
        noise_channel.py     NoiseChannel (Kraus operator storage + validation)
        registry.py          Generic Registry[T] class

    noise/
        base.py              ErrorModel ABC
        pauli.py             BitFlipError, PhaseFlipError, DepolarizingError, PauliYError
        measurement.py       MeasurementError (asymmetric readout)
        gate.py              CoherentRotationError, CrosstalkError
        correlated.py        CorrelatedPauliError (joint qubit pair errors)
        leakage.py           LeakageError (non-computational state transitions)
        composed.py          ComposedNoiseModel (stacks multiple models)

    codes/
        base.py              QECCode ABC, Stabilizer, LogicalOperator
        lattice.py           LatticeNode, LatticeEdge, Lattice
        repetition.py        RepetitionCode (1D chain)
        surface.py           SurfaceCode (rotated, d x d grid)
        color.py             ColorCode (4.8.8 and 6.6.6 lattice types)

    decoders/
        base.py              Decoder ABC, DecoderResult
        lookup.py            LookupTableDecoder (exact, small codes)
        mwpm.py              MWPMDecoder (greedy matching)
        union_find.py        UnionFindDecoder (almost-linear time)

    simulation/
        result.py            SimulationResult, ThresholdResult
        frame.py             PauliFrameSimulator
        sampler.py           NoisySampler (Monte Carlo loop)
        experiment.py        ThresholdExperiment (sweep utility)

    viz/
        base.py              Visualizer ABC, FigureHandle
        style.py             QENSStyle, DEFAULT_STYLE, get_style()
        circuit_diagram.py   draw_circuit()
        lattice_view.py      draw_lattice()
        decoding_graph.py    draw_decoding_graph()
        stats.py             plot_threshold(), plot_logical_rates(), plot_histogram()

    utils/
        random.py            get_rng() -- seeded numpy Generator factory
        pauli_algebra.py     Pauli multiplication, commutation, symplectic inner product
        sparse.py            GF2Matrix -- sparse binary matrix over GF(2)
```

---

## Dependency Graph

Each layer depends only on layers to its left. There are no circular dependencies.

```
utils  -->  core  -->  noise  -->  codes  -->  decoders  -->  simulation  -->  viz
```

In detail:

| Module | Depends on |
|--------|-----------|
| `utils` | numpy only |
| `core` | `utils` |
| `noise` | `core`, `utils` |
| `codes` | `core`, `utils` |
| `decoders` | `core`, `codes` (TYPE_CHECKING only for codes) |
| `simulation` | `core`, `noise`, `codes`, `decoders`, `utils` |
| `viz` | `core`, `codes`, `decoders`, `simulation` (for result types) |

The `decoders` module uses `TYPE_CHECKING` imports for `QECCode` to avoid hard runtime dependencies on the codes module, enabling cleaner separation.

---

## Core Abstractions

### ErrorModel

Defined in `qens/noise/base.py`. The contract:

| Method | Required | Purpose |
|--------|----------|---------|
| `sample_errors(num_qubits, affected_qubits, rng)` | Yes | Sample a PauliString error |
| `to_channel(affected_qubits)` | No | Return Kraus representation |
| `applies_to(gate)` | No | Filter which gates this model targets (default: all) |
| `__repr__()` | Yes | String representation |

Error models are stateless except for `LeakageError`, which tracks leaked qubits.

### QECCode

Defined in `qens/codes/base.py`. The contract:

| Property/Method | Required | Purpose |
|-----------------|----------|---------|
| `name` | Yes | Human-readable name |
| `num_data_qubits` | Yes | Number of data qubits |
| `num_ancilla_qubits` | Yes | Number of ancilla qubits |
| `code_distance` | Yes | Code distance d |
| `stabilizer_generators()` | Yes | List of Stabilizer objects |
| `logical_operators()` | Yes | List of LogicalOperator objects |
| `check_matrix()` | Yes | Parity check matrix as numpy array |
| `syndrome_circuit(rounds)` | Yes | Build syndrome extraction Circuit |
| `qubit_coordinates()` | Yes | Map qubit index to coordinate |
| `compute_syndrome(error)` | No | Provided by base class |
| `is_logical_error(residual)` | No | Provided by base class |

The base class implements `compute_syndrome` via the symplectic inner product and `is_logical_error` by checking commutation with stabilizers and anticommutation with logical operators.

### Decoder

Defined in `qens/decoders/base.py`. The contract:

| Method | Required | Purpose |
|--------|----------|---------|
| `decode(syndrome)` | Yes | Return DecoderResult (correction + metadata) |
| `precompute()` | No | One-time setup (graphs, tables) |
| `build_decoding_graph()` | No | Return graph dict for visualization |

The `DecoderResult.success` field is a provisional estimate. The decoder does not know the actual error, only the syndrome. True success is determined in `NoisySampler.run()` by checking `is_logical_error(error * correction)`.

### Visualizer

Defined in `qens/viz/base.py`. The contract:

| Method | Required | Purpose |
|--------|----------|---------|
| `draw(**kwargs)` | Yes | Return FigureHandle wrapping matplotlib |

In practice, the standalone functions (`draw_circuit`, `draw_lattice`, etc.) are used more often than subclassing `Visualizer`.

---

## Registry System

`Registry[T]` is a generic class in `qens/core/registry.py`:

```python
class Registry(Generic[T]):
    def register(self, name: str, cls: type[T]) -> None: ...
    def get(self, name: str) -> type[T]: ...
    def list_registered(self) -> list[str]: ...
    def __contains__(self, name: str) -> bool: ...
```

Each subsystem instantiates a module-level registry and auto-registers built-in implementations in its `__init__.py`:

| Registry | Module | Built-in entries |
|----------|--------|-----------------|
| `noise_registry` | `qens.noise` | bit_flip, phase_flip, depolarizing, pauli_y, measurement, coherent_rotation, crosstalk, correlated_pauli, leakage |
| `code_registry` | `qens.codes` | repetition, surface, color |
| `decoder_registry` | `qens.decoders` | lookup, union_find, mwpm |
| `viz_registry` | `qens.viz` | (empty by default -- visualization uses standalone functions) |

Duplicate names raise `ValueError`. Missing names raise `KeyError` with a message listing available entries.

---

## Simulation Pipeline

`NoisySampler.run()` orchestrates the full Monte Carlo loop:

```
For each shot:
    1. ErrorModel.sample_errors()      --> PauliString (the error)
    2. QECCode.compute_syndrome()      --> Syndrome (binary vector)
    3. Decoder.decode()                --> DecoderResult (correction)
    4. pauli_string_multiply(error, correction)  --> residual
    5. QECCode.is_logical_error()      --> bool
```

`ThresholdExperiment.run()` wraps this in a double loop over distances and error rates, constructing fresh code/decoder/noise instances for each point.

### Data Flow

```
NoisySampler.run(code, noise, decoder, shots)
    --> SimulationResult
            .syndromes:      list[Syndrome]       (one per shot)
            .errors:         list[PauliString]     (one per shot)
            .corrections:    list[PauliString]     (one per shot)
            .logical_errors: list[bool]            (one per shot)

ThresholdExperiment.run()
    --> ThresholdResult
            .distances:            list[int]
            .physical_error_rates: list[float]
            .logical_error_rates:  NDArray[float64]  (shape: distances x rates)
            .shots_per_point:      int
```

---

## CSS Code Validation

The `ColorCode` class includes a runtime CSS validation check (`_validate_css`) that verifies:

1. Every plaquette has **even weight** (number of qubits)
2. Every pair of plaquettes has **even overlap** (number of shared qubits)

These two conditions guarantee that all X-type and Z-type stabilizers commute, which is the defining property of CSS codes. If either condition fails, the constructor raises `RuntimeError`.

---

## Testing Strategy

| Category | Location | What is tested |
|----------|----------|---------------|
| Core unit tests | `tests/test_core/` | Types, circuit builder, noise channel, registry |
| Noise unit tests | `tests/test_noise/` | Each error model: shape, statistics (10k samples, 3-sigma), Kraus validation |
| Code unit tests | `tests/test_codes/` | Stabilizer commutation, check matrix shape, syndrome computation, logical operators |
| Decoder unit tests | `tests/test_decoders/` | Known-answer tests on small codes |
| Simulation tests | `tests/test_simulation/` | Deterministic seeding, result shapes, frame propagation rules |
| Viz smoke tests | `tests/test_viz/` | Figure creation and cleanup without rendering |
| Integration tests | `tests/test_integration/` | End-to-end pipelines: code + noise + decoder + result check |

All 194 tests run in under 1 second. Statistical noise model tests use 10,000 samples and verify frequencies within 3-sigma tolerance.

---

## Next Steps

- [Extending QENS](extending.md) -- How to add custom components
- [API Reference](api-reference.md) -- Complete signature reference
- [Contributing](../CONTRIBUTING.md) -- Development workflow
