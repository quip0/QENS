<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# API Reference

Complete API reference for the QENS SDK, organized by module.

---

## qens (Top-Level Exports)

The top-level `qens` package re-exports the most commonly used names for convenience:

**Types:** `PauliOp`, `Outcome`, `PauliString`, `Syndrome`, `Coordinate`

**Circuit:** `Circuit`, `Gate`, `Moment`

**Codes:** `QECCode`, `RepetitionCode`, `SurfaceCode`, `ColorCode`

**Noise:** `ErrorModel`, `BitFlipError`, `PhaseFlipError`, `DepolarizingError`, `PauliYError`, `MeasurementError`, `CoherentRotationError`, `CrosstalkError`, `CorrelatedPauliError`, `LeakageError`, `ComposedNoiseModel`

**Decoders:** `Decoder`, `DecoderResult`, `LookupTableDecoder`, `MWPMDecoder`, `UnionFindDecoder`

**Simulation:** `ThresholdExperiment`, `NoisySampler`, `SimulationResult`, `ThresholdResult`, `PauliFrameSimulator`

**Visualization:** `draw_circuit`, `draw_lattice`, `draw_decoding_graph`, `plot_threshold`, `plot_logical_rates`, `plot_histogram`

---

## qens.core.types

Low-level type definitions used throughout the SDK.

#### `PauliOp`

Enum representing single-qubit Pauli operators.

**Members:**
- `PauliOp.I` -- Identity
- `PauliOp.X` -- Pauli X (bit flip)
- `PauliOp.Y` -- Pauli Y
- `PauliOp.Z` -- Pauli Z (phase flip)

#### `Outcome`

Enum representing measurement outcomes.

**Members:**
- `Outcome.ZERO` -- Measured |0>
- `Outcome.ONE` -- Measured |1>

#### `PauliString`

```python
PauliString = tuple[PauliOp, ...]
```

An ordered tuple of Pauli operators, one per qubit.

#### `Syndrome`

```python
Syndrome = tuple[int, ...]
```

A tuple of integers (0 or 1) representing stabilizer measurement outcomes.

#### `KrausMatrix`

```python
KrausMatrix = np.ndarray
```

A 2D complex NumPy array representing a single Kraus operator.

#### `QubitIndex`

```python
QubitIndex = int
```

Non-negative integer identifying a qubit in a circuit or code.

#### `Coordinate`

```python
Coordinate = tuple[float, float]
```

A 2D coordinate pair used for qubit layout and visualization.

---

## qens.core.circuit

Circuit construction with a fluent API.

#### `Gate(name: str, qubits: tuple[int, ...], params: dict[str, float] | None = None)`

Represents a single quantum gate operation.

**Properties:**
- `name: str` -- Gate name (e.g., "H", "CX", "M")
- `qubits: tuple[int, ...]` -- Qubit indices this gate acts on
- `params: dict[str, float] | None` -- Optional gate parameters (e.g., rotation angles)

**Methods:**
- `is_measurement() -> bool` -- True if this is a measurement gate
- `is_two_qubit() -> bool` -- True if the gate acts on two or more qubits

#### `Moment(gates: list[Gate])`

A collection of gates that can be executed in parallel (no overlapping qubits).

**Properties:**
- `gates: list[Gate]` -- The gates in this moment
- `qubits_used: set[int]` -- All qubit indices involved in this moment

**Methods:**
- `add_gate(gate: Gate) -> None` -- Add a gate; raises ValueError on qubit conflict
- `has_measurements() -> bool` -- True if any gate in the moment is a measurement

#### `Circuit(num_qubits: int)`

Builder for quantum circuits. All gate methods return `self` for chaining.

**Properties:**
- `num_qubits: int` -- Number of qubits in the circuit
- `moments: list[Moment]` -- Ordered list of moments
- `depth: int` -- Number of moments in the circuit

**Methods:**
- `h(qubit: int) -> Circuit` -- Append Hadamard gate
- `x(qubit: int) -> Circuit` -- Append Pauli-X gate
- `z(qubit: int) -> Circuit` -- Append Pauli-Z gate
- `cx(control: int, target: int) -> Circuit` -- Append CNOT gate
- `cz(control: int, target: int) -> Circuit` -- Append CZ gate
- `measure(qubit: int) -> Circuit` -- Append measurement
- `reset(qubit: int) -> Circuit` -- Append qubit reset
- `barrier() -> Circuit` -- Insert a barrier (new moment boundary)
- `append_gate(gate: Gate) -> Circuit` -- Append an arbitrary gate
- `append_moment(moment: Moment) -> Circuit` -- Append a full moment
- `__add__(other: Circuit) -> Circuit` -- Concatenate two circuits
- `__len__() -> int` -- Number of moments

---

## qens.core.noise_channel

Kraus-operator representation of a quantum noise channel.

#### `NoiseChannel(kraus_ops: list[KrausMatrix])`

Represents a completely positive trace-preserving (CPTP) map.

**Properties:**
- `kraus_ops: list[KrausMatrix]` -- List of Kraus operator matrices
- `num_kraus: int` -- Number of Kraus operators

**Methods:**
- `validate() -> bool` -- Check that Kraus operators sum to identity (CPTP condition)
- `probabilities() -> list[float]` -- Return the probability of each Kraus branch (trace of K^dag K)
- `sample(rng: np.random.Generator) -> int` -- Sample a Kraus branch index according to probabilities

---

## qens.core.registry

Generic plugin registry.

#### `Registry[T]()`

A typed dictionary mapping string names to classes.

**Methods:**
- `register(name: str, cls: type[T]) -> None` -- Register a class. Raises `ValueError` on duplicate name.
- `get(name: str) -> type[T]` -- Retrieve a class by name. Raises `KeyError` if not found.
- `list_registered() -> list[str]` -- Return all registered names.
- `__contains__(name: str) -> bool` -- Check if a name is registered.

---

## qens.core.qubit

Qubit metadata.

#### `QubitRole`

Enum for qubit roles in a QEC code.

**Members:**
- `QubitRole.DATA` -- Data qubit
- `QubitRole.ANCILLA` -- Ancilla (syndrome measurement) qubit

#### `Qubit(index: int, role: QubitRole, coordinate: Coordinate | None = None)`

Dataclass representing a qubit with metadata.

**Fields:**
- `index: int` -- Qubit index in the circuit
- `role: QubitRole` -- Whether this is a data or ancilla qubit
- `coordinate: Coordinate | None` -- Optional 2D position for visualization

---

## qens.noise

Error models for simulating quantum noise.

#### `ErrorModel` (abstract)

Base class for all error models.

**Abstract Methods:**
- `sample_errors(num_qubits: int, affected_qubits: list[int], rng: np.random.Generator) -> PauliString` -- Generate a random Pauli error

**Optional Methods:**
- `to_channel() -> NoiseChannel` -- Convert to Kraus representation
- `applies_to(gate: Gate) -> bool` -- Whether this model applies to a given gate (default: True)

**Dunder Methods:**
- `__repr__() -> str` -- Human-readable representation

#### `BitFlipError(p: float)`

Applies X with probability `p` independently to each affected qubit.

**Parameters:**
- `p: float` -- Bit-flip probability per qubit (0 <= p <= 1)

#### `PhaseFlipError(p: float)`

Applies Z with probability `p` independently to each affected qubit.

**Parameters:**
- `p: float` -- Phase-flip probability per qubit (0 <= p <= 1)

#### `DepolarizingError(p: float)`

Applies X, Y, or Z each with probability `p/3` independently to each affected qubit.

**Parameters:**
- `p: float` -- Total depolarizing probability per qubit (0 <= p <= 1)

#### `PauliYError(p: float)`

Applies Y with probability `p` independently to each affected qubit.

**Parameters:**
- `p: float` -- Y-error probability per qubit (0 <= p <= 1)

#### `MeasurementError(p0: float, p1: float | None = None)`

Flips measurement outcomes asymmetrically.

**Parameters:**
- `p0: float` -- Probability of flipping a 0 outcome to 1
- `p1: float | None` -- Probability of flipping a 1 outcome to 0 (defaults to `p0` if None)

#### `CoherentRotationError(angle: float, axis: str = "Z")`

Applies a small coherent rotation about a Pauli axis, modeled as a probabilistic Pauli error.

**Parameters:**
- `angle: float` -- Rotation angle in radians
- `axis: str` -- Rotation axis: "X", "Y", or "Z"

#### `CrosstalkError(p: float, qubit_pairs: list[tuple[int, int]])`

Applies correlated errors on specified qubit pairs when either is involved in a gate.

**Parameters:**
- `p: float` -- Crosstalk probability
- `qubit_pairs: list[tuple[int, int]]` -- Pairs of qubits subject to crosstalk

#### `CorrelatedPauliError(p: float, pauli_string: PauliString)`

Applies a fixed multi-qubit Pauli error with probability `p`.

**Parameters:**
- `p: float` -- Probability of the correlated error occurring
- `pauli_string: PauliString` -- The multi-qubit Pauli operator to apply

#### `LeakageError(p_leak: float, p_return: float = 0.0)`

Models qubit leakage to non-computational states with stateful tracking.

**Parameters:**
- `p_leak: float` -- Probability of leaking out of the computational subspace
- `p_return: float` -- Probability of returning from a leaked state per round

#### `ComposedNoiseModel(models: list[ErrorModel])`

Stacks multiple error models, applying each in sequence.

**Parameters:**
- `models: list[ErrorModel]` -- Ordered list of error models to compose

**Methods:**
- `sample_errors(num_qubits: int, affected_qubits: list[int], rng: np.random.Generator) -> PauliString` -- Apply all models and multiply the resulting Pauli strings

#### `noise_registry: Registry[ErrorModel]`

Module-level registry for error models. See the Registry API for usage.

---

## qens.codes

Quantum error-correcting codes.

#### `Stabilizer(name: str, pauli_string: PauliString)`

Dataclass representing a stabilizer generator.

**Fields:**
- `name: str` -- Human-readable stabilizer name (e.g., "S0")
- `pauli_string: PauliString` -- The Pauli operator for this stabilizer

#### `LogicalOperator(name: str, pauli_string: PauliString)`

Dataclass representing a logical operator of the code.

**Fields:**
- `name: str` -- Logical operator name (e.g., "X_L", "Z_L")
- `pauli_string: PauliString` -- The Pauli operator

#### `Lattice(nodes: list[LatticeNode], edges: list[LatticeEdge])`

Graph structure representing the code's qubit layout.

**Properties:**
- `nodes: list[LatticeNode]` -- All nodes in the lattice
- `edges: list[LatticeEdge]` -- All edges in the lattice

#### `LatticeNode(index: int, coordinate: Coordinate, role: QubitRole)`

Dataclass for a node in a code lattice.

**Fields:**
- `index: int` -- Node index
- `coordinate: Coordinate` -- 2D position
- `role: QubitRole` -- Data or ancilla

#### `LatticeEdge(source: int, target: int, weight: float = 1.0)`

Dataclass for an edge in a code lattice.

**Fields:**
- `source: int` -- Source node index
- `target: int` -- Target node index
- `weight: float` -- Edge weight (default 1.0)

#### `QECCode` (abstract)

Base class for quantum error-correcting codes.

**Abstract Properties:**
- `name: str` -- Code name
- `num_data_qubits: int` -- Number of data qubits
- `num_ancilla_qubits: int` -- Number of ancilla qubits
- `code_distance: int` -- Code distance

**Computed Properties:**
- `num_qubits: int` -- Total qubits (data + ancilla)

**Abstract Methods:**
- `stabilizer_generators() -> list[Stabilizer]` -- Return the stabilizer generators
- `logical_operators() -> list[LogicalOperator]` -- Return the logical operators
- `check_matrix() -> np.ndarray` -- Return the parity check matrix (GF(2))
- `syndrome_circuit(rounds: int = 1) -> Circuit` -- Build the syndrome extraction circuit
- `qubit_coordinates() -> dict[int, Coordinate]` -- Return 2D positions for all qubits

**Provided Methods:**
- `compute_syndrome(error: PauliString) -> Syndrome` -- Compute the syndrome for a given error
- `is_logical_error(correction: PauliString) -> bool` -- Check if a correction results in a logical error

#### `RepetitionCode(distance: int)`

1D repetition code for bit-flip errors.

**Parameters:**
- `distance: int` -- Code distance (>= 2)

#### `SurfaceCode(distance: int)`

Rotated surface code.

**Parameters:**
- `distance: int` -- Code distance (odd, >= 3)

#### `ColorCode(distance: int, lattice_type: str = "4.8.8")`

Color code on a 2D lattice.

**Parameters:**
- `distance: int` -- Code distance (odd, >= 3)
- `lattice_type: str` -- Lattice geometry: `"4.8.8"` or `"6.6.6"`

#### `code_registry: Registry[QECCode]`

Module-level registry for QEC codes.

---

## qens.decoders

Decoding algorithms for QEC.

#### `DecoderResult(correction: PauliString, confidence: float = 1.0)`

Dataclass returned by all decoders.

**Fields:**
- `correction: PauliString` -- The inferred Pauli correction to apply
- `confidence: float` -- Decoder confidence (0.0 to 1.0)

#### `Decoder` (abstract)

Base class for decoders.

**Constructor:**
- `Decoder(code: QECCode)` -- Initialize with the code to decode

**Properties:**
- `code: QECCode` -- The associated QEC code

**Abstract Methods:**
- `decode(syndrome: Syndrome) -> DecoderResult` -- Decode a syndrome into a correction

**Optional Methods:**
- `precompute() -> None` -- Perform any precomputation (e.g., build lookup tables)
- `build_decoding_graph() -> Lattice` -- Build a graph for visualization

#### `LookupTableDecoder(code: QECCode)`

Exhaustive lookup table decoder. Enumerates all single-qubit errors and caches the syndrome-to-correction map. Optimal for small codes.

**Methods:**
- `decode(syndrome: Syndrome) -> DecoderResult` -- Exact lookup decoding
- `precompute() -> None` -- Build the lookup table (called automatically on first decode)

#### `MWPMDecoder(code: QECCode)`

Greedy minimum-weight perfect matching decoder.

**Methods:**
- `decode(syndrome: Syndrome) -> DecoderResult` -- MWPM-based decoding
- `build_decoding_graph() -> Lattice` -- Return the decoding graph with edge weights

#### `UnionFindDecoder(code: QECCode)`

Almost-linear-time decoder using the union-find data structure.

**Methods:**
- `decode(syndrome: Syndrome) -> DecoderResult` -- Union-find decoding
- `build_decoding_graph() -> Lattice` -- Return the decoding graph

#### `decoder_registry: Registry[Decoder]`

Module-level registry for decoders.

---

## qens.simulation

Simulation engines and experiment runners.

#### `SimulationResult(num_shots: int, num_errors: int, logical_error_rate: float, raw_syndromes: list[Syndrome] | None = None)`

Dataclass holding the outcome of a simulation run.

**Fields:**
- `num_shots: int` -- Number of Monte Carlo shots
- `num_errors: int` -- Number of detected logical errors
- `logical_error_rate: float` -- Fraction of shots that resulted in a logical error
- `raw_syndromes: list[Syndrome] | None` -- Optional list of raw syndrome measurements

#### `ThresholdResult(physical_rates: list[float], logical_rates: dict[int, list[float]], threshold_estimate: float | None)`

Dataclass holding the outcome of a threshold experiment.

**Fields:**
- `physical_rates: list[float]` -- Physical error rates swept
- `logical_rates: dict[int, list[float]]` -- Logical error rates keyed by code distance
- `threshold_estimate: float | None` -- Estimated threshold value (None if curves do not cross)

#### `NoisySampler(code: QECCode, noise_model: ErrorModel, decoder: Decoder, seed: int | None = None)`

Monte Carlo sampler that injects errors, measures syndromes, decodes, and checks for logical errors.

**Parameters:**
- `code: QECCode` -- The QEC code
- `noise_model: ErrorModel` -- The error model to sample from
- `decoder: Decoder` -- The decoder to use
- `seed: int | None` -- Optional RNG seed for reproducibility

**Methods:**
- `run(num_shots: int) -> SimulationResult` -- Run `num_shots` Monte Carlo trials

#### `ThresholdExperiment(code_class: type[QECCode], distances: list[int], physical_rates: list[float], noise_model_class: type[ErrorModel], decoder_class: type[Decoder], num_shots: int = 10000, seed: int | None = None)`

Sweeps physical error rates across multiple code distances to estimate the error-correction threshold.

**Parameters:**
- `code_class: type[QECCode]` -- Code class to instantiate at each distance
- `distances: list[int]` -- List of code distances to test
- `physical_rates: list[float]` -- Physical error rates to sweep
- `noise_model_class: type[ErrorModel]` -- Error model class (instantiated with each rate)
- `decoder_class: type[Decoder]` -- Decoder class
- `num_shots: int` -- Shots per (distance, rate) pair
- `seed: int | None` -- Optional RNG seed

**Methods:**
- `run() -> ThresholdResult` -- Execute the full sweep and return results

#### `PauliFrameSimulator(circuit: Circuit, noise_model: ErrorModel | None = None, seed: int | None = None)`

Efficient Clifford circuit simulator using the Pauli frame formalism.

**Parameters:**
- `circuit: Circuit` -- The circuit to simulate
- `noise_model: ErrorModel | None` -- Optional noise model
- `seed: int | None` -- Optional RNG seed

**Methods:**
- `run(num_shots: int) -> list[PauliString]` -- Simulate the circuit and return the final Pauli frame for each shot

---

## qens.viz

Visualization functions and infrastructure.

#### `FigureHandle(fig: matplotlib.figure.Figure, axes: matplotlib.axes.Axes | list[matplotlib.axes.Axes])`

Wrapper around matplotlib figure objects returned by all visualization functions.

**Fields:**
- `fig: Figure` -- The matplotlib Figure
- `axes: Axes | list[Axes]` -- The axes (single or list)

#### `QENSStyle`

Configurable color palette and sizing for all QENS visualizations. Frozen dataclass.

**Key fields:**
- `data_qubit_color: str` -- Fill color for data qubits (`"#4A90D9"`)
- `ancilla_x_color: str` -- Fill color for X-type ancilla markers (`"#E74C3C"`)
- `ancilla_z_color: str` -- Fill color for Z-type ancilla markers (`"#2ECC71"`)
- `error_x_color / error_y_color / error_z_color: str` -- Colors for X, Y, Z errors
- `syndrome_active: str` -- Color for active syndrome bits (`"#E74C3C"`)
- `color_code_plaquette_colors: tuple[str, str, str]` -- 3-color palette for color codes (`("tomato", "yellowgreen", "steelblue")`)
- `background_color: str` -- Figure background (`"#FFFFFF"`)
- `text_color: str` -- Text label color (`"#2C3E50"`)

See the [Visualization Guide](visualization.md#customizing-style) for the full field list.

#### `draw_circuit(circuit: Circuit, errors: PauliString | None = None, style: QENSStyle | None = None, **kwargs) -> FigureHandle`

Draw a quantum circuit diagram with optional error annotations.

**Parameters:**
- `circuit: Circuit` -- The circuit to draw
- `errors: PauliString | None` -- Optional error overlay
- `style: QENSStyle | None` -- Optional style override
- `**kwargs` -- Passed to matplotlib (e.g., `figsize`)

#### `draw_lattice(code: QECCode, syndrome: Syndrome | None = None, errors: PauliString | None = None, style: QENSStyle | None = None, **kwargs) -> FigureHandle`

Draw the code lattice with optional syndrome and error overlays.

**Parameters:**
- `code: QECCode` -- The code whose lattice to draw
- `syndrome: Syndrome | None` -- Optional syndrome to highlight
- `errors: PauliString | None` -- Optional errors to highlight
- `style: QENSStyle | None` -- Optional style override
- `**kwargs` -- Passed to matplotlib

#### `draw_decoding_graph(decoder: Decoder, syndrome: Syndrome | None = None, matching: list[tuple[int, int]] | None = None, style: QENSStyle | None = None, **kwargs) -> FigureHandle`

Draw the decoding graph with optional matching edges.

**Parameters:**
- `decoder: Decoder` -- The decoder (must support `build_decoding_graph()`)
- `syndrome: Syndrome | None` -- Optional syndrome to highlight
- `matching: list[tuple[int, int]] | None` -- Optional matched pairs to draw
- `style: QENSStyle | None` -- Optional style override
- `**kwargs` -- Passed to matplotlib

#### `plot_threshold(result: ThresholdResult, style: QENSStyle | None = None, **kwargs) -> FigureHandle`

Plot logical error rate vs. physical error rate for multiple code distances (standard QEC threshold plot).

**Parameters:**
- `result: ThresholdResult` -- Threshold experiment results
- `style: QENSStyle | None` -- Optional style override
- `**kwargs` -- Passed to matplotlib

#### `plot_logical_rates(results: dict[str, float], style: QENSStyle | None = None, **kwargs) -> FigureHandle`

Bar chart of logical error rates.

**Parameters:**
- `results: dict[str, float]` -- Mapping of labels to logical error rates
- `style: QENSStyle | None` -- Optional style override
- `**kwargs` -- Passed to matplotlib

#### `plot_histogram(data: list[float] | np.ndarray, bins: int = 50, style: QENSStyle | None = None, **kwargs) -> FigureHandle`

General-purpose histogram plot.

**Parameters:**
- `data: list[float] | np.ndarray` -- Data to plot
- `bins: int` -- Number of bins
- `style: QENSStyle | None` -- Optional style override
- `**kwargs` -- Passed to matplotlib

#### `get_style() -> QENSStyle`

Return the current default style instance.

#### `viz_registry: Registry[Visualizer]`

Module-level registry for visualizers.

---

## qens.utils

Utility functions for Pauli algebra and linear algebra over GF(2).

#### `get_rng(seed: int | None = None) -> np.random.Generator`

Create a seeded NumPy random generator. If `seed` is None, uses system entropy.

#### `pauli_multiply(a: PauliOp, b: PauliOp) -> PauliOp`

Multiply two single-qubit Pauli operators (ignoring phase).

#### `pauli_commutes(a: PauliOp, b: PauliOp) -> bool`

Check whether two single-qubit Pauli operators commute.

#### `pauli_string_multiply(a: PauliString, b: PauliString) -> PauliString`

Element-wise multiply two Pauli strings (ignoring global phase).

#### `symplectic_inner_product(a: PauliString, b: PauliString) -> int`

Compute the symplectic inner product of two Pauli strings. Returns 0 if they commute, 1 if they anticommute.

#### `GF2Matrix(data: np.ndarray)`

Sparse matrix over GF(2) with row reduction and kernel computation.

**Parameters:**
- `data: np.ndarray` -- 2D array of 0s and 1s (dtype uint8)

**Methods:**
- `row_reduce() -> GF2Matrix` -- Return the row-echelon form
- `kernel() -> list[np.ndarray]` -- Compute the null space over GF(2)
- `rank() -> int` -- Return the matrix rank over GF(2)
- `__matmul__(other: np.ndarray) -> np.ndarray` -- Matrix multiplication mod 2
