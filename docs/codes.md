# Error-Correcting Codes Guide

This guide covers the quantum error-correcting codes available in QENS:
the repetition code, the rotated surface code, and the color code. You will
learn how to construct codes, inspect their stabilizer structure, compute
syndromes, and build syndrome extraction circuits.

---

## Overview

All codes subclass `QECCode` (defined in `qens.codes.base`). The base class
defines the following interface:

| Property / Method | Description |
|---|---|
| `name` | Human-readable name, e.g. `"Repetition-5"`. |
| `num_data_qubits` | Number of data qubits. |
| `num_ancilla_qubits` | Number of ancilla qubits used for syndrome extraction. |
| `num_qubits` | Total qubits: `num_data_qubits + num_ancilla_qubits`. |
| `code_distance` | The code distance `d`. |
| `stabilizer_generators()` | List of `Stabilizer` objects defining the code. |
| `logical_operators()` | List of `LogicalOperator` objects (logical X and Z). |
| `check_matrix()` | Parity check matrix H as a NumPy array. |
| `syndrome_circuit(rounds=1)` | Build the syndrome extraction `Circuit`. |
| `qubit_coordinates()` | Map qubit index to `(row, col)` coordinate for visualization. |
| `compute_syndrome(error)` | Compute the syndrome for a given Pauli error. |
| `is_logical_error(residual)` | Check if a residual error is a logical error. |

### Key Data Types

```python
from qens.codes.base import Stabilizer, LogicalOperator

# Stabilizer: a Pauli string, its support qubits, and type ("X" or "Z")
# LogicalOperator: a Pauli string and a label ("X_L" or "Z_L")
```

A `Stabilizer` is a frozen dataclass with three fields:

- `pauli_string` -- A `PauliString` (NumPy `uint8` array) of length
  `num_data_qubits`.
- `qubits` -- List of qubit indices where the stabilizer acts non-trivially.
- `stabilizer_type` -- Either `"X"` or `"Z"`.

A `LogicalOperator` has:

- `pauli_string` -- The Pauli string representation.
- `label` -- Either `"X_L"` or `"Z_L"`.

---

## Repetition Code

The `RepetitionCode(distance)` implements a 1D chain of `d` data qubits with
`d - 1` ancilla qubits measuring ZZ stabilizers between adjacent pairs. It
corrects bit-flip (X) errors.

**Requirements:** `distance >= 2`.

### Qubit Layout

For distance 5, the layout is a linear chain:

```
D0 -- A0 -- D1 -- A1 -- D2 -- A2 -- D3 -- A3 -- D4
```

- `D0..D4` are data qubits (indices 0 through 4).
- `A0..A3` are ancilla qubits (indices 5 through 8).
- Each ancilla measures the ZZ stabilizer between its two neighboring data
  qubits.

### Basic Usage

```python
from qens.codes.repetition import RepetitionCode

code = RepetitionCode(distance=5)

print(code.name)                # Repetition-5
print(code.num_data_qubits)     # 5
print(code.num_ancilla_qubits)  # 4
print(code.num_qubits)          # 9
print(code.code_distance)       # 5
```

### Inspecting Stabilizers

```python
from qens.codes.repetition import RepetitionCode

code = RepetitionCode(distance=3)
stabs = code.stabilizer_generators()

for s in stabs:
    print(f"Type={s.stabilizer_type}, qubits={s.qubits}, pauli={s.pauli_string}")
# Type=Z, qubits=[0, 1], pauli=[3 3 0]
# Type=Z, qubits=[1, 2], pauli=[0 3 3]
```

The Pauli values are `PauliOp.Z = 3`. Each stabilizer acts as ZZ on its two
data qubits and I on the rest.

### Check Matrix

For distance 3, the check matrix is:

```python
import numpy as np
from qens.codes.repetition import RepetitionCode

code = RepetitionCode(distance=3)
H = code.check_matrix()
print(H)
# [[1 1 0]
#  [0 1 1]]
```

Each row is a stabilizer; a `1` marks the data qubits it covers.

### Computing a Syndrome

```python
import numpy as np
from qens.codes.repetition import RepetitionCode
from qens.core.types import PauliOp

code = RepetitionCode(distance=5)

# Inject an X error on qubit 2
error = np.zeros(5, dtype=np.uint8)
error[2] = PauliOp.X

syndrome = code.compute_syndrome(error)
print(syndrome)
# [0 1 1 0]  -- stabilizers 1 and 2 are triggered (the ones touching qubit 2)
```

### Checking Logical Errors

```python
import numpy as np
from qens.codes.repetition import RepetitionCode
from qens.core.types import PauliOp

code = RepetitionCode(distance=3)

# A single X error is correctable (not a logical error)
single_x = np.zeros(3, dtype=np.uint8)
single_x[0] = PauliOp.X
print(code.is_logical_error(single_x))
# False

# X on all data qubits is the logical X operator
all_x = np.full(3, PauliOp.X, dtype=np.uint8)
print(code.is_logical_error(all_x))
# True
```

### Logical Operators

```python
from qens.codes.repetition import RepetitionCode

code = RepetitionCode(distance=3)
logicals = code.logical_operators()

for op in logicals:
    print(f"{op.label}: {op.pauli_string}")
# X_L: [1 1 1]   (X on all data qubits)
# Z_L: [3 0 0]   (Z on qubit 0)
```

---

## Surface Code

The `SurfaceCode(distance, rotated=True)` implements the rotated surface code
on a `d x d` grid of data qubits. It is a CSS code with separate X-type and
Z-type stabilizers.

**Requirements:**
- `distance >= 2`
- `distance` must be odd

### Structure

For distance 3, the code has:

- **9 data qubits** arranged on a 3 x 3 grid.
- **8 stabilizer generators** (4 X-type + 4 Z-type).

Data qubits sit at integer coordinates `(r, c)` for `r, c` in `[0, d-1]`.
Ancilla qubits sit at plaquette centers. X-stabilizers and Z-stabilizers are
placed on alternating plaquettes, with boundary conditions ensuring the code
has exactly one logical qubit.

### Basic Usage

```python
from qens.codes.surface import SurfaceCode

code = SurfaceCode(distance=3)

print(code.name)                # RotatedSurface-3
print(code.num_data_qubits)     # 9
print(code.num_ancilla_qubits)  # 8
print(code.code_distance)       # 3

stabs = code.stabilizer_generators()
x_stabs = [s for s in stabs if s.stabilizer_type == "X"]
z_stabs = [s for s in stabs if s.stabilizer_type == "Z"]
print(f"X stabilizers: {len(x_stabs)}, Z stabilizers: {len(z_stabs)}")
# X stabilizers: 4, Z stabilizers: 4
```

### Injecting an Error and Decoding the Syndrome

```python
import numpy as np
from qens.codes.surface import SurfaceCode
from qens.core.types import PauliOp

code = SurfaceCode(distance=3)

# X error on the center qubit (index 4, which is position (1,1))
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[4] = PauliOp.X

syndrome = code.compute_syndrome(error)
print(f"Syndrome: {syndrome}")
print(f"Active stabilizers: {list(np.nonzero(syndrome)[0])}")
```

### Stabilizer Commutation

A defining property of stabilizer codes is that all stabilizers mutually
commute. You can verify this:

```python
import numpy as np
from qens.codes.surface import SurfaceCode
from qens.utils.pauli_algebra import symplectic_inner_product

code = SurfaceCode(distance=3)
stabs = code.stabilizer_generators()

# All stabilizers commute (symplectic inner product = 0)
for i in range(len(stabs)):
    for j in range(i + 1, len(stabs)):
        sip = symplectic_inner_product(stabs[i].pauli_string, stabs[j].pauli_string)
        assert sip == 0, f"Stabilizers {i} and {j} do not commute!"

print("All stabilizers commute.")

# Logical operators anticommute with each other
logicals = code.logical_operators()
x_l = logicals[0]  # X_L
z_l = logicals[1]  # Z_L
sip = symplectic_inner_product(x_l.pauli_string, z_l.pauli_string)
print(f"X_L and Z_L anticommute: {sip == 1}")
# True
```

---

## Color Code

The `ColorCode(distance, lattice_type)` implements triangular color codes.
Color codes are CSS codes that support transversal implementation of the full
Clifford group -- a significant advantage for fault-tolerant computation.

**Requirements:**
- `distance >= 3`
- `distance` must be odd
- `lattice_type` must be `"4.8.8"` or `"6.6.6"`

### 4.8.8 Lattice (Steane Code Family)

The 4.8.8 lattice places data qubits on a centered hexagonal grid. Plaquettes
are derived from the hex lattice structure and have even weight (typically 4
or 6 qubits). For distance `d`, the number of data qubits is
`n = 3t^2 + 3t + 1` where `t = (d-1)/2`.

```python
from qens.codes.color import ColorCode

code = ColorCode(distance=3, lattice_type="4.8.8")

print(code.name)                  # Color-4.8.8-3
print(code.num_data_qubits)       # 7 (Steane code)
print(code.num_ancilla_qubits)    # varies by construction
print(code.code_distance)         # 3
print(code.supports_transversal_clifford)  # True

stabs = code.stabilizer_generators()
print(f"Total stabilizers: {len(stabs)}")

# Color codes have paired X and Z stabilizers on the same plaquettes
x_stabs = [s for s in stabs if s.stabilizer_type == "X"]
z_stabs = [s for s in stabs if s.stabilizer_type == "Z"]
print(f"X stabilizers: {len(x_stabs)}, Z stabilizers: {len(z_stabs)}")
```

### 6.6.6 Lattice

The 6.6.6 lattice uses a triangular grid with rectangular (2x2) plaquettes,
each containing 4 data qubits (even weight).

```python
from qens.codes.color import ColorCode

code = ColorCode(distance=3, lattice_type="6.6.6")

print(code.name)                  # Color-6.6.6-3
print(code.num_data_qubits)       # 6
print(code.num_ancilla_qubits)    # varies
print(code.supports_transversal_clifford)  # True

stabs = code.stabilizer_generators()
for s in stabs[:4]:
    print(f"Type={s.stabilizer_type}, qubits={s.qubits}")
```

### Distance-5 Color Code

```python
from qens.codes.color import ColorCode

code = ColorCode(distance=5, lattice_type="4.8.8")

print(code.name)             # Color-4.8.8-5
print(code.num_data_qubits)  # 19
print(code.code_distance)    # 5
```

---

## Lattice Structure

Every code that builds a lattice exposes it through the `lattice` property.
The lattice is composed of `LatticeNode` and `LatticeEdge` objects.

```python
from qens.codes.lattice import Lattice, LatticeNode, LatticeEdge
```

| Class | Fields |
|---|---|
| `LatticeNode` | `index: int`, `coordinate: tuple`, `role: str` (one of `"data"`, `"ancilla_x"`, `"ancilla_z"`, `"ancilla"`) |
| `LatticeEdge` | `node_a: int`, `node_b: int`, `weight: float` (default 1.0) |

### Lattice API

| Method / Property | Description |
|---|---|
| `nodes` | List of all `LatticeNode` objects. |
| `edges` | List of all `LatticeEdge` objects. |
| `neighbors(index)` | List of neighbor indices for a given node. |
| `data_nodes()` | List of nodes with `role == "data"`. |
| `ancilla_nodes()` | List of nodes with `role != "data"`. |
| `get_node(index)` | Get a specific node by index. |

```python
from qens.codes.repetition import RepetitionCode

code = RepetitionCode(distance=3)
lattice = code.lattice

print(lattice)
# Lattice(nodes=5, edges=4)

# Iterate over data qubits
for node in lattice.data_nodes():
    print(f"  {node}")
# Node(0, (0, 0), data)
# Node(1, (0, 2), data)
# Node(2, (0, 4), data)

# Iterate over ancilla qubits
for node in lattice.ancilla_nodes():
    print(f"  {node}")
# Node(3, (0, 1), ancilla_z)
# Node(4, (0, 3), ancilla_z)

# Query neighbors
print(f"Neighbors of qubit 1: {lattice.neighbors(1)}")
# [3, 4]  (connected to both ancilla qubits)
```

---

## Syndrome Computation

The `compute_syndrome(error)` method uses the symplectic inner product between
each stabilizer and the error to produce the syndrome -- a binary array
indicating which stabilizers are violated.

```python
import numpy as np
from qens.codes.surface import SurfaceCode
from qens.core.types import PauliOp

code = SurfaceCode(distance=3)

# Create a two-qubit X error
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[0] = PauliOp.X
error[1] = PauliOp.X

syndrome = code.compute_syndrome(error)
print(f"Syndrome: {syndrome}")
print(f"Number of defects: {np.sum(syndrome)}")
```

### Checking for Logical Errors

After applying a correction, the residual error (original error composed with
the correction) must be checked. `is_logical_error(residual)` returns `True` if
the residual:

1. Commutes with all stabilizers (is in the normalizer), AND
2. Anticommutes with at least one logical operator.

```python
import numpy as np
from qens.codes.repetition import RepetitionCode
from qens.core.types import PauliOp

code = RepetitionCode(distance=3)

# Identity residual: no error (trivially in stabilizer group)
identity = np.zeros(3, dtype=np.uint8)
print(code.is_logical_error(identity))
# False

# Single X error: does not commute with all stabilizers
single_x = np.zeros(3, dtype=np.uint8)
single_x[1] = PauliOp.X
print(code.is_logical_error(single_x))
# False (not even in the normalizer)

# Logical X: commutes with stabilizers, anticommutes with Z_L
all_x = np.full(3, PauliOp.X, dtype=np.uint8)
print(code.is_logical_error(all_x))
# True
```

---

## Syndrome Circuits

The `syndrome_circuit(rounds)` method builds a `Circuit` that extracts the
syndrome. The circuit structure for each round is:

1. **Reset** all ancilla qubits.
2. **Entangle** ancillas with data qubits:
   - X-stabilizers: H on ancilla, then CX from ancilla to each data qubit, then
     H on ancilla.
   - Z-stabilizers: CX from each data qubit to the ancilla.
3. **Measure** all ancilla qubits.

```python
from qens.codes.repetition import RepetitionCode

code = RepetitionCode(distance=3)
circuit = code.syndrome_circuit(rounds=1)

print(circuit)
# Circuit(num_qubits=5, depth=...)

print(f"Total qubits: {circuit.num_qubits}")
# 5 (3 data + 2 ancilla)

# Inspect the moments
for i, moment in enumerate(circuit.moments):
    gates = [(g.name, g.qubits) for g in moment.gates]
    print(f"Moment {i}: {gates}")
```

For multiple rounds:

```python
from qens.codes.surface import SurfaceCode

code = SurfaceCode(distance=3)
circuit = code.syndrome_circuit(rounds=3)

print(f"Circuit depth for 3 rounds: {circuit.depth}")
print(f"Total qubits: {circuit.num_qubits}")
# 17 (9 data + 8 ancilla)
```

---

## Custom Codes

To implement a new code family, subclass `QECCode` and implement all abstract
methods:

```python
from qens.codes.base import QECCode, Stabilizer, LogicalOperator
from qens.core.circuit import Circuit
import numpy as np

class MyCode(QECCode):

    @property
    def name(self) -> str:
        return "MyCode-3"

    @property
    def num_data_qubits(self) -> int:
        return 5  # example

    @property
    def num_ancilla_qubits(self) -> int:
        return 4  # example

    @property
    def code_distance(self) -> int:
        return 3

    def stabilizer_generators(self) -> list[Stabilizer]:
        # Define your stabilizers here
        ...

    def logical_operators(self) -> list[LogicalOperator]:
        # Define logical X and Z
        ...

    def check_matrix(self) -> np.ndarray:
        # Build from stabilizer_generators
        ...

    def syndrome_circuit(self, rounds: int = 1) -> Circuit:
        # Build syndrome extraction circuit
        ...

    def qubit_coordinates(self) -> dict[int, tuple]:
        # Map qubit index to (row, col) for visualization
        ...
```

Register with the code registry:

```python
from qens.core.registry import Registry
from qens.codes.base import QECCode

code_registry = Registry[QECCode]()
code_registry.register("my_code", MyCode)
```

---

## Next Steps

- [Error Models](error-models.md) -- Noise models to pair with your codes.
- [Decoders](decoders.md) -- Decode syndromes from noisy codes.
- [Simulation](simulation.md) -- Run full Monte Carlo threshold experiments.
- [Visualization](visualization.md) -- Visualize lattices and syndrome circuits.
