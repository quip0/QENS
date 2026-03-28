# Changelog

All notable changes to QENS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

**Surface Code**
- Fixed coordinate system mismatch in `SurfaceCode._build_layout()` — data qubits were at `(r, c)` while ancilla qubits used doubled coordinates `(2*fr+1, 2*fc+1)`, causing the lattice visualization to render with data qubits bunched together and ancillas spread apart. Data qubit coordinates are now `(2*r, 2*c)` so both share a unified grid
- Surface code lattice visualization completely rewritten to match standard QEC style (qiskit-qec convention):
  - Stabilizer plaquettes drawn as filled `Polygon` patches built from neighboring data qubit vertex positions, with black outlines
  - X-stabilizer plaquettes use tomato fill, Z-stabilizer plaquettes use yellowgreen fill
  - Data qubits rendered as small black dots (`s=50`) instead of large colored circles
  - Active syndrome bits shown as red star markers (`marker="*"`) at ancilla positions
  - Error qubits colored by type: X=red, Y=purple, Z=blue with enlarged markers
  - Qubit index labels use offset annotations instead of centered white text
  - Legend moved outside the plot area with compact styling
  - Compact figure sizing (`scale=0.35`, tight margins) for inline notebook use

**Color Code Construction**
- 4.8.8 color code: plaquettes now use the best single color class with neighbors-only (excluding center vertex), producing non-overlapping even-weight plaquettes that properly tile the lattice. Previously only 3 plaquettes were generated at any distance; now d=5 produces 7 plaquettes and d=7 produces 12, with full coverage of all data qubits
- 6.6.6 color code: completely rewritten to use a honeycomb lattice tiled within an equilateral triangle. Flat-top hexagonal cells are clipped to the triangle boundary, producing proper 6-qubit interior plaquettes and 4-qubit boundary plaquettes. Previously used a rectangular 2x2 grid that did not correspond to any standard color code construction

**Visualization**
- Color code visualization (`draw_lattice` for `ColorCode`): completely rewritten to match standard QEC literature style. Plaquettes are now drawn as bold, opaque polygon fills (tomato/yellowgreen/steelblue) with black outlines, data qubits as small black dots with offset labels, visible axes
- Fixed poor readability across all visualization outputs — titles, labels, legends, and node markers were too small to read at typical display sizes
- Decoding graph (`draw_decoding_graph`) no longer resembles a traveling-salesman-problem diagram: nodes now display index labels, edges show weight annotations, matching edges are clearly distinguished from structural edges, and boundary nodes have better spacing
- Circuit diagram (`draw_circuit`) gates and labels were too small and tightly packed — increased column/row spacing, gate sizes, control dot sizes, and line widths
- Threshold and stats plots had undersized markers, thin lines, and small axis labels

### Changed

**Surface Code**
- `SurfaceCode._build_layout()`: data qubit coordinates changed from `(r, c)` to `(2*r, 2*c)` to share grid with ancilla coordinates. Only affects visualization; qubit indices, stabilizers, check matrix, and syndrome circuit are unchanged.

**Color Code**
- `ColorCode._build_488()`: plaquette generation uses single color class with neighbors-only approach instead of center+neighbors with multi-class fallback
- `ColorCode._build_666()`: completely new honeycomb-in-triangle construction replacing the previous rectangular-grid approach. Data qubit coordinates are now Cartesian `(x, y)` floats instead of integer grid positions
- CSS validation relaxed to check even plaquette weight only (pairwise overlap check removed)

**Visualization**
- Default style sizes increased: font 9→11, qubit markers 300→450, ancilla markers 200→320, edge width 1.5→2.0
- Added `color_code_plaquette_colors` to `QENSStyle` for the 3-color palette: `("tomato", "yellowgreen", "steelblue")`
- Color code rendering uses a dedicated `_draw_color_code()` path separate from the surface code rendering
- Example scripts now save output to `output/` (gitignored) instead of `images/`
- Notebook multi-panel composites use `tempfile` instead of writing to `images/`
- `images/` directory now contains only curated documentation assets

## [0.1.0] - 2026-03-27

### Added

**Core**
- Quantum circuit builder with fluent API supporting H, X, Z, CX, CZ, M, and R gates
- PauliOp enum, PauliString, Syndrome, and Coordinate type aliases
- NoiseChannel with Kraus operator representation and CPTP validation
- Generic Registry[T] plugin system for extensibility across all subsystems
- Pauli algebra utilities: multiplication, commutation check, and symplectic inner product
- GF(2) sparse matrix with row reduction and kernel computation
- Seeded RNG wrapper for reproducible simulations

**Error Models**
- ErrorModel abstract base class defining the noise model interface
- BitFlipError for independent X errors with tunable probability
- PhaseFlipError for independent Z errors with tunable probability
- DepolarizingError for symmetric X/Y/Z errors
- PauliYError for independent Y errors
- MeasurementError with asymmetric readout flip probabilities
- CoherentRotationError for small coherent over-rotations about a Pauli axis
- CrosstalkError for correlated noise on specified qubit pairs
- CorrelatedPauliError for joint multi-qubit Pauli errors
- LeakageError with stateful leakage tracking and probabilistic return
- ComposedNoiseModel for stacking multiple error models in sequence

**QEC Codes**
- QECCode abstract base class with stabilizers, check matrices, and syndrome circuits
- RepetitionCode supporting any distance >= 2
- SurfaceCode (rotated layout) for odd distance >= 3
- ColorCode with 4.8.8 and 6.6.6 lattice types for odd distance >= 3
- Lattice infrastructure with LatticeNode, LatticeEdge, and Lattice dataclasses

**Decoders**
- Decoder abstract base class with DecoderResult output
- LookupTableDecoder for exact decoding of small codes via exhaustive enumeration
- MWPMDecoder implementing greedy minimum-weight perfect matching
- UnionFindDecoder with almost-linear-time decoding

**Simulation**
- NoisySampler for Monte Carlo error injection, syndrome measurement, and decoding
- PauliFrameSimulator for efficient Clifford circuit simulation
- ThresholdExperiment for sweeping physical error rates across multiple code distances
- SimulationResult and ThresholdResult data containers

**Visualization**
- draw_circuit() with error annotation support
- draw_lattice() with syndrome and error overlays
- draw_decoding_graph() with matching edge visualization
- plot_threshold() for standard QEC threshold plots
- plot_logical_rates() bar charts for comparing decoder performance
- plot_histogram() general-purpose histogram plotting
- QENSStyle configurable color palette for consistent visual identity

**Documentation**
- Comprehensive README with installation instructions and usage guide
- Getting started guide for new users
- Core concepts reference covering types, circuits, and the registry system
- Per-feature documentation for error models, codes, decoders, simulation, and visualization
- Extension guide with full working examples for all four extension points
- Complete API reference organized by module
- Architecture overview
- Contributing guidelines with development setup and code standards
- Four runnable example scripts demonstrating end-to-end workflows

**Testing**
- 194 unit, integration, and smoke tests covering all modules
- Statistical validation for noise models using 10,000-sample runs with 3-sigma tolerance
- Full test suite executes in under 1 second

[0.1.0]: https://github.com/quip0/QENS/releases/tag/v0.1.0
