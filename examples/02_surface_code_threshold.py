"""Surface code threshold experiment.

Sweeps physical error rates across multiple surface code distances to
produce the standard threshold plot used in QEC research. Lines for
different distances should cross near the threshold error rate.
"""
import matplotlib
matplotlib.use("Agg")

from qens import (
    SurfaceCode,
    DepolarizingError,
    MWPMDecoder,
    ThresholdExperiment,
)
from qens.viz.stats import plot_threshold

# --- Configuration ---
distances = [3, 5, 7]
physical_error_rates = [0.001, 0.003, 0.005, 0.008, 0.01, 0.015, 0.02]
shots_per_point = 1000  # Keep low for a fast example; increase for research

# --- Set up and run the experiment ---
print("Surface Code Threshold Experiment")
print(f"  Distances:       {distances}")
print(f"  Error rates:     {physical_error_rates}")
print(f"  Shots per point: {shots_per_point}")
print()

experiment = ThresholdExperiment(
    code_class=SurfaceCode,
    distances=distances,
    physical_error_rates=physical_error_rates,
    noise_model_factory=lambda p: DepolarizingError(p=p),
    decoder_class=MWPMDecoder,
    shots_per_point=shots_per_point,
    seed=123,
)

total_points = len(distances) * len(physical_error_rates)

def on_progress(completed: int, total: int) -> None:
    pct = 100 * completed / total
    print(f"  [{completed}/{total}] {pct:.0f}% complete")

print("Running sweep...")
result = experiment.run(progress_callback=on_progress)
print()

# --- Print results table ---
print("Results:")
header = f"{'d':>4s}" + "".join(f"  p={p:.4f}" for p in physical_error_rates)
print(header)
print("-" * len(header))
for i, d in enumerate(distances):
    row = f"{d:>4d}"
    for j in range(len(physical_error_rates)):
        row += f"  {result.logical_error_rates[i, j]:8.4f}"
    print(row)

# --- Save threshold plot ---
fig_handle = plot_threshold(
    result,
    title="Surface Code Threshold (MWPM Decoder)",
)
fig_handle.save("output/surface_threshold.png")
fig_handle.close()
print("\nThreshold plot saved to output/surface_threshold.png")
