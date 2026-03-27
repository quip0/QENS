<img src="../images/logo/compactlogo.svg" width="200" alt="QENS">

# Extension Guide

QENS is designed from the ground up to be extensible. Every major subsystem follows the same **Abstract Base Class + Registry** pattern, making it straightforward to add custom error models, quantum error-correcting codes, decoders, and visualizers without modifying the core library.

This guide covers the architecture, walks through each extension point with full working examples, and provides a reference for the registry API.

---

## Extension Architecture

QENS exposes four extension points, each built on the same pattern:

1. **An abstract base class** that defines the interface your component must implement.
2. **A module-level `Registry` instance** that maps string names to concrete classes.
3. **Extension point comments** in the source code marking where new components should be added.

The four extension points are:

| Extension Point | Base Class   | Registry            | Module           |
|-----------------|-------------|---------------------|------------------|
| Error Models    | `ErrorModel`  | `noise_registry`    | `qens.noise`     |
| QEC Codes       | `QECCode`     | `code_registry`     | `qens.codes`     |
| Decoders        | `Decoder`     | `decoder_registry`  | `qens.decoders`  |
| Visualizers     | `Visualizer`  | `viz_registry`      | `qens.viz`       |

All registries are instances of `Registry[T]` from `qens.core.registry`.

---

## Creating a Custom Error Model

### Step-by-Step

1. **Subclass `ErrorModel`** from `qens.noise`.
2. **Implement `sample_errors(num_qubits, affected_qubits, rng) -> PauliString`** — this is the core method that generates a random Pauli error given the number of qubits, the set of affected qubit indices, and a NumPy random generator.
3. **Implement `__repr__`** to provide a human-readable description.
4. **Optionally implement `to_channel()`** to return a `NoiseChannel` (Kraus representation) for analytical work.
5. **Optionally implement `applies_to(gate)`** to restrict which gates this error model acts on.
6. **Register** your model with the noise registry.

### Full Example: Thermal Relaxation Error

```python
import numpy as np
from qens.noise import ErrorModel, noise_registry
from qens.core.types import PauliString, PauliOp


class ThermalRelaxationError(ErrorModel):
    """Simulates energy relaxation (T1) and dephasing (T2) during a gate.

    Given T1, T2, and the gate duration, computes the probabilities of
    X, Y, and Z errors occurring during the gate.
    """

    def __init__(self, t1: float, t2: float, gate_time: float) -> None:
        if t2 > 2 * t1:
            raise ValueError("T2 <= 2*T1 is required by physics.")
        if gate_time < 0:
            raise ValueError("gate_time must be non-negative.")
        self.t1 = t1
        self.t2 = t2
        self.gate_time = gate_time

        # Derived probabilities
        p_reset = 1.0 - np.exp(-gate_time / t1)
        p_phase = 1.0 - np.exp(-gate_time / t2) if t2 > 0 else 1.0
        self._p_x = p_reset / 4.0
        self._p_y = p_reset / 4.0
        self._p_z = p_phase / 2.0 - p_reset / 4.0
        self._p_z = max(self._p_z, 0.0)

    def sample_errors(
        self,
        num_qubits: int,
        affected_qubits: list[int],
        rng: np.random.Generator,
    ) -> PauliString:
        error = [PauliOp.I] * num_qubits
        for q in affected_qubits:
            r = rng.random()
            if r < self._p_x:
                error[q] = PauliOp.X
            elif r < self._p_x + self._p_y:
                error[q] = PauliOp.Y
            elif r < self._p_x + self._p_y + self._p_z:
                error[q] = PauliOp.Z
        return tuple(error)

    def __repr__(self) -> str:
        return (
            f"ThermalRelaxationError(t1={self.t1}, t2={self.t2}, "
            f"gate_time={self.gate_time})"
        )


# Register the custom model
noise_registry.register("thermal_relaxation", ThermalRelaxationError)
```

### Using the Custom Model

```python
from qens.core.types import PauliOp
from qens.utils import get_rng

model = ThermalRelaxationError(t1=50e-6, t2=70e-6, gate_time=35e-9)
rng = get_rng(seed=42)

# Sample a single error on a 5-qubit system affecting qubits 0 and 2
error = model.sample_errors(5, [0, 2], rng)
print(error)  # e.g. (PauliOp.I, PauliOp.I, PauliOp.Z, PauliOp.I, PauliOp.I)

# Retrieve by name from the registry
from qens.noise import noise_registry
cls = noise_registry.get("thermal_relaxation")
model2 = cls(t1=50e-6, t2=70e-6, gate_time=35e-9)
```

---

## Creating a Custom QEC Code

### Step-by-Step

1. **Subclass `QECCode`** from `qens.codes`.
2. **Implement all abstract properties:**
   - `name -> str`
   - `num_data_qubits -> int`
   - `num_ancilla_qubits -> int`
   - `code_distance -> int`
3. **Implement all abstract methods:**
   - `stabilizer_generators() -> list[Stabilizer]`
   - `logical_operators() -> list[LogicalOperator]`
   - `check_matrix() -> np.ndarray`
   - `syndrome_circuit(rounds: int) -> Circuit`
   - `qubit_coordinates() -> dict[int, Coordinate]`
4. **Inherit from the base class** which provides computed helpers:
   - `num_qubits` (returns `num_data_qubits + num_ancilla_qubits`)
   - `compute_syndrome(error: PauliString) -> Syndrome`
   - `is_logical_error(correction: PauliString) -> bool`
5. **Register** with the code registry.

### Full Example: Three-Qubit Bit-Flip Code

```python
import numpy as np
from qens.codes import QECCode, Stabilizer, LogicalOperator, code_registry
from qens.core.circuit import Circuit
from qens.core.types import PauliOp, PauliString, Coordinate


class ThreeQubitBitFlip(QECCode):
    """The simplest QEC code: corrects a single bit-flip (X) error on 3 qubits.

    Stabilizers: Z0 Z1, Z1 Z2
    Logical operator: X0 X1 X2
    """

    @property
    def name(self) -> str:
        return "three_qubit_bit_flip"

    @property
    def num_data_qubits(self) -> int:
        return 3

    @property
    def num_ancilla_qubits(self) -> int:
        return 2

    @property
    def code_distance(self) -> int:
        return 3

    def stabilizer_generators(self) -> list[Stabilizer]:
        return [
            Stabilizer(
                name="S0",
                pauli_string=(PauliOp.Z, PauliOp.Z, PauliOp.I),
            ),
            Stabilizer(
                name="S1",
                pauli_string=(PauliOp.I, PauliOp.Z, PauliOp.Z),
            ),
        ]

    def logical_operators(self) -> list[LogicalOperator]:
        return [
            LogicalOperator(
                name="X_L",
                pauli_string=(PauliOp.X, PauliOp.X, PauliOp.X),
            ),
        ]

    def check_matrix(self) -> np.ndarray:
        return np.array([
            [1, 1, 0],
            [0, 1, 1],
        ], dtype=np.uint8)

    def syndrome_circuit(self, rounds: int = 1) -> Circuit:
        circuit = Circuit(self.num_qubits)
        for _ in range(rounds):
            # Measure Z0 Z1 using ancilla qubit 3
            circuit.cx(0, 3).cx(1, 3).measure(3).reset(3)
            # Measure Z1 Z2 using ancilla qubit 4
            circuit.cx(1, 4).cx(2, 4).measure(4).reset(4)
        return circuit

    def qubit_coordinates(self) -> dict[int, Coordinate]:
        return {
            0: (0.0, 0.0),
            1: (1.0, 0.0),
            2: (2.0, 0.0),
            3: (0.5, 1.0),  # ancilla for S0
            4: (1.5, 1.0),  # ancilla for S1
        }


# Register
code_registry.register("three_qubit_bit_flip", ThreeQubitBitFlip)
```

### Using the Custom Code

```python
code = ThreeQubitBitFlip()
print(code.num_qubits)          # 5
print(code.code_distance)       # 3

# Compute syndrome for a single X error on qubit 0
error = (PauliOp.X, PauliOp.I, PauliOp.I)
syndrome = code.compute_syndrome(error)
print(syndrome)                  # (1, 0)
```

---

## Creating a Custom Decoder

### Step-by-Step

1. **Subclass `Decoder`** from `qens.decoders`.
2. **Call `super().__init__(code)`** in your constructor, passing the `QECCode` instance.
3. **Implement `decode(syndrome) -> DecoderResult`** — return a `DecoderResult` containing the inferred correction as a `PauliString` and optionally the confidence.
4. **Optionally implement `precompute()`** for any setup work (e.g., building lookup tables).
5. **Optionally implement `build_decoding_graph()`** for visualization support.
6. **Register** with the decoder registry.

### Full Example: Majority Vote Decoder for Repetition Code

```python
import numpy as np
from qens.decoders import Decoder, DecoderResult, decoder_registry
from qens.codes import QECCode
from qens.core.types import PauliOp, PauliString, Syndrome


class MajorityVoteDecoder(Decoder):
    """A simple majority-vote decoder for the repetition code.

    Counts the number of syndrome bits that are 1. If a majority are
    triggered, infers a logical error; otherwise, infers no error.
    This is optimal for the repetition code under i.i.d. bit-flip noise.
    """

    def __init__(self, code: QECCode) -> None:
        super().__init__(code)

    def decode(self, syndrome: Syndrome) -> DecoderResult:
        n = self.code.num_data_qubits
        num_flagged = sum(syndrome)
        total = len(syndrome)

        if num_flagged > total / 2:
            # Majority of stabilizers flagged: apply X to all data qubits
            correction = tuple(PauliOp.X for _ in range(n))
        else:
            # No correction needed
            correction = tuple(PauliOp.I for _ in range(n))

        return DecoderResult(
            correction=correction,
            confidence=1.0 - (num_flagged / total) if total > 0 else 1.0,
        )

    def __repr__(self) -> str:
        return f"MajorityVoteDecoder(code={self.code.name})"


# Register
decoder_registry.register("majority_vote", MajorityVoteDecoder)
```

### Using the Custom Decoder

```python
from qens.codes import RepetitionCode

code = RepetitionCode(distance=5)
decoder = MajorityVoteDecoder(code)

# Syndrome with 3 out of 4 stabilizers flagged
syndrome = (1, 1, 1, 0)
result = decoder.decode(syndrome)
print(result.correction)   # (PauliOp.X, PauliOp.X, PauliOp.X, PauliOp.X, PauliOp.X)
print(result.confidence)   # 0.25
```

---

## Creating a Custom Visualizer

### Step-by-Step

1. **Subclass `Visualizer`** from `qens.viz.base`.
2. **Implement `draw(**kwargs) -> FigureHandle`** — create a matplotlib figure and return it wrapped in a `FigureHandle`.
3. **Use matplotlib** for all rendering.
4. **Return `FigureHandle(fig=fig, axes=ax)`** so the caller can further customize or save the figure.
5. **Register** with the viz registry.

### Brief Example

```python
import matplotlib.pyplot as plt
from qens.viz.base import Visualizer, FigureHandle, viz_registry


class SyndromeHistoryVisualizer(Visualizer):
    """Plots syndrome measurement outcomes over multiple rounds as a heatmap."""

    def __init__(self, syndrome_history: list[tuple[int, ...]]) -> None:
        self.syndrome_history = syndrome_history

    def draw(self, **kwargs) -> FigureHandle:
        import numpy as np

        data = np.array(self.syndrome_history)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 4)))
        ax.imshow(data.T, cmap="Greys", aspect="auto", interpolation="nearest")
        ax.set_xlabel("Round")
        ax.set_ylabel("Stabilizer index")
        ax.set_title("Syndrome History")
        return FigureHandle(fig=fig, axes=ax)


viz_registry.register("syndrome_history", SyndromeHistoryVisualizer)
```

---

## Registry API Reference

All registries are instances of `Registry[T]` from `qens.core.registry`. The API is identical across all four registries.

### Creating a Registry

```python
from qens.core.registry import Registry

my_registry: Registry[MyBaseClass] = Registry()
```

### Methods

| Method / Operation              | Signature                           | Description                                      |
|---------------------------------|-------------------------------------|--------------------------------------------------|
| `register(name, cls)`          | `(str, type[T]) -> None`           | Register a class under the given name.           |
| `get(name)`                     | `(str) -> type[T]`                 | Retrieve a registered class by name.             |
| `list_registered()`            | `() -> list[str]`                  | Return a list of all registered names.           |
| `name in registry`             | `__contains__(str) -> bool`        | Check if a name is registered.                   |

### Error Handling

- Registering a **duplicate name** raises `ValueError`.
- Retrieving a **missing name** raises `KeyError`.

---

## Available Registries

| Registry            | Module Path        | Base Class   | Built-in Registrations                                                                                                        |
|---------------------|--------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------|
| `noise_registry`    | `qens.noise`       | `ErrorModel`  | `bit_flip`, `phase_flip`, `depolarizing`, `pauli_y`, `measurement`, `coherent_rotation`, `crosstalk`, `correlated_pauli`, `leakage` |
| `code_registry`     | `qens.codes`       | `QECCode`     | `repetition`, `surface`, `color`                                                                                              |
| `decoder_registry`  | `qens.decoders`    | `Decoder`     | `lookup_table`, `mwpm`, `union_find`                                                                                          |
| `viz_registry`      | `qens.viz`         | `Visualizer`  | `circuit`, `lattice`, `decoding_graph`, `threshold`, `logical_rates`, `histogram`                                             |

---

## Tips for Extension Authors

- **Follow the existing patterns.** Look at built-in implementations for reference.
- **Write tests.** Statistical tests for noise models (10,000 samples, 3-sigma tolerance). Unit tests for codes and decoders. Smoke tests for visualizers.
- **Use type annotations** on all public methods and properties.
- **Register in `__init__.py`** of the relevant subpackage so users can discover your component via the registry.
- **Keep it pure Python + NumPy.** QENS avoids compiled extensions to maximize portability.
