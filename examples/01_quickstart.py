"""Quickstart: run a simple repetition code simulation.

Demonstrates the basic QENS workflow:
  1. Create a repetition code
  2. Apply depolarizing noise
  3. Decode with a lookup table decoder
  4. Measure the logical error rate
  5. Save a lattice visualization
"""
import matplotlib
matplotlib.use("Agg")

from qens import (
    RepetitionCode,
    DepolarizingError,
    LookupTableDecoder,
    ThresholdExperiment,
    draw_lattice,
)

# --- 1. Build a distance-3 repetition code ---
code = RepetitionCode(distance=3)
print(f"Code: {code}")
print(f"  Data qubits:    {code.num_data_qubits}")
print(f"  Ancilla qubits: {code.num_ancilla_qubits}")
print(f"  Distance:       {code.code_distance}")

# --- 2. Set up noise and decoder ---
noise = DepolarizingError(p=0.05)
decoder = LookupTableDecoder(code)

# --- 3. Run 10,000 shots ---
print("\nRunning 10,000 shots...")
result = ThresholdExperiment.single_point(
    code=code,
    noise_model=noise,
    decoder=decoder,
    shots=10_000,
    seed=42,
)

# --- 4. Print results ---
print(f"Shots:              {result.num_shots}")
print(f"Logical errors:     {result.logical_error_count}")
print(f"Logical error rate: {result.logical_error_rate:.4f}")

# --- 5. Save a lattice visualization ---
fig_handle = draw_lattice(code, title="Repetition Code (d=3)")
fig_handle.save("quickstart_lattice.png")
fig_handle.close()
print("\nLattice saved to quickstart_lattice.png")
