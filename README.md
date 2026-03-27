# QENS

**Quantum Error and Noise Simulation SDK** -- a Python-native toolkit for simulating quantum errors, decoding syndromes, and visualizing error-correcting codes.

QENS provides a layered API for researchers, educators, and engineers working with quantum error correction. It ships with built-in support for surface codes, repetition codes, and color codes, multiple decoder implementations, and publication-quality visualization -- all with only `numpy` and `matplotlib` as dependencies.

## Installation

```bash
pip install -e .
```

For development (includes pytest, mypy, ruff):

```bash
pip install -e ".[dev]"
```

Requires Python 3.11+.

---

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

---

## Detailed Usage Guide

### 1. Building Quantum Circuits

QENS provides a fluent builder API for constructing quantum circuits gate by gate:

```python
from qens import Circuit, Gate, Moment

# Fluent API -- chain gates together
circuit = Circuit(num_qubits=3).h(0).cx(0, 1).cx(0, 2).measure_all()
print(circuit)  # Circuit(num_qubits=3, depth=4)

# Or build manually with Gate and Moment objects
gate = Gate("H", qubits=(0,))
moment = Moment()
moment.add(gate)
circuit = Circuit(5)
circuit.append_moment(moment)
```

**Available fluent gates:** `h(q)`, `x(q)`, `z(q)`, `cx(ctrl, tgt)`, `cz(q0, q1)`, `measure(q)`, `measure_all()`, `reset(q)`.

**Circuit properties:** `num_qubits`, `depth`, `moments`.

---

### 2. Error Models

Every error model subclasses `ErrorModel` and implements `sample_errors()`. All models support Pauli-frame sampling and can be composed.

#### Pauli Errors

```python
from qens import BitFlipError, PhaseFlipError, DepolarizingError, PauliYError
import numpy as np

noise = DepolarizingError(p=0.01)  # X, Y, Z each with prob p/3

rng = np.random.default_rng(42)
error = noise.sample_errors(num_qubits=5, affected_qubits=[0, 1, 2, 3, 4], rng=rng)
# Returns a PauliString: array of 0=I, 1=X, 2=Y, 3=Z
```

#### Measurement Errors

```python
from qens import MeasurementError

# Asymmetric readout: different 0->1 and 1->0 flip rates
readout = MeasurementError(p_0to1=0.02, p_1to0=0.005)

# Only applies to measurement gates
readout.applies_to(Gate("M", (0,)))   # True
readout.applies_to(Gate("H", (0,)))   # False
```

#### Gate Errors

```python
from qens import CoherentRotationError, CrosstalkError

# Gaussian over/under-rotation on every non-measurement gate
rotation = CoherentRotationError(angle_stddev=0.01)

# ZZ crosstalk between specific qubit pairs
crosstalk = CrosstalkError(coupling_map={(0, 1): 0.002, (1, 2): 0.001})
```

#### Correlated and Leakage Errors

```python
from qens import CorrelatedPauliError, LeakageError
from qens.core.types import PauliOp

# Joint Pauli errors on qubit pairs
correlated = CorrelatedPauliError(joint_errors={
    (0, 1): [(0.01, PauliOp.X, PauliOp.X)],  # XX with prob 0.01
    (2, 3): [(0.005, PauliOp.Z, PauliOp.Z)],  # ZZ with prob 0.005
})

# Leakage to |2> state with relaxation back
leakage = LeakageError(p_leak=0.001, p_relax=0.1)
print(leakage.leaked_qubits)  # Track which qubits are leaked
leakage.reset()                # Clear leakage state
```

#### Composing Noise Models

Stack multiple error models into a single composed model. Each model's `applies_to()` filter is respected.

```python
from qens import ComposedNoiseModel, DepolarizingError, MeasurementError, CrosstalkError

noise = ComposedNoiseModel([
    DepolarizingError(p=0.001),
    MeasurementError(p_0to1=0.01, p_1to0=0.005),
    CrosstalkError(coupling_map={(0, 1): 0.002}),
])

# Sample errors for a specific gate (respects filters)
from qens import Gate
error = noise.sample_errors_for_gate(
    num_qubits=5, gate=Gate("CX", (0, 1)), rng=rng
)
```

#### Kraus Representations

Pauli error models provide Kraus operator representations for density-matrix simulation:

```python
channel = DepolarizingError(p=0.01).to_channel(affected_qubits=[0])
print(channel.validate())      # True (completeness relation holds)
print(channel.probabilities())  # [0.99, 0.0033, 0.0033, 0.0033]
```

---

### 3. Error-Correcting Codes

All codes subclass `QECCode` and provide stabilizers, logical operators, check matrices, and syndrome extraction circuits.

#### Repetition Code

```python
from qens import RepetitionCode

code = RepetitionCode(distance=5)
print(code.num_data_qubits)     # 5
print(code.num_ancilla_qubits)  # 4
print(code.code_distance)       # 5

# Stabilizer generators (ZZ on adjacent pairs)
for stab in code.stabilizer_generators():
    print(f"  {stab.stabilizer_type}: qubits {stab.qubits}")

# Parity check matrix
H = code.check_matrix()  # shape (4, 5)

# Syndrome extraction circuit
circuit = code.syndrome_circuit(rounds=3)
```

#### Surface Code

```python
from qens import SurfaceCode
import numpy as np

code = SurfaceCode(distance=3)  # Rotated surface code
print(code.num_data_qubits)     # 9
print(code.num_ancilla_qubits)  # 8

# Inject an X error and compute the syndrome
error = np.zeros(9, dtype=np.uint8)
error[4] = 1  # X on center qubit
syndrome = code.compute_syndrome(error)
print(f"Syndrome: {syndrome}")  # Non-trivial where Z-stabilizers detect X

# Check if an error is a logical error
residual = np.zeros(9, dtype=np.uint8)
residual[0] = 1; residual[3] = 1; residual[6] = 1  # X on left column = X_L
print(code.is_logical_error(residual))  # True
```

#### Color Code

```python
from qens import ColorCode

# 4.8.8 lattice (default)
code_488 = ColorCode(distance=3, lattice_type="4.8.8")
print(code_488.supports_transversal_clifford)  # True

# 6.6.6 lattice
code_666 = ColorCode(distance=5, lattice_type="6.6.6")
```

#### Qubit Coordinates

Every code provides coordinates for visualization:

```python
coords = code.qubit_coordinates()
# {0: (0, 0), 1: (0, 1), ...} -- maps qubit index to (row, col)
```

---

### 4. Decoders

All decoders subclass `Decoder` and implement `decode(syndrome) -> DecoderResult`.

#### Lookup Table Decoder

Exact decoding via precomputed syndrome-to-correction table. Best for small codes (d <= 7).

```python
from qens import RepetitionCode, LookupTableDecoder
import numpy as np

code = RepetitionCode(5)
decoder = LookupTableDecoder(code)
decoder.precompute()  # Build lookup table

# Decode a syndrome
error = np.zeros(5, dtype=np.uint8)
error[2] = 1  # X error on qubit 2
syndrome = code.compute_syndrome(error)

result = decoder.decode(syndrome)
print(result.correction)  # Correction to apply
print(result.metadata)     # {"table_hit": True}
```

#### MWPM Decoder

Greedy minimum-weight perfect matching. Good balance of speed and accuracy.

```python
from qens import SurfaceCode, MWPMDecoder

code = SurfaceCode(5)
decoder = MWPMDecoder(code)
decoder.precompute()  # Build decoding graph

result = decoder.decode(syndrome)
print(result.metadata["matching"])  # List of matched defect pairs

# Access the decoding graph structure (for visualization)
graph = decoder.build_decoding_graph()
print(graph.keys())  # ['nodes', 'edges', 'boundary_nodes']
```

#### Union-Find Decoder

Fast approximate decoding with almost-linear time complexity.

```python
from qens import UnionFindDecoder

decoder = UnionFindDecoder(code)
decoder.precompute()
result = decoder.decode(syndrome)
```

---

### 5. Running Simulations

#### Single-Point Simulation

Run a fixed number of Monte Carlo shots at one noise level:

```python
from qens import (
    RepetitionCode, DepolarizingError, MWPMDecoder,
    ThresholdExperiment, NoisySampler,
)

code = RepetitionCode(5)
noise = DepolarizingError(p=0.05)
decoder = MWPMDecoder(code)

# Option A: via ThresholdExperiment convenience method
result = ThresholdExperiment.single_point(
    code=code, noise_model=noise, decoder=decoder,
    shots=10_000, seed=42
)
print(f"Logical error rate: {result.logical_error_rate:.4f}")
print(f"Logical errors: {result.logical_error_count} / {result.num_shots}")

# Option B: via NoisySampler directly
sampler = NoisySampler(seed=42)
result = sampler.run(code, noise, decoder, shots=10_000)

# Access individual shots
syn_0 = result.sample_syndrome(0)
err_0 = result.sample_error(0)
```

#### Sampling Without Decoding

Generate error samples and syndromes without the decoding step:

```python
sampler = NoisySampler(seed=42)
result = sampler.sample_errors(code, noise, shots=1_000)
# result.syndromes and result.errors are populated
# result.corrections and result.logical_errors are empty
```

#### Threshold Sweep

Sweep physical error rates across multiple code distances to find the error threshold:

```python
from qens import SurfaceCode, DepolarizingError, MWPMDecoder, ThresholdExperiment

experiment = ThresholdExperiment(
    code_class=SurfaceCode,
    distances=[3, 5, 7],
    physical_error_rates=[0.001, 0.003, 0.005, 0.008, 0.01, 0.015, 0.02],
    noise_model_factory=lambda p: DepolarizingError(p=p),
    decoder_class=MWPMDecoder,
    shots_per_point=10_000,
    seed=42,
)

# Run with progress tracking
def on_progress(completed, total):
    print(f"  [{completed}/{total}] {100*completed/total:.0f}%")

result = experiment.run(progress_callback=on_progress)

# Access results
print(result.distances)             # [3, 5, 7]
print(result.physical_error_rates)  # [0.001, ..., 0.02]
print(result.logical_error_rates)   # shape (3, 7) numpy array
```

#### Pauli Frame Simulator

Track Pauli errors through Clifford circuits efficiently (O(n) per gate):

```python
from qens.simulation import PauliFrameSimulator
from qens import Circuit, PauliOp
import numpy as np

sim = PauliFrameSimulator(num_qubits=3)

# Inject an X error on qubit 0
error = np.array([PauliOp.X, PauliOp.I, PauliOp.I], dtype=np.uint8)
sim.apply_error(error)

# Propagate through a circuit
circuit = Circuit(3).h(0).cx(0, 1)
sim.propagate_circuit(circuit)

print(sim.frame)      # See how the error propagated
print(sim.measure(0)) # 1 if X/Y error on qubit, else 0
```

---

### 6. Visualization

All visualization functions return a `FigureHandle` with `.save(path)`, `.show()`, and `.close()` methods. Use `matplotlib.use('Agg')` for headless environments.

#### Circuit Diagrams

```python
from qens import SurfaceCode, DepolarizingError, draw_circuit

code = SurfaceCode(3)
circuit = code.syndrome_circuit(rounds=1)
noise = DepolarizingError(p=0.01)

# Basic circuit diagram
fig = draw_circuit(circuit)
fig.save("circuit.png")

# With error annotations highlighting noise-prone gates
fig = draw_circuit(circuit, noise_model=noise, highlight_errors=True)
fig.save("noisy_circuit.png")

# With explicit error locations
fig = draw_circuit(circuit, error_locations=[(0, 2), (1, 5)])
fig.save("marked_circuit.png")
```

#### Lattice Views

```python
from qens import RepetitionCode, SurfaceCode, draw_lattice
import numpy as np

code = SurfaceCode(3)

# Basic lattice
fig = draw_lattice(code)

# With syndrome overlay
error = np.zeros(9, dtype=np.uint8)
error[4] = 1  # X error
syndrome = code.compute_syndrome(error)
fig = draw_lattice(code, syndrome=syndrome, error=error, title="X error on center")
fig.save("lattice_with_error.png")
```

#### Decoding Graphs

```python
from qens import SurfaceCode, MWPMDecoder, draw_decoding_graph
import numpy as np

code = SurfaceCode(3)
decoder = MWPMDecoder(code)
decoder.precompute()

error = np.zeros(9, dtype=np.uint8)
error[4] = 1
syndrome = code.compute_syndrome(error)
decode_result = decoder.decode(syndrome)

fig = draw_decoding_graph(
    decoder, syndrome=syndrome, decode_result=decode_result,
    show_matching=True, title="MWPM Decoding"
)
fig.save("decoding_graph.png")
```

#### Statistical Plots

```python
from qens import plot_threshold, plot_logical_rates, plot_histogram

# Threshold plot (from a ThresholdExperiment result)
fig = plot_threshold(result, log_scale=True, title="Surface Code Threshold")
fig.save("threshold.pdf")  # Publication-quality PDF

# Bar chart of logical error rates
fig = plot_logical_rates(
    distances=[3, 5, 7, 9],
    logical_rates=[0.05, 0.01, 0.002, 0.0004],
)
fig.save("rates_by_distance.png")

# Histogram of any simulation data
fig = plot_histogram(data, bins=50, xlabel="Error weight", title="Error Distribution")
fig.save("histogram.png")
```

---

### 7. Extending QENS

Every subsystem uses the **ABC + Registry** pattern. Extension points are marked with comments in the source.

#### Custom Error Model

```python
from qens.noise.base import ErrorModel
from qens.noise import noise_registry
import numpy as np

class ThermalRelaxationError(ErrorModel):
    def __init__(self, t1: float, t2: float, gate_time: float):
        self.p_x = 1 - np.exp(-gate_time / t1)
        self.p_z = 1 - np.exp(-gate_time / t2)

    def sample_errors(self, num_qubits, affected_qubits, rng):
        error = np.zeros(num_qubits, dtype=np.uint8)
        for q in affected_qubits:
            if rng.random() < self.p_x:
                error[q] = 1  # X
            elif rng.random() < self.p_z:
                error[q] = 3  # Z
        return error

    def __repr__(self):
        return f"ThermalRelaxationError(p_x={self.p_x:.4f}, p_z={self.p_z:.4f})"

noise_registry.register("thermal", ThermalRelaxationError)
```

#### Custom Decoder

```python
from qens.decoders.base import Decoder, DecoderResult
from qens.decoders import decoder_registry

class MyDecoder(Decoder):
    def decode(self, syndrome):
        correction = np.zeros(self._code.num_data_qubits, dtype=np.uint8)
        # ... your decoding logic ...
        return DecoderResult(correction=correction, success=True)

decoder_registry.register("my_decoder", MyDecoder)
```

#### Registry Lookup

```python
from qens.noise import noise_registry
from qens.codes import code_registry
from qens.decoders import decoder_registry

print(noise_registry.list_registered())
# ['bit_flip', 'coherent_rotation', 'correlated_pauli', 'crosstalk',
#  'depolarizing', 'leakage', 'measurement', 'pauli_y', 'phase_flip']

cls = noise_registry.get("depolarizing")
model = cls(p=0.01)
```

---

## Architecture

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

```bash
python3 examples/01_quickstart.py              # Basic workflow
python3 examples/02_surface_code_threshold.py   # Threshold sweep
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
