# Error Models Guide

This guide covers every noise model in the QENS SDK, from simple Pauli errors
to correlated multi-qubit noise and leakage. You will learn how to create,
sample, compose, and inspect error models for use in quantum error correction
simulations.

---

## Overview

All error models in QENS inherit from the abstract base class `ErrorModel`
(defined in `qens.noise.base`). The contract is straightforward:

| Method | Purpose |
|---|---|
| `sample_errors(num_qubits, affected_qubits, rng)` | Sample a `PauliString` representing the error on each qubit. Required. |
| `to_channel(affected_qubits)` | Return a `NoiseChannel` (Kraus representation). Optional. |
| `applies_to(gate)` | Return `True` if this model should fire after `gate`. Default: all gates. |

A `PauliString` is a NumPy `uint8` array of length `num_qubits`, where each
element is one of the `PauliOp` values: `I = 0`, `X = 1`, `Y = 2`, `Z = 3`.

```python
from qens.core.types import PauliOp

print(PauliOp.I, PauliOp.X, PauliOp.Y, PauliOp.Z)
# 0 1 2 3
```

---

## Pauli Errors

QENS ships four single-qubit Pauli error models. They all share the same
interface: construct with a probability `p`, then sample errors.

### BitFlipError

Applies a Pauli X (bit-flip) with probability `p` independently on each
affected qubit.

```python
import numpy as np
from qens.noise.pauli import BitFlipError

noise = BitFlipError(p=0.1)
rng = np.random.default_rng(42)

# Sample one error on a 5-qubit system, all qubits affected
error = noise.sample_errors(num_qubits=5, affected_qubits=[0, 1, 2, 3, 4], rng=rng)
print(error)
# Example output: [0 1 0 0 0]  (X error on qubit 1)
```

**Pauli applied:** X only.

### PhaseFlipError

Applies a Pauli Z (phase-flip) with probability `p` per qubit.

```python
from qens.noise.pauli import PhaseFlipError

noise = PhaseFlipError(p=0.05)
rng = np.random.default_rng(0)

error = noise.sample_errors(num_qubits=3, affected_qubits=[0, 1, 2], rng=rng)
print(error)
# Example output: [0 0 3]  (Z error on qubit 2)
```

**Pauli applied:** Z only.

### DepolarizingError

Applies X, Y, or Z each with probability `p/3` per qubit. With probability
`1 - p`, the qubit is left unchanged.

```python
from qens.noise.pauli import DepolarizingError

noise = DepolarizingError(p=0.03)
rng = np.random.default_rng(7)

error = noise.sample_errors(num_qubits=5, affected_qubits=[0, 1, 2, 3, 4], rng=rng)
print(error)
# Possible output: [0 0 1 0 0]  (X error on qubit 2)
```

**Paulis applied:** X, Y, and Z with equal probability (each `p/3`).

### PauliYError

Applies a Pauli Y error with probability `p` per qubit.

```python
from qens.noise.pauli import PauliYError

noise = PauliYError(p=0.02)
rng = np.random.default_rng(99)

error = noise.sample_errors(num_qubits=3, affected_qubits=[0, 1, 2], rng=rng)
print(error)
# Possible output: [0 2 0]  (Y error on qubit 1)
```

**Pauli applied:** Y only.

### Kraus Channel Examples

Every Pauli error model supports `to_channel()`, which returns the Kraus
operator representation for density-matrix-level analysis.

```python
import numpy as np
from qens.noise.pauli import BitFlipError, DepolarizingError

# Bit-flip channel
bf = BitFlipError(p=0.1)
channel = bf.to_channel(affected_qubits=[0])

print(f"Number of Kraus operators: {channel.num_kraus}")
# 2

# Verify completeness: sum_k E_k^dag E_k == I
print(f"Channel is valid: {channel.validate()}")
# True

# Inspect probabilities
print(f"Probabilities: {channel.probabilities()}")
# [0.9, 0.1]

# Depolarizing channel has 4 Kraus operators
dep = DepolarizingError(p=0.03)
dep_channel = dep.to_channel(affected_qubits=[0])
print(f"Depolarizing Kraus ops: {dep_channel.num_kraus}")
# 4
print(f"Valid: {dep_channel.validate()}")
# True
```

---

## Measurement Error

`MeasurementError` models asymmetric readout noise. It only applies to
measurement gates (the `applies_to` method returns `True` exclusively for
`Gate("M", ...)`).

**Constructor:**

```python
MeasurementError(p_0to1=0.01, p_1to0=None)
```

- `p_0to1`: Probability that a |0> state is misread as |1>.
- `p_1to0`: Probability that a |1> state is misread as |0>. Defaults to `p_0to1`
  (symmetric readout error) if not specified.

In the Pauli frame picture, measurement error is modeled as a bit-flip (X)
applied just before measurement, with probability equal to the average of
`p_0to1` and `p_1to0`.

```python
import numpy as np
from qens.noise.measurement import MeasurementError
from qens.core.circuit import Gate

# Symmetric readout error
meas_noise = MeasurementError(p_0to1=0.02)
print(meas_noise)
# MeasurementError(p_0to1=0.02, p_1to0=0.02)

# Asymmetric readout error
meas_asym = MeasurementError(p_0to1=0.01, p_1to0=0.05)
print(meas_asym)
# MeasurementError(p_0to1=0.01, p_1to0=0.05)

# Gate filtering: only applies to measurement gates
print(meas_noise.applies_to(Gate("M", (0,))))   # True
print(meas_noise.applies_to(Gate("H", (0,))))   # False
print(meas_noise.applies_to(Gate("CX", (0, 1))))  # False

# Sample errors
rng = np.random.default_rng(42)
error = meas_noise.sample_errors(num_qubits=4, affected_qubits=[0, 1, 2, 3], rng=rng)
print(error)
# Possible output: [0 0 0 1]  (readout flip on qubit 3)
```

---

## Gate Errors

### CoherentRotationError

Models systematic over/under-rotation of gates. Each gate application adds a
small rotation drawn from a Gaussian distribution with standard deviation
`angle_stddev`. In the Pauli frame, this is approximated as a probabilistic
Pauli error with probability `sin^2(angle)`.

Only applies to non-measurement gates (`applies_to` returns `False` for
`Gate("M", ...)`).

```python
import numpy as np
from qens.noise.gate import CoherentRotationError
from qens.core.circuit import Gate

rotation = CoherentRotationError(angle_stddev=0.05)
print(rotation)
# CoherentRotationError(angle_stddev=0.05)

# Applies to computational gates, not measurements
print(rotation.applies_to(Gate("H", (0,))))     # True
print(rotation.applies_to(Gate("CX", (0, 1))))  # True
print(rotation.applies_to(Gate("M", (0,))))      # False

rng = np.random.default_rng(42)
error = rotation.sample_errors(num_qubits=3, affected_qubits=[0, 1, 2], rng=rng)
print(error)
# Typically all zeros (small angle_stddev), occasional X/Y/Z errors
```

### CrosstalkError

Models unwanted ZZ interactions between qubit pairs during gate operations.
The `coupling_map` dictionary specifies which qubit pairs experience crosstalk
and the interaction strength (probability).

Crosstalk activates when at least one qubit in a coupled pair is among the
affected qubits. Does not apply to measurement or reset gates.

```python
import numpy as np
from qens.noise.gate import CrosstalkError

# Define crosstalk between qubit pairs
coupling = {
    (0, 1): 0.005,   # 0.5% ZZ crosstalk between qubits 0 and 1
    (1, 2): 0.003,   # 0.3% between qubits 1 and 2
}

xtalk = CrosstalkError(coupling_map=coupling)
print(xtalk)
# CrosstalkError(pairs=2)

rng = np.random.default_rng(42)
error = xtalk.sample_errors(num_qubits=3, affected_qubits=[0, 1, 2], rng=rng)
print(error)
# When triggered, both qubits in a pair get Z errors (XOR'd onto frame)
```

---

## Correlated Errors

`CorrelatedPauliError` models noise where errors on neighboring qubits are
correlated -- for example, cosmic ray events or shared control lines.

**Constructor:**

```python
CorrelatedPauliError(joint_errors)
```

`joint_errors` is a dictionary mapping qubit pairs `(q0, q1)` to a list of
`(probability, pauli_on_q0, pauli_on_q1)` tuples. The probabilities for a
given pair should sum to at most 1.0 (the remainder is the probability of no
error on that pair).

```python
import numpy as np
from qens.noise.correlated import CorrelatedPauliError
from qens.core.types import PauliOp

# Correlated XX errors on qubits (0, 1) with 1% probability
# and correlated ZZ errors on qubits (2, 3) with 0.5% probability
corr = CorrelatedPauliError(joint_errors={
    (0, 1): [
        (0.01, PauliOp.X, PauliOp.X),  # 1% chance of XX on qubits 0,1
        (0.005, PauliOp.Z, PauliOp.Z), # 0.5% chance of ZZ on qubits 0,1
    ],
    (2, 3): [
        (0.008, PauliOp.X, PauliOp.X), # 0.8% chance of XX on qubits 2,3
    ],
})
print(corr)
# CorrelatedPauliError(pairs=2)

rng = np.random.default_rng(42)
error = corr.sample_errors(num_qubits=4, affected_qubits=[0, 1, 2, 3], rng=rng)
print(error)
# Errors appear on paired qubits simultaneously
```

---

## Leakage

`LeakageError` models transitions between the computational subspace
({|0>, |1>}) and a non-computational leakage state (|2>). It is a stateful
error model that tracks which qubits are currently leaked.

**Constructor:**

```python
LeakageError(p_leak=0.001, p_relax=0.1)
```

- `p_leak`: Probability of a qubit leaking from the computational subspace to
  |2> per gate cycle.
- `p_relax`: Probability that a leaked qubit relaxes back to the computational
  subspace per gate cycle.

In the Pauli frame approximation, a leaked qubit produces a random Pauli error
(uniformly I, X, Y, or Z), modeling the maximally depolarizing effect of being
outside the code space.

```python
import numpy as np
from qens.noise.leakage import LeakageError

leak = LeakageError(p_leak=0.01, p_relax=0.3)
rng = np.random.default_rng(42)

# Initially no qubits are leaked
print(f"Leaked qubits: {leak.leaked_qubits}")
# Leaked qubits: set()

# Simulate several rounds to observe leak/relax dynamics
for cycle in range(10):
    error = leak.sample_errors(num_qubits=5, affected_qubits=[0, 1, 2, 3, 4], rng=rng)
    print(f"Cycle {cycle}: leaked={leak.leaked_qubits}, error={error}")

# Reset leakage tracking
leak.reset()
print(f"After reset: {leak.leaked_qubits}")
# After reset: set()
```

Key points about `LeakageError`:

- **Stateful:** The `leaked_qubits` property returns the set of qubit indices
  currently in the |2> state.
- **reset():** Clears all leakage tracking state. Call this between independent
  simulation runs.
- A leaked qubit remains leaked (and continues producing random Pauli errors)
  until it relaxes with probability `p_relax`.

---

## Composing Noise Models

`ComposedNoiseModel` combines multiple error models into a single model. It
applies each constituent model sequentially and merges their errors via Pauli
string multiplication.

```python
import numpy as np
from qens.noise.composed import ComposedNoiseModel
from qens.noise.pauli import DepolarizingError
from qens.noise.measurement import MeasurementError
from qens.noise.gate import CrosstalkError, CoherentRotationError

# Build a realistic noise model
noise = ComposedNoiseModel([
    DepolarizingError(p=0.001),
    MeasurementError(p_0to1=0.01, p_1to0=0.02),
    CoherentRotationError(angle_stddev=0.005),
    CrosstalkError(coupling_map={(0, 1): 0.002, (2, 3): 0.001}),
])

print(noise)
# ComposedNoiseModel([DepolarizingError(p=0.001), MeasurementError(...), ...])
```

### sample_errors vs. sample_errors_for_gate

`ComposedNoiseModel` provides two sampling methods:

- **`sample_errors(num_qubits, affected_qubits, rng)`** -- Calls every model
  regardless of gate type, composing results via Pauli multiplication.
- **`sample_errors_for_gate(num_qubits, gate, rng)`** -- Checks each model's
  `applies_to(gate)` filter first. Only models that apply to the given gate
  contribute errors. The affected qubits are taken from the gate's `qubits`
  attribute.

```python
import numpy as np
from qens.core.circuit import Gate
from qens.noise.composed import ComposedNoiseModel
from qens.noise.pauli import DepolarizingError
from qens.noise.measurement import MeasurementError

noise = ComposedNoiseModel([
    DepolarizingError(p=0.01),
    MeasurementError(p_0to1=0.05),
])

rng = np.random.default_rng(42)

# For a Hadamard gate: DepolarizingError applies, MeasurementError does not
h_gate = Gate("H", (0,))
print(noise.applies_to(h_gate))  # True (at least one sub-model applies)
error = noise.sample_errors_for_gate(num_qubits=3, gate=h_gate, rng=rng)
print(error)

# For a measurement gate: both DepolarizingError and MeasurementError apply
m_gate = Gate("M", (0,))
error = noise.sample_errors_for_gate(num_qubits=3, gate=m_gate, rng=rng)
print(error)
```

---

## Kraus Channels

Any error model that implements `to_channel()` returns a `NoiseChannel` object,
which wraps a list of Kraus matrices.

### NoiseChannel API

| Method/Property | Description |
|---|---|
| `num_kraus` | Number of Kraus operators in the channel. |
| `validate(tol=1e-10)` | Check the completeness relation: sum of E_k^dag E_k equals I. |
| `probabilities()` | Return a NumPy array of probabilities for each Kraus operator. |
| `sample(rng)` | Sample which Kraus operator is applied, returning its index. |

```python
import numpy as np
from qens.noise.pauli import DepolarizingError

dep = DepolarizingError(p=0.1)
channel = dep.to_channel(affected_qubits=[0])

# Inspect the channel
print(f"Kraus operators: {channel.num_kraus}")
# 4

print(f"Valid channel: {channel.validate()}")
# True

probs = channel.probabilities()
print(f"Probabilities: {probs}")
# [0.9, 0.0333..., 0.0333..., 0.0333...]

# Sample which operator fires
rng = np.random.default_rng(42)
idx = channel.sample(rng)
print(f"Sampled Kraus operator index: {idx}")
# 0 (identity, most likely)

# Inspect the Kraus matrices
for i, ek in enumerate(channel.kraus_ops):
    print(f"E_{i}:\n{ek}\n")
```

---

## Custom Error Models

You can create your own error models by subclassing `ErrorModel` and
implementing `sample_errors` and `__repr__`.

```python
import numpy as np
from qens.noise.base import ErrorModel
from qens.core.types import PauliOp, PauliString, QubitIndex
from typing import Sequence


class ThermalRelaxationError(ErrorModel):
    """Simplified T1/T2 relaxation in the Pauli frame picture.

    With probability p_relax, applies a random Pauli (biased toward Z
    to approximate amplitude damping).
    """

    def __init__(self, p_relax: float = 0.005, z_bias: float = 0.7) -> None:
        self.p_relax = p_relax
        self.z_bias = z_bias

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: Sequence[QubitIndex],
        rng: np.random.Generator,
    ) -> PauliString:
        error = np.zeros(num_qubits, dtype=np.uint8)
        for q in affected_qubits:
            if rng.random() < self.p_relax:
                # Biased toward Z errors
                if rng.random() < self.z_bias:
                    error[q] = PauliOp.Z
                else:
                    error[q] = rng.choice([PauliOp.X, PauliOp.Y])
        return error

    def __repr__(self) -> str:
        return f"ThermalRelaxationError(p_relax={self.p_relax})"
```

### Registering Custom Models

Use the `Registry` to make your model discoverable:

```python
from qens.core.registry import Registry
from qens.noise.base import ErrorModel

noise_registry = Registry[ErrorModel]()
noise_registry.register("thermal_relaxation", ThermalRelaxationError)

# Retrieve by name
cls = noise_registry.get("thermal_relaxation")
model = cls(p_relax=0.01)
print(model)
# ThermalRelaxationError(p_relax=0.01)
```

---

## Next Steps

- [Error-Correcting Codes](codes.md) -- Pair noise models with QEC codes.
- [Decoders](decoders.md) -- Decode syndromes produced under noise.
- [Simulation](simulation.md) -- Run Monte Carlo sampling with composed noise.
- [Visualization](visualization.md) -- Visualize circuits with error annotations.
