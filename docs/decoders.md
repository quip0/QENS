<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Decoders Guide

This guide covers the three decoders shipped with QENS: the lookup table
decoder, the minimum-weight perfect matching (MWPM) decoder, and the
union-find decoder. You will learn how to choose a decoder, use it to correct
errors, and build custom decoders.

---

## Overview

All decoders inherit from `Decoder` (defined in `qens.decoders.base`):

```python
from qens.decoders.base import Decoder, DecoderResult
```

**Constructor:** Every decoder takes a `QECCode` instance:

```python
decoder = SomeDecoder(code)
```

**Key method:** `decode(syndrome) -> DecoderResult`

The `DecoderResult` dataclass contains:

| Field | Type | Description |
|---|---|---|
| `correction` | `PauliString` | The Pauli correction to apply. |
| `success` | `bool` | Provisional success estimate (see note below). |
| `metadata` | `dict` | Decoder-specific information (e.g., matching details). |

**Optional methods:**

| Method | Description |
|---|---|
| `precompute()` | Pre-build decoding structures (tables, graphs). Called automatically on first `decode()` if not called manually. |
| `build_decoding_graph()` | Return a graph dict with `"nodes"`, `"edges"`, `"boundary_nodes"` keys. Used by visualization. |

---

## Choosing a Decoder

| Decoder | Time Complexity | Decode Quality | Best For |
|---|---|---|---|
| `LookupTableDecoder` | O(1) lookup after precompute | Exact (optimal) | Small codes, d <= 7 |
| `MWPMDecoder` | O(n^2) greedy matching | Near-optimal | Medium codes, d <= 15-20 |
| `UnionFindDecoder` | O(n * alpha(n)) | Approximate | Any code size |

**General guidance:**

- For prototyping and small experiments, `LookupTableDecoder` gives optimal
  corrections but is limited by exponential memory usage in the code size.
- For research-scale surface code simulations, `MWPMDecoder` provides
  near-optimal quality with reasonable speed.
- For large-scale simulations or threshold sweeps, `UnionFindDecoder` is the
  fastest option with acceptable quality.

---

## Lookup Table Decoder

`LookupTableDecoder` precomputes a mapping from every possible syndrome to
the minimum-weight correction. This guarantees optimal decoding for all
correctable errors, but the table grows exponentially with the number of
stabilizers, making it practical only for small codes (distance 7 or below).

```python
from qens.decoders.lookup import LookupTableDecoder
```

### Usage

```python
import numpy as np
from qens.codes.repetition import RepetitionCode
from qens.decoders.lookup import LookupTableDecoder
from qens.core.types import PauliOp

# Create a distance-3 repetition code and decoder
code = RepetitionCode(distance=3)
decoder = LookupTableDecoder(code)

# Precompute is optional -- it runs automatically on first decode()
decoder.precompute()

# Inject a single X error on qubit 1
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[1] = PauliOp.X

# Compute syndrome
syndrome = code.compute_syndrome(error)
print(f"Syndrome: {syndrome}")
# [1 1]

# Decode
result = decoder.decode(syndrome)
print(f"Correction: {result.correction}")
print(f"Success: {result.success}")
print(f"Table hit: {result.metadata['table_hit']}")
# Correction: [0 1 0]  (X correction on qubit 1)
# Success: True
# Table hit: True
```

### Metadata

The `LookupTableDecoder` provides:

- `"table_hit"` (bool): Whether the syndrome was found in the precomputed
  table. If `False`, the decoder returns the identity (no correction).

---

## MWPM Decoder

`MWPMDecoder` implements a greedy minimum-weight perfect matching algorithm.
It is a pure Python implementation with no external dependencies.

The decoder builds a decoding graph where:

- **Nodes** correspond to stabilizer generators.
- **Edges** connect same-type stabilizers that share data qubits, weighted by 1.0.
- A **boundary node** connects to weight-2 stabilizers with weight 0.5.

When a syndrome arrives, the decoder identifies defects (non-zero syndrome
bits), computes shortest-path distances between all pairs of defects, and
greedily matches the closest unmatched pairs.

```python
from qens.decoders.mwpm import MWPMDecoder
```

### Usage

```python
import numpy as np
from qens.codes.surface import SurfaceCode
from qens.decoders.mwpm import MWPMDecoder
from qens.core.types import PauliOp

code = SurfaceCode(distance=3)
decoder = MWPMDecoder(code)
decoder.precompute()

# Inject an X error on the center qubit
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[4] = PauliOp.X

syndrome = code.compute_syndrome(error)
print(f"Syndrome: {syndrome}")
print(f"Defects at: {list(np.nonzero(syndrome)[0])}")

result = decoder.decode(syndrome)
print(f"Correction: {result.correction}")
print(f"Num defects: {result.metadata['num_defects']}")
print(f"Matching: {result.metadata['matching']}")
```

### Decoding Graph

You can inspect the decoding graph structure, which is also used by the
visualization module:

```python
from qens.codes.surface import SurfaceCode
from qens.decoders.mwpm import MWPMDecoder

code = SurfaceCode(distance=3)
decoder = MWPMDecoder(code)
decoder.precompute()

graph = decoder.build_decoding_graph()
print(f"Nodes: {len(graph['nodes'])}")
print(f"Edges: {len(graph['edges'])}")
print(f"Boundary nodes: {graph['boundary_nodes']}")

# Each edge is a dict with 'from', 'to', 'weight', 'data_qubit'
for edge in graph['edges'][:5]:
    print(f"  {edge}")
```

### Metadata

The `MWPMDecoder` provides:

- `"num_defects"` (int): Number of non-zero syndrome bits.
- `"matching"` (list): List of `(node_a, node_b, weight)` tuples representing
  the matching found by the decoder.

---

## Union-Find Decoder

`UnionFindDecoder` implements the growth-and-fusion strategy described by
Delfosse and Nickerson (2021). It uses a weighted union-find data structure
with path compression, giving near-linear time complexity.

The algorithm works in two phases:

1. **Growth phase:** Process edges in order of increasing weight. When an edge
   connects two clusters where at least one contains a defect, fuse them.
2. **Peeling phase:** Extract a correction from the fused cluster structure by
   flipping data qubits shared between matched stabilizers.

```python
from qens.decoders.union_find import UnionFindDecoder
```

### Usage

```python
import numpy as np
from qens.codes.surface import SurfaceCode
from qens.decoders.union_find import UnionFindDecoder
from qens.core.types import PauliOp

code = SurfaceCode(distance=5)
decoder = UnionFindDecoder(code)
decoder.precompute()

# Inject a weight-2 error
error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[6] = PauliOp.X
error[7] = PauliOp.X

syndrome = code.compute_syndrome(error)
result = decoder.decode(syndrome)

print(f"Correction: {result.correction}")
print(f"Success: {result.success}")
print(f"Num defects: {result.metadata['num_defects']}")
```

### Metadata

The `UnionFindDecoder` provides:

- `"num_defects"` (int): Number of non-zero syndrome bits.

---

## Decoding Workflow

Here is the complete step-by-step flow for error injection, syndrome
extraction, decoding, and logical error checking:

```python
import numpy as np
from qens.codes.surface import SurfaceCode
from qens.decoders.mwpm import MWPMDecoder
from qens.noise.pauli import DepolarizingError
from qens.core.types import PauliOp
from qens.utils.pauli_algebra import pauli_string_multiply

# Step 1: Create code and decoder
code = SurfaceCode(distance=3)
decoder = MWPMDecoder(code)

# Step 2: Precompute decoding structures (optional, auto-called on first decode)
decoder.precompute()

# Step 3: Sample an error (or inject one manually)
rng = np.random.default_rng(42)
noise = DepolarizingError(p=0.05)
error = noise.sample_errors(
    num_qubits=code.num_data_qubits,
    affected_qubits=list(range(code.num_data_qubits)),
    rng=rng,
)
print(f"Error: {error}")

# Step 4: Compute syndrome and decode
syndrome = code.compute_syndrome(error)
print(f"Syndrome: {syndrome}")

result = decoder.decode(syndrome)
print(f"Correction: {result.correction}")

# Step 5: Check the residual for logical error
residual, _ = pauli_string_multiply(error, result.correction)
is_logical = code.is_logical_error(residual)
print(f"Residual: {residual}")
print(f"Logical error: {is_logical}")
```

---

## Note on DecoderResult.success

The `success` field in `DecoderResult` is a **provisional** estimate. The
decoder only sees the syndrome, not the actual physical error. It estimates
success by checking whether the correction itself would be a logical error,
which is not the same as checking whether error + correction is a logical
error.

For true success evaluation, use `NoisySampler.run()`, which computes the
residual `error * correction` and calls `code.is_logical_error(residual)`:

```python
from qens.codes.surface import SurfaceCode
from qens.decoders.mwpm import MWPMDecoder
from qens.noise.pauli import DepolarizingError
from qens.simulation.sampler import NoisySampler

code = SurfaceCode(distance=3)
decoder = MWPMDecoder(code)
noise = DepolarizingError(p=0.05)

sampler = NoisySampler(seed=42)
result = sampler.run(code, noise, decoder, shots=1000)

print(f"Logical error rate: {result.logical_error_rate:.4f}")
print(f"Logical errors: {result.logical_error_count} / {result.num_shots}")
```

The `decode()` method is still useful for inspecting individual corrections
and debugging, but should not be relied upon for statistical accuracy.

---

## Custom Decoders

To implement a custom decoder, subclass `Decoder` and implement `decode()`:

```python
import numpy as np
from qens.decoders.base import Decoder, DecoderResult
from qens.core.types import Syndrome, PauliOp


class NaiveDecoder(Decoder):
    """A simple decoder that corrects the first non-zero syndrome bit."""

    def decode(self, syndrome: Syndrome) -> DecoderResult:
        nd = self._code.num_data_qubits
        correction = np.zeros(nd, dtype=np.uint8)

        # Find first defect
        defects = np.nonzero(syndrome)[0]
        if len(defects) > 0:
            stabs = self._code.stabilizer_generators()
            stab = stabs[defects[0]]
            # Correct the first qubit in the stabilizer support
            q = stab.qubits[0]
            pauli = PauliOp.X if stab.stabilizer_type == "Z" else PauliOp.Z
            correction[q] = pauli

        return DecoderResult(
            correction=correction,
            success=True,  # provisional
            metadata={"strategy": "naive"},
        )
```

Optionally override `precompute()` and `build_decoding_graph()`:

```python
    def precompute(self) -> None:
        # Build any data structures needed for fast decoding
        super().precompute()

    def build_decoding_graph(self):
        # Return {"nodes": [...], "edges": [...], "boundary_nodes": [...]}
        ...
```

Register with the decoder registry:

```python
from qens.core.registry import Registry
from qens.decoders.base import Decoder

decoder_registry = Registry[Decoder]()
decoder_registry.register("naive", NaiveDecoder)
```

---

## Next Steps

- [Error Models](error-models.md) -- Noise models that produce the syndromes
  decoders consume.
- [Codes](codes.md) -- The codes that decoders operate on.
- [Simulation](simulation.md) -- Automated Monte Carlo sampling with decoders.
- [Visualization](visualization.md) -- Visualize decoding graphs and matchings.
