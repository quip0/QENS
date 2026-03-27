<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Simulation Guide

This guide covers the simulation infrastructure in QENS: the `NoisySampler`
for Monte Carlo error sampling, the `PauliFrameSimulator` for efficient
error propagation through Clifford circuits, and the `ThresholdExperiment`
for automated threshold sweeps.

---

## Overview

| Component | Purpose |
|---|---|
| `NoisySampler` | Monte Carlo engine: sample errors, compute syndromes, optionally decode. |
| `PauliFrameSimulator` | Track Pauli error propagation through Clifford circuits in O(n) per gate. |
| `ThresholdExperiment` | High-level sweep over multiple code distances and error rates. |
| `SimulationResult` | Data container for sampling outcomes. |
| `ThresholdResult` | Data container for threshold sweep outcomes. |

---

## Single-Point Simulation

There are two ways to run a single simulation point (one code, one noise
level, one decoder).

### Approach 1: ThresholdExperiment.single_point

The `single_point` static method is a convenience wrapper that creates a
sampler, calls `precompute()` on the decoder, and runs the simulation.

```python
from qens.codes.repetition import RepetitionCode
from qens.decoders.lookup import LookupTableDecoder
from qens.noise.pauli import BitFlipError
from qens.simulation.experiment import ThresholdExperiment

code = RepetitionCode(distance=5)
noise = BitFlipError(p=0.05)
decoder = LookupTableDecoder(code)

result = ThresholdExperiment.single_point(
    code=code,
    noise_model=noise,
    decoder=decoder,
    shots=10_000,
    seed=42,
)

print(result)
# SimulationResult(shots=10000, logical_error_rate=0.XXXX)

print(f"Logical error rate: {result.logical_error_rate:.4f}")
print(f"Logical errors: {result.logical_error_count} / {result.num_shots}")
```

### Approach 2: NoisySampler Direct

`NoisySampler` gives you more control. You create the sampler, then call
`run()` with your code, noise model, decoder, and shot count.

```python
from qens.codes.surface import SurfaceCode
from qens.decoders.mwpm import MWPMDecoder
from qens.noise.pauli import DepolarizingError
from qens.simulation.sampler import NoisySampler

code = SurfaceCode(distance=3)
noise = DepolarizingError(p=0.01)
decoder = MWPMDecoder(code)
decoder.precompute()

sampler = NoisySampler(seed=42)
result = sampler.run(code, noise, decoder, shots=5_000)

print(f"Shots: {result.num_shots}")
print(f"Logical error rate: {result.logical_error_rate:.4f}")
print(f"Logical error count: {result.logical_error_count}")
```

### SimulationResult Properties

The `SimulationResult` object provides access to all per-shot data:

| Property / Method | Description |
|---|---|
| `num_shots` | Total number of simulation shots. |
| `logical_error_rate` | Fraction of shots resulting in a logical error. |
| `logical_error_count` | Number of shots with a logical error. |
| `sample_syndrome(i)` | Syndrome array for shot `i`. |
| `sample_error(i)` | Error PauliString for shot `i`. |
| `syndromes` | List of all syndrome arrays. |
| `errors` | List of all error PauliStrings. |
| `corrections` | List of all correction PauliStrings (empty if no decoder). |
| `logical_errors` | List of booleans (empty if no decoder). |

```python
# Inspect individual shots
for i in range(min(5, result.num_shots)):
    syndrome = result.sample_syndrome(i)
    error = result.sample_error(i)
    print(f"Shot {i}: syndrome={syndrome}, error={error}")
```

---

## Sampling Without Decoding

Use `NoisySampler.sample_errors()` to sample errors and compute syndromes
without running a decoder. This is useful for:

- Collecting syndrome statistics.
- Building custom decoding pipelines.
- Feeding data to visualization tools.

```python
from qens.codes.surface import SurfaceCode
from qens.noise.pauli import DepolarizingError
from qens.simulation.sampler import NoisySampler
import numpy as np

code = SurfaceCode(distance=3)
noise = DepolarizingError(p=0.05)

sampler = NoisySampler(seed=42)
result = sampler.sample_errors(code, noise, shots=1_000)

print(f"Shots: {result.num_shots}")
print(f"Logical error rate: {result.logical_error_rate}")
# 0.0 (no decoder was used, so no logical errors are tracked)

# Analyze syndrome statistics
syndrome_weights = [int(np.sum(result.sample_syndrome(i))) for i in range(result.num_shots)]
print(f"Mean syndrome weight: {np.mean(syndrome_weights):.2f}")
print(f"Max syndrome weight: {max(syndrome_weights)}")

# Analyze error weights
error_weights = [int(np.sum(result.sample_error(i) > 0)) for i in range(result.num_shots)]
print(f"Mean error weight: {np.mean(error_weights):.2f}")
```

---

## Threshold Sweep

The `ThresholdExperiment` automates the standard QEC workflow: for each
combination of code distance and physical error rate, run many shots and
record the logical error rate.

### Constructor Parameters

| Parameter | Type | Description |
|---|---|---|
| `code_class` | `type[QECCode]` | The code class to instantiate (e.g., `SurfaceCode`). |
| `distances` | `list[int]` | List of code distances to test. |
| `physical_error_rates` | `list[float]` | List of physical error rates to sweep. |
| `noise_model_factory` | `Callable[[float], ErrorModel]` | Factory that creates a noise model from a physical error rate. |
| `decoder_class` | `type[Decoder]` | The decoder class to instantiate. |
| `shots_per_point` | `int` | Number of Monte Carlo shots per (distance, rate) pair. Default: 10,000. |
| `seed` | `int or None` | Random seed for reproducibility. |

### Running the Sweep

```python
from qens.codes.surface import SurfaceCode
from qens.decoders.mwpm import MWPMDecoder
from qens.noise.pauli import DepolarizingError
from qens.simulation.experiment import ThresholdExperiment

experiment = ThresholdExperiment(
    code_class=SurfaceCode,
    distances=[3, 5, 7],
    physical_error_rates=[0.001, 0.005, 0.01, 0.02, 0.05],
    noise_model_factory=lambda p: DepolarizingError(p=p),
    decoder_class=MWPMDecoder,
    shots_per_point=1_000,
    seed=42,
)

# Optional progress callback
def on_progress(completed, total):
    print(f"  Progress: {completed}/{total} ({100*completed/total:.0f}%)")

result = experiment.run(progress_callback=on_progress)
print(result)
# ThresholdResult(distances=[3, 5, 7], p_range=[0.0010, 0.0500], shots=1000)
```

### ThresholdResult

The `ThresholdResult` object contains:

| Field | Type | Description |
|---|---|---|
| `distances` | `list[int]` | Code distances tested. |
| `physical_error_rates` | `list[float]` | Physical error rates tested. |
| `logical_error_rates` | `np.ndarray` | 2D array of shape `(len(distances), len(physical_error_rates))`. |
| `shots_per_point` | `int` | Shots per data point. |

```python
import numpy as np

# Access the results matrix
print(f"Shape: {result.logical_error_rates.shape}")
# (3, 5)

# Print results table
print(f"{'p':>8s}", end="")
for d in result.distances:
    print(f"  d={d:>2d}", end="")
print()

for j, p in enumerate(result.physical_error_rates):
    print(f"{p:>8.4f}", end="")
    for i in range(len(result.distances)):
        print(f"  {result.logical_error_rates[i, j]:>.4f}", end="")
    print()
```

Example output:

```
       p  d= 3  d= 5  d= 7
  0.0010  0.000  0.000  0.000
  0.0050  0.005  0.002  0.000
  0.0100  0.025  0.010  0.004
  0.0200  0.075  0.045  0.030
  0.0500  0.200  0.180  0.170
```

Lines for different distances should cross at the threshold error rate.

---

## Pauli Frame Simulator

The `PauliFrameSimulator` efficiently tracks how Pauli errors propagate
through Clifford gates. Instead of simulating full quantum states (which
requires O(2^n) memory), it tracks only a Pauli frame -- an array of Pauli
operators, one per qubit -- which is O(n) in both space and time per gate.

```python
from qens.simulation.frame import PauliFrameSimulator
```

### API

| Method / Property | Description |
|---|---|
| `PauliFrameSimulator(num_qubits)` | Create a simulator with an identity frame. |
| `apply_error(error)` | Compose a PauliString error onto the current frame. |
| `propagate_gate(gate)` | Update the frame through one Clifford gate. |
| `propagate_circuit(circuit)` | Propagate through an entire circuit. |
| `measure(qubit)` | Returns 1 if X or Y error on qubit (bit flip), 0 otherwise. |
| `frame` | Read-only copy of the current Pauli frame. |
| `reset()` | Clear the frame to all-identity. |

### Gate Propagation Rules

The simulator implements Clifford conjugation rules:

- **H:** X becomes Z, Z becomes X, Y stays Y (up to phase).
- **CX (CNOT):** X on control propagates to target. Z on target propagates
  back to control.
- **CZ:** X on either qubit adds Z to the other qubit.
- **X, Z, M, R:** Do not change the Pauli frame.

### Example: Error Propagation

```python
import numpy as np
from qens.simulation.frame import PauliFrameSimulator
from qens.core.types import PauliOp
from qens.core.circuit import Gate

sim = PauliFrameSimulator(num_qubits=3)

# Apply an X error on qubit 0
error = np.zeros(3, dtype=np.uint8)
error[0] = PauliOp.X
sim.apply_error(error)
print(f"After X error on q0: {sim.frame}")
# [1 0 0]

# Propagate through a CNOT (control=0, target=1)
sim.propagate_gate(Gate("CX", (0, 1)))
print(f"After CX(0,1): {sim.frame}")
# [1 1 0]  -- X error on control propagated to target

# Propagate through a Hadamard on qubit 0
sim.propagate_gate(Gate("H", (0,)))
print(f"After H(0): {sim.frame}")
# [3 1 0]  -- X on qubit 0 became Z

# Measure qubit 1
outcome = sim.measure(1)
print(f"Measurement of qubit 1: {outcome}")
# 1 (bit flip detected because of X error)

# Reset and start fresh
sim.reset()
print(f"After reset: {sim.frame}")
# [0 0 0]
```

### Propagating Through a Full Circuit

```python
import numpy as np
from qens.simulation.frame import PauliFrameSimulator
from qens.core.circuit import Circuit
from qens.core.types import PauliOp

# Build a GHZ preparation circuit
circuit = Circuit(3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)

# Start with a Z error on qubit 0
sim = PauliFrameSimulator(num_qubits=3)
z_error = np.zeros(3, dtype=np.uint8)
z_error[0] = PauliOp.Z
sim.apply_error(z_error)

print(f"Before circuit: {sim.frame}")
# [3 0 0]

sim.propagate_circuit(circuit)
print(f"After circuit: {sim.frame}")
# The Z error has propagated through the circuit according to Clifford rules
```

---

## Reproducibility

All randomness in QENS flows through NumPy `Generator` objects. To get
reproducible results, pass a `seed` parameter:

```python
from qens.simulation.sampler import NoisySampler
from qens.codes.repetition import RepetitionCode
from qens.decoders.lookup import LookupTableDecoder
from qens.noise.pauli import BitFlipError

code = RepetitionCode(distance=3)
noise = BitFlipError(p=0.1)
decoder = LookupTableDecoder(code)

# Same seed produces identical results
result1 = NoisySampler(seed=123).run(code, noise, decoder, shots=100)
result2 = NoisySampler(seed=123).run(code, noise, decoder, shots=100)

assert result1.logical_error_rate == result2.logical_error_rate
assert all(
    (e1 == e2).all()
    for e1, e2 in zip(result1.errors, result2.errors)
)
print("Results are identical with the same seed.")
```

The `ThresholdExperiment` also accepts a `seed` parameter for reproducible
sweeps.

---

## Performance Tips

1. **Pauli frame simulation is O(n) per gate.** This is the key efficiency
   win that allows QENS to simulate large codes. The frame simulator avoids
   exponential state vector simulation entirely.

2. **LookupTableDecoder is fastest for small codes.** After the one-time
   precomputation, each decode is O(1) (a hash table lookup). Use it for
   codes with distance 7 or below.

3. **For large threshold sweeps, use UnionFindDecoder.** Its near-linear time
   complexity makes it the best choice when running thousands of shots across
   many distance/error-rate combinations.

4. **Increase shots for low-noise regimes.** At very low physical error rates,
   logical errors are rare events. You need more Monte Carlo samples to
   observe enough logical errors for statistically meaningful error rates.
   A rule of thumb: aim for at least 100 logical error events per data point.

5. **Precompute decoders once, reuse across error rates.** In a threshold
   sweep, the decoding graph depends only on the code, not the noise model.
   `ThresholdExperiment` handles this automatically -- it creates one decoder
   per distance and reuses it across all error rates.

---

## Next Steps

- [Error Models](error-models.md) -- Noise models used by the sampler.
- [Codes](codes.md) -- QEC codes the simulator operates on.
- [Decoders](decoders.md) -- Decoders that process simulation syndromes.
- [Visualization](visualization.md) -- Plot threshold curves and simulation
  statistics.
