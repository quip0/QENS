"""Custom composed noise model with circuit and decoding visualization.

Demonstrates how to combine multiple error sources into a single noise
model, build a syndrome extraction circuit, visualize it with error
annotations, and inspect the decoding graph after a single shot.
"""
import matplotlib
matplotlib.use("Agg")

import numpy as np

from qens import (
    SurfaceCode,
    DepolarizingError,
    MeasurementError,
    CrosstalkError,
    ComposedNoiseModel,
    MWPMDecoder,
    NoisySampler,
    draw_circuit,
    draw_decoding_graph,
)

# --- 1. Build a composed noise model ---
# Combine depolarizing noise on data qubits, measurement readout errors,
# and ZZ crosstalk between nearest-neighbor pairs.
depolarizing = DepolarizingError(p=0.01)
measurement = MeasurementError(p_0to1=0.005)
crosstalk = CrosstalkError(coupling_map={
    (0, 1): 0.002,
    (1, 2): 0.002,
    (3, 4): 0.002,
    (4, 5): 0.002,
    (6, 7): 0.002,
    (7, 8): 0.002,
    (0, 3): 0.002,
    (3, 6): 0.002,
    (1, 4): 0.002,
    (4, 7): 0.002,
    (2, 5): 0.002,
    (5, 8): 0.002,
})

noise = ComposedNoiseModel([depolarizing, measurement, crosstalk])
print(f"Composed noise model: {noise}")
print(f"  Components: {len(noise.models)}")
for m in noise.models:
    print(f"    - {m}")

# --- 2. Build a d=3 surface code and its syndrome circuit ---
code = SurfaceCode(distance=3)
circuit = code.syndrome_circuit(rounds=1)

print(f"\nCode: {code}")
print(f"  Total qubits in circuit: {circuit.num_qubits}")
print(f"  Circuit depth: {circuit.depth}")

# --- 3. Draw the circuit with error annotations ---
fig_circuit = draw_circuit(
    circuit,
    noise_model=noise,
    highlight_errors=True,
)
fig_circuit.save("noisy_circuit.png")
fig_circuit.close()
print("\nNoisy circuit diagram saved to noisy_circuit.png")

# --- 4. Run a single shot, decode, and visualize the decoding graph ---
decoder = MWPMDecoder(code)
decoder.precompute()

sampler = NoisySampler(seed=77)
sim_result = sampler.run(code, depolarizing, decoder, shots=1)

syndrome = sim_result.sample_syndrome(0)
error = sim_result.sample_error(0)

print(f"\nSingle-shot results:")
print(f"  Error:    {error}")
print(f"  Syndrome: {syndrome}")
print(f"  Logical error: {sim_result.logical_errors[0]}")

# Decode again to get the DecoderResult with matching metadata
decode_result = decoder.decode(syndrome)

fig_graph = draw_decoding_graph(
    decoder,
    syndrome=syndrome,
    decode_result=decode_result,
    show_matching=True,
    title="Decoding Graph (d=3 Surface Code)",
)
fig_graph.save("decoding_graph.png")
fig_graph.close()
print("Decoding graph saved to decoding_graph.png")
