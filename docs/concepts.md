<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Core Concepts

This page introduces the quantum error correction concepts you need to use QENS effectively. If you are already familiar with QEC, skip to the [API Reference](api-reference.md).

---

## Quantum Error Correction at a Glance

Qubits are inherently fragile. Environmental noise, imperfect gates, and faulty measurements all introduce errors. Quantum error correction (QEC) protects information by encoding a single **logical qubit** into many **physical (data) qubits**. Additional **ancilla qubits** measure error symptoms without disturbing the encoded information. A classical **decoder** then infers what went wrong and prescribes a correction.

The pipeline in QENS mirrors this:

```
Error  -->  Syndrome extraction  -->  Decoding  -->  Correction  -->  Check
(noise)     (stabilizer measurements)  (classical)   (Pauli operator)  (logical error?)
```

---

## Pauli Errors

Quantum errors on a single qubit can be decomposed into the **Pauli operators**:

| Operator | Symbol | Effect | QENS value |
|----------|--------|--------|------------|
| Identity | I | No error | `PauliOp.I = 0` |
| Bit-flip | X | Flips \|0> and \|1> | `PauliOp.X = 1` |
| Bit-phase-flip | Y | Flips and adds phase | `PauliOp.Y = 2` |
| Phase-flip | Z | Adds relative phase | `PauliOp.Z = 3` |

An error on `n` qubits is a **Pauli string** -- a tensor product of single-qubit Paulis. In QENS, this is represented as a numpy `uint8` array of length `n`, where each entry is the `PauliOp` value:

```python
import numpy as np
from qens.core.types import PauliOp

# X error on qubit 2 of a 5-qubit system
error = np.array([0, 0, 1, 0, 0], dtype=np.uint8)  # I I X I I
```

All QENS error models sample Pauli strings. This is not an approximation for the codes and noise types QENS targets -- any single-qubit error channel can be decomposed into Pauli components.

---

## Stabilizer Codes

A stabilizer code is defined by a set of **stabilizer generators** -- mutually commuting Pauli operators that leave the code space unchanged. In QENS, each stabilizer is stored as:

```python
from qens.codes.base import Stabilizer

# Example: a ZZ stabilizer on qubits 0 and 1
stab = Stabilizer(
    pauli_string=np.array([3, 3, 0, 0, 0], dtype=np.uint8),  # Z Z I I I
    qubits=[0, 1],
    stabilizer_type="Z",
)
```

Key properties:
- All stabilizer generators must **commute** with each other
- A valid codeword is a +1 eigenstate of every stabilizer
- An error that **anticommutes** with a stabilizer flips that stabilizer's measurement outcome

---

## Syndromes

When you measure all stabilizers, the pattern of outcomes is the **syndrome** -- a binary vector where 1 indicates a stabilizer that was triggered (anticommuted with the error):

```python
code = qens.RepetitionCode(5)
error = np.zeros(5, dtype=np.uint8)
error[2] = PauliOp.X  # X error on qubit 2

syndrome = code.compute_syndrome(error)
# array([0, 1, 1, 0], dtype=uint8) -- stabilizers 1 and 2 triggered
```

The syndrome tells the decoder *where* errors likely occurred, without revealing the encoded information. Different errors can produce the same syndrome; the decoder's job is to guess the most probable one.

---

## CSS Codes

**Calderbank-Shor-Steane (CSS) codes** are an important subclass of stabilizer codes where:

- **X-type stabilizers** are products of Pauli X operators (they detect Z errors)
- **Z-type stabilizers** are products of Pauli Z operators (they detect X errors)

The surface code and color code in QENS are both CSS codes. CSS structure allows X and Z errors to be decoded independently, simplifying the decoder.

For CSS codes, the stabilizer commutation requirement reduces to: every pair of X and Z stabilizers must share an **even** number of qubits.

---

## Code Distance

The **distance** `d` of a code is the minimum weight (number of non-identity Paulis) of a logical operator -- an operator that commutes with all stabilizers but changes the encoded information.

A distance-`d` code can correct up to `floor((d-1)/2)` errors. Larger distance means more protection but more physical qubits:

| Code | Distance | Data qubits | Correctable errors |
|------|----------|-------------|-------------------|
| RepetitionCode(3) | 3 | 3 | 1 |
| RepetitionCode(5) | 5 | 5 | 2 |
| SurfaceCode(3) | 3 | 9 | 1 |
| SurfaceCode(5) | 5 | 25 | 2 |

---

## Logical Error Rate and Threshold

A **logical error** occurs when the combined effect of the physical error and the decoder's correction is itself a logical operator -- the decoder was "fooled" into applying the wrong correction.

The **logical error rate** is the fraction of Monte Carlo shots that result in a logical error. The central goal of QEC is to make this rate arbitrarily small by increasing the code distance.

The **threshold** is the physical error rate below which larger codes perform strictly better. Below threshold, the logical error rate decreases exponentially with distance. Above threshold, larger codes actually perform worse because there are too many errors for the code to handle.

QENS's `ThresholdExperiment` automates the measurement of this relationship by sweeping error rates across multiple distances and producing the standard threshold plot.

---

## The Pauli Frame Model

Simulating a full quantum state of `n` qubits requires tracking `2^n` amplitudes -- intractable for the hundreds or thousands of qubits in a QEC code. QENS avoids this entirely.

The **Pauli frame** model exploits the fact that:
1. QEC circuits consist entirely of **Clifford gates** (H, CNOT, CZ, S, measurements)
2. Clifford gates map Pauli operators to Pauli operators
3. We only need to track how Pauli errors propagate, not the full quantum state

This reduces the simulation cost to **O(n) per gate** instead of O(2^n). The `PauliFrameSimulator` class implements this:

```python
from qens.simulation import PauliFrameSimulator
from qens.core.types import PauliOp

sim = PauliFrameSimulator(num_qubits=2)
sim.apply_error(np.array([PauliOp.X, PauliOp.I], dtype=np.uint8))

# After a CNOT, X on control propagates to target
from qens import Gate
sim.propagate_gate(Gate("CX", (0, 1)))
print(sim.frame)  # [X, X] -- error spread to qubit 1
```

Propagation rules for key gates:

| Gate | Input error | Output error |
|------|-------------|-------------|
| H | X | Z |
| H | Z | X |
| H | Y | Y |
| CNOT | X on control | X on both |
| CNOT | Z on target | Z on both |
| CZ | X on either | X on that qubit + Z on the other |

The `NoisySampler` uses this model internally to run the full Monte Carlo loop efficiently.

---

## Kraus Representation

For users who need density-matrix-level detail, QENS error models can provide their **Kraus representation**. A noise channel acting on a density matrix rho is:

```
rho  -->  sum_k  E_k @ rho @ E_k^dagger
```

where `E_k` are Kraus operators satisfying the completeness relation `sum_k E_k^dag E_k = I`.

```python
channel = qens.DepolarizingError(p=0.01).to_channel(affected_qubits=[0])
print(channel.validate())       # True
print(channel.num_kraus)        # 4 (I, X, Y, Z)
print(channel.probabilities())  # [0.99, 0.0033, 0.0033, 0.0033]
```

Not all error models provide Kraus representations (e.g., `LeakageError` and `CorrelatedPauliError` do not). The Pauli-frame sampling method (`sample_errors`) is always available.

---

## Next Steps

- [Error Models](error-models.md) -- How QENS models each type of noise
- [QEC Codes](codes.md) -- The three code families and their properties
- [Decoders](decoders.md) -- How syndromes are turned into corrections
- [Architecture](architecture.md) -- Technical design of the SDK
