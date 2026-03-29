<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Decoder Comparison Guide

QENS provides three decoders. This guide explains how each one works, when to use it, and what trade-offs to expect.

---

## Quick Reference

| Decoder | Class | Algorithm | Time per decode | Memory | Optimal? |
|---------|-------|-----------|-----------------|--------|----------|
| Lookup Table | `LookupTableDecoder` | Precomputed table | O(1) | O(2^s) | Yes (for correctable errors) |
| MWPM | `MWPMDecoder` | Greedy min-weight matching | O(n²) | O(n) | Near-optimal |
| Union-Find | `UnionFindDecoder` | Growth + fusion | O(n·α(n)) | O(n) | Approximate |

*s = number of stabilizers; n = number of syndrome defects; α = inverse Ackermann function (effectively constant)*

All three follow the same interface:

```python
decoder = SomeDecoder(code)
decoder.precompute()              # optional; auto-called on first decode()
result = decoder.decode(syndrome) # returns DecoderResult
```

---

## LookupTableDecoder

**Best for:** Distance ≤ 7, prototyping, debugging, optimal-correction baselines.

### How it works

`LookupTableDecoder` precomputes a mapping from every possible syndrome (a binary vector of length $s$) to the minimum-weight Pauli correction. The table has $2^s$ entries.

```python
from qens import RepetitionCode, LookupTableDecoder
from qens.core.types import PauliOp
import numpy as np

code = RepetitionCode(distance=5)
decoder = LookupTableDecoder(code)
decoder.precompute()  # Builds the 2^4 = 16-entry table

error = np.zeros(code.num_data_qubits, dtype=np.uint8)
error[2] = PauliOp.X

syndrome = code.compute_syndrome(error)
result = decoder.decode(syndrome)

print(f"Correction: {result.correction}")
print(f"Table hit:  {result.metadata['table_hit']}")
```

### Metadata

| Key | Type | Description |
|-----|------|-------------|
| `table_hit` | `bool` | Whether the syndrome was in the precomputed table. If `False`, no correction is applied. |

### Limitations

The table size grows as $2^s$. For a distance-9 surface code with 80 stabilizers, the table requires $2^{80}$ entries — infeasible. Use `LookupTableDecoder` only when the number of stabilizers is ≤ ~20.

| Code | d | Stabilizers | Table entries |
|------|---|------------|---------------|
| `RepetitionCode` | 5 | 4 | 16 |
| `RepetitionCode` | 7 | 6 | 64 |
| `SurfaceCode` | 3 | 8 | 256 |
| `SurfaceCode` | 5 | 24 | ~16 million |

---

## MWPMDecoder

**Best for:** Surface code simulations at d ≤ 15–20, near-optimal decoding quality.

### How it works

`MWPMDecoder` builds a **decoding graph** where:
- Nodes correspond to stabilizer generators
- Edges connect stabilizers that share a data qubit, weighted by 1.0
- A boundary node connects to weight-2 stabilizers with weight 0.5

Given a syndrome, the decoder identifies **defects** (non-zero syndrome bits) and uses greedy minimum-weight perfect matching to pair them. The correction is the union of data qubits on the matched paths.

```python
from qens import SurfaceCode, MWPMDecoder, DepolarizingError
import numpy as np

code = SurfaceCode(distance=5)
decoder = MWPMDecoder(code)
decoder.precompute()

noise = DepolarizingError(p=0.01)
rng = np.random.default_rng(42)
error = noise.sample_errors(code.num_data_qubits, list(range(code.num_data_qubits)), rng)

syndrome = code.compute_syndrome(error)
result = decoder.decode(syndrome)

print(f"Defects:    {result.metadata['num_defects']}")
print(f"Matching:   {result.metadata['matching']}")
print(f"Correction: {result.correction}")
```

### Decoding Graph

You can inspect the graph that MWPM operates on:

```python
graph = decoder.build_decoding_graph()
print(f"Nodes:          {len(graph['nodes'])}")
print(f"Edges:          {len(graph['edges'])}")
print(f"Boundary nodes: {graph['boundary_nodes']}")

# Visualize
from qens import draw_decoding_graph
fig = draw_decoding_graph(decoder, title="MWPM Decoding Graph")
fig.show()
```

### Metadata

| Key | Type | Description |
|-----|------|-------------|
| `num_defects` | `int` | Number of non-zero syndrome bits |
| `matching` | `list[tuple]` | List of `(node_a, node_b, weight)` matched pairs |

### Performance notes

The greedy matching is O(n²) where n is the number of defects. For low error rates (few defects), this is fast. For high error rates near threshold, n grows and the decoder slows. Precompute cost is O(edges) — fast for all practical code sizes.

---

## UnionFindDecoder

**Best for:** Large-scale threshold sweeps, any code size, fastest per shot.

### How it works

`UnionFindDecoder` implements the growth-and-fusion strategy (Delfosse & Nickerson, 2021) using a weighted union-find with path compression:

1. **Growth phase:** Process edges in order of increasing weight. When an edge connects two components where at least one contains a defect, fuse them into a single cluster.
2. **Peeling phase:** Walk the fused cluster tree and extract a correction by flipping data qubits shared between matched stabilizers.

```python
from qens import SurfaceCode, UnionFindDecoder, DepolarizingError
import numpy as np

code = SurfaceCode(distance=7)
decoder = UnionFindDecoder(code)
decoder.precompute()

noise = DepolarizingError(p=0.01)
rng = np.random.default_rng(42)
error = noise.sample_errors(code.num_data_qubits, list(range(code.num_data_qubits)), rng)

syndrome = code.compute_syndrome(error)
result = decoder.decode(syndrome)

print(f"Defects:    {result.metadata['num_defects']}")
print(f"Correction: {result.correction}")
```

### Metadata

| Key | Type | Description |
|-----|------|-------------|
| `num_defects` | `int` | Number of non-zero syndrome bits |

### Performance notes

The union-find operations run in O(α(n)) per operation (inverse Ackermann — effectively O(1)). The growth phase processes all edges once: O(edges). Total complexity is O(n·α(n)) per decode — near-linear.

This makes `UnionFindDecoder` the clear choice for large threshold sweeps where per-shot decoding time dominates.

---

## Side-by-Side Comparison

### Decoding quality

At low error rates (well below threshold), all three decoders perform similarly. Near and above threshold, decoding quality diverges:

```python
from qens import NoisySampler, SurfaceCode, DepolarizingError
from qens import LookupTableDecoder, MWPMDecoder, UnionFindDecoder

code = SurfaceCode(distance=3)
noise = DepolarizingError(p=0.05)
sampler = NoisySampler(seed=42)

for cls in [MWPMDecoder, UnionFindDecoder]:
    decoder = cls(code)
    result = sampler.run(code, noise, decoder, shots=5_000)
    print(f"{cls.__name__:20s}: LER = {result.logical_error_rate:.4f}")
```

### When correctability matters

- `LookupTableDecoder` produces the **minimum-weight correction** for every correctable syndrome — it is provably optimal for correctable errors.
- `MWPMDecoder` achieves near-optimal quality in practice; the greedy matching rarely misses the true minimum-weight pairing.
- `UnionFindDecoder` is approximate — it may occasionally choose a sub-optimal correction, but the gap is small at typical operating points.

---

## Choosing a Decoder

| Scenario | Recommendation |
|----------|---------------|
| Learning and prototyping | `LookupTableDecoder` on small codes |
| Surface code d ≤ 7, exact results needed | `LookupTableDecoder` |
| Surface code d ≤ 15, research simulations | `MWPMDecoder` |
| Surface code d > 15, or threshold sweep | `UnionFindDecoder` |
| Color code, any distance | `MWPMDecoder` or `UnionFindDecoder` |
| Comparing decoder quality | All three at same (code, noise) point |

---

## Important Note on `DecoderResult.success`

The `success` field is a **provisional estimate** — the decoder checks whether its own correction would be a logical error, not whether `error * correction` is. It can be wrong.

```python
# DON'T use this for statistics:
result = decoder.decode(syndrome)
is_success = result.success  # unreliable

# DO use NoisySampler for statistical accuracy:
sampler = NoisySampler(seed=42)
run_result = sampler.run(code, noise, decoder, shots=10_000)
print(f"True LER: {run_result.logical_error_rate:.4f}")
```

---

## Building Custom Decoders

All decoders inherit from `qens.decoders.base.Decoder`. Implement `decode()` at minimum:

```python
from qens.decoders.base import Decoder, DecoderResult
from qens.core.types import Syndrome
import numpy as np

class MyDecoder(Decoder):
    def decode(self, syndrome: Syndrome) -> DecoderResult:
        correction = np.zeros(self._code.num_data_qubits, dtype=np.uint8)
        # ... your decoding logic ...
        return DecoderResult(correction=correction, success=True, metadata={})
```

Optionally override `precompute()` to build data structures, and `build_decoding_graph()` to enable visualization.

See the [Extending QENS](extending.md) guide and the [Decoders reference](decoders.md) for full details.

---

## Next Steps

- [Decoders API Reference](decoders.md) — Complete decoder API documentation
- [Decoder Comparison Notebook](notebooks/03_decoder_comparison.ipynb) — Interactive benchmarks
- [Syndrome Extraction Guide](syndrome-extraction.md) — How syndromes are produced
- [Simulation Guide](simulation.md) — Running threshold experiments
