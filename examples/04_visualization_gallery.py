"""Visualization gallery: every plot type in QENS.

Produces five separate PNG files demonstrating:
  1. Repetition code lattice with a syndrome overlay
  2. Surface code lattice with an error overlay
  3. Surface code syndrome extraction circuit
  4. Decoding graph with matching
  5. Threshold plot from mock data
"""
import matplotlib
matplotlib.use("Agg")

import numpy as np

from qens import (
    RepetitionCode,
    SurfaceCode,
    DepolarizingError,
    MWPMDecoder,
    NoisySampler,
    draw_lattice,
    draw_circuit,
    draw_decoding_graph,
)
from qens.viz.stats import plot_threshold
from qens.simulation.result import ThresholdResult

# ---------------------------------------------------------------
# 1. Repetition code lattice with syndrome overlay
# ---------------------------------------------------------------
print("1/5  Repetition code lattice with syndrome overlay...")

rep_code = RepetitionCode(distance=5)
noise = DepolarizingError(p=0.15)
sampler = NoisySampler(seed=10)
rep_result = sampler.sample_errors(rep_code, noise, shots=1)

syndrome = rep_result.sample_syndrome(0)
error = rep_result.sample_error(0)

fig = draw_lattice(
    rep_code,
    syndrome=syndrome,
    error=error,
    title="Repetition Code (d=5) — Syndrome + Error",
)
fig.save("output/gallery_rep_lattice.png")
fig.close()
print("     -> output/gallery_rep_lattice.png")

# ---------------------------------------------------------------
# 2. Surface code lattice with error overlay
# ---------------------------------------------------------------
print("2/5  Surface code lattice with error overlay...")

surf_code = SurfaceCode(distance=3)
surf_result = sampler.sample_errors(surf_code, DepolarizingError(p=0.10), shots=1)

surf_syndrome = surf_result.sample_syndrome(0)
surf_error = surf_result.sample_error(0)

fig = draw_lattice(
    surf_code,
    syndrome=surf_syndrome,
    error=surf_error,
    title="Surface Code (d=3) — Error Overlay",
)
fig.save("output/gallery_surface_lattice.png")
fig.close()
print("     -> output/gallery_surface_lattice.png")

# ---------------------------------------------------------------
# 3. Surface code syndrome extraction circuit
# ---------------------------------------------------------------
print("3/5  Surface code syndrome circuit diagram...")

circuit = surf_code.syndrome_circuit(rounds=1)
fig = draw_circuit(circuit)
fig.save("output/gallery_circuit.png")
fig.close()
print("     -> output/gallery_circuit.png")

# ---------------------------------------------------------------
# 4. Decoding graph with matching
# ---------------------------------------------------------------
print("4/5  Decoding graph with matching...")

decoder = MWPMDecoder(surf_code)
decoder.precompute()

# Use the syndrome from step 2
decode_result = decoder.decode(surf_syndrome)

fig = draw_decoding_graph(
    decoder,
    syndrome=surf_syndrome,
    decode_result=decode_result,
    show_matching=True,
    title="Decoding Graph with Matching (d=3)",
)
fig.save("output/gallery_decoding_graph.png")
fig.close()
print("     -> output/gallery_decoding_graph.png")

# ---------------------------------------------------------------
# 5. Threshold plot from mock data
# ---------------------------------------------------------------
print("5/5  Mock threshold plot...")

# Create a realistic-looking mock ThresholdResult so this example
# runs instantly without a full sweep.
distances = [3, 5, 7]
p_rates = [0.001, 0.003, 0.005, 0.008, 0.01, 0.015, 0.02]

# Mock logical error rates that show threshold-like crossing behavior
mock_rates = np.array([
    # d=3: higher logical rates
    [0.0002, 0.0020, 0.0055, 0.0140, 0.0230, 0.0520, 0.0900],
    # d=5: crosses d=3 near the threshold
    [0.00002, 0.0006, 0.0030, 0.0100, 0.0200, 0.0550, 0.1050],
    # d=7: lowest at small p, crosses near threshold
    [0.000003, 0.0002, 0.0015, 0.0070, 0.0170, 0.0580, 0.1200],
], dtype=np.float64)

mock_result = ThresholdResult(
    distances=distances,
    physical_error_rates=p_rates,
    logical_error_rates=mock_rates,
    shots_per_point=10_000,
)

fig = plot_threshold(mock_result, title="Threshold Plot (Mock Data)")
fig.save("output/gallery_threshold.png")
fig.close()
print("     -> output/gallery_threshold.png")

print("\nAll gallery images saved.")
