<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Syndrome Extraction Guide

Syndrome extraction is the core measurement step in quantum error correction: you measure a set of **stabilizer generators** to detect where errors occurred, without disturbing the encoded logical information.

This guide explains the mechanics, walks through the QENS API for syndrome extraction, and covers practical considerations like CSS code structure, logical errors, and measurement noise.

---

## What Is a Syndrome?

When an error $E$ (a Pauli string) acts on the data qubits, each stabilizer generator $S_i$ either **commutes** or **anticommutes** with $E$:

- $S_i E = E S_i$ → measurement outcome unchanged → syndrome bit 0
- $S_i E = -E S_i$ → measurement outcome flipped → syndrome bit 1

The syndrome is the binary vector of all measurement outcomes.

```python
import numpy as np
from qens import RepetitionCode
from qens.core.types import PauliOp

code = RepetitionCode(distance=5)

# X error on qubit 2
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[2] = PauliOp.X

syndrome = code.compute_syndrome(error)
# array([0, 1, 1, 0], dtype=uint8)
# Stabilizers 1 and 2 anticommute with the error
```

---

## Stabilizer Generators

Call `code.stabilizer_generators()` to inspect the full set:

```python
stabs = code.stabilizer_generators()
for i, s in enumerate(stabs):
    print(f"S{i}: type={s.stabilizer_type}, qubits={s.qubits}")
```

Each `Stabilizer` object has:

| Field | Type | Description |
|-------|------|-------------|
| `pauli_string` | `np.ndarray[uint8]` | Full Pauli string over all qubits |
| `qubits` | `list[int]` | Qubit indices in the stabilizer support |
| `stabilizer_type` | `str` | `"X"` or `"Z"` (for CSS codes) |

---

## Syndromes Are XOR-Linear

Syndrome extraction is a linear map over GF(2). If errors $A$ and $B$ act on disjoint qubits:

```
syndrome(A ⊗ B) = syndrome(A) XOR syndrome(B)
```

This means two errors can **cancel** each other's syndromes:

```python
from qens.utils.pauli_algebra import pauli_string_multiply

e1 = np.zeros(5, dtype=np.uint8); e1[1] = PauliOp.X  # syndrome [1,1,0,0]
e2 = np.zeros(5, dtype=np.uint8); e2[2] = PauliOp.X  # syndrome [0,1,1,0]

combined, _ = pauli_string_multiply(e1, e2)
syndrome_combined = code.compute_syndrome(combined)
# [1, 0, 1, 0] — the inner stabilizer (between qubits 1 and 2) cancels
```

The decoder must figure out which combination of errors most likely produced the observed syndrome.

---

## CSS Codes: X and Z Syndromes Are Independent

For CSS codes (`SurfaceCode`, `ColorCode`), stabilizers split into two types:

- **Z-type stabilizers** detect X errors (anticommute with X)
- **X-type stabilizers** detect Z errors (anticommute with Z)

```python
from qens import SurfaceCode

surf = SurfaceCode(distance=3)
stabs = surf.stabilizer_generators()

x_stabs = [s for s in stabs if s.stabilizer_type == 'X']
z_stabs = [s for s in stabs if s.stabilizer_type == 'Z']

print(f"X-type: {len(x_stabs)}, Z-type: {len(z_stabs)}")
```

**Consequence:** X and Z errors can be decoded independently, which is why decoders like MWPM work on each sector separately.

A **Y error** (= X·Z) triggers both X-type and Z-type stabilizers simultaneously:

```python
error = np.zeros(surf.num_data_qubits, dtype=np.uint8)
error[4] = PauliOp.Y  # Center qubit

syndrome = surf.compute_syndrome(error)
# Both X-sector and Z-sector bits are set
```

---

## Syndrome Patterns by Error Location

The location of syndrome defects encodes the error pattern:

| Error location | Stabilizers triggered |
|----------------|----------------------|
| Interior qubit | Two adjacent stabilizers (syndrome "endpoints") |
| Boundary qubit | One stabilizer (syndrome "half-chain") |
| No error | Zero stabilizers |
| Logical operator | Zero stabilizers (undetectable) |

For the surface code, each X error creates a pair of defects in the Z-sector of the syndrome, connected by the shortest path on the decoding graph. The decoder's job is to find that path.

---

## Logical Errors: Undetectable Failures

A **logical error** is a Pauli string that commutes with every stabilizer (zero syndrome) but is not in the stabilizer group — it anticommutes with at least one logical operator.

```python
# Logical X of the repetition code = X on all qubits
logical_x = np.ones(code.num_data_qubits, dtype=np.uint8)

syndrome = code.compute_syndrome(logical_x)
# array([0, 0, 0, 0]) — zero syndrome!

is_logical = code.is_logical_error(logical_x)
# True
```

This is the failure mode QEC protects against. A decoder fails when it proposes a correction $C$ such that $E \cdot C$ is a logical error.

---

## Noisy Syndrome Extraction

In hardware, stabilizer measurements are imperfect. `MeasurementError` models independent bit-flip errors on the ancilla qubits:

```python
from qens import BitFlipError, MeasurementError, ComposedNoiseModel

data_noise  = BitFlipError(p=0.02)
meas_noise  = MeasurementError(p=0.01)
total_noise = ComposedNoiseModel([data_noise, meas_noise])
```

**Important:** Measurement errors mean a single syndrome extraction round is unreliable. Production QEC implementations use **repeated syndrome extraction** and look for stable defects across multiple rounds. QENS v0 models single-round extraction; multi-round support is planned.

---

## Full Extraction-to-Decode Workflow

```python
import numpy as np
from qens import SurfaceCode, MWPMDecoder, DepolarizingError
from qens.utils.pauli_algebra import pauli_string_multiply

code    = SurfaceCode(distance=3)
decoder = MWPMDecoder(code)
noise   = DepolarizingError(p=0.05)
rng     = np.random.default_rng(42)

# 1. Sample a random error
error = noise.sample_errors(
    num_qubits=code.num_data_qubits,
    affected_qubits=list(range(code.num_data_qubits)),
    rng=rng,
)

# 2. Extract syndrome
syndrome = code.compute_syndrome(error)

# 3. Decode
result = decoder.decode(syndrome)

# 4. Check residual
residual, _ = pauli_string_multiply(error, result.correction)
failed = code.is_logical_error(residual)

print(f"Error:    {error}")
print(f"Syndrome: {syndrome}")
print(f"Correction: {result.correction}")
print(f"Logical error: {failed}")
```

For statistical accuracy over many shots, use `NoisySampler.run()` instead of rolling your own loop:

```python
from qens import NoisySampler

sampler = NoisySampler(seed=42)
result = sampler.run(code, noise, decoder, shots=10_000)
print(f"Logical error rate: {result.logical_error_rate:.4f}")
```

---

## Visualizing the Syndrome

The decoding graph visualizer highlights active syndrome bits (defects) as colored nodes:

```python
from qens import draw_decoding_graph

decoder.precompute()
fig = draw_decoding_graph(decoder, syndrome=syndrome, title="Active Syndrome")
fig.show()
```

---

## Next Steps

- [Decoders Guide](decoders.md) — How each decoder interprets the syndrome
- [Syndrome Extraction Notebook](notebooks/02_syndrome_extraction.ipynb) — Interactive walkthrough
- [Decoder Comparison Guide](decoder-comparison.md) — Benchmarking all three decoders
- [Error Models](error-models.md) — The noise models that produce the errors
