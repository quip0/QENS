"""QENS - Quantum Error and Noise Simulation SDK."""

from qens._version import __version__

# Core
from qens.core.types import PauliOp, Outcome
from qens.core.circuit import Circuit, Gate, Moment

# Codes
from qens.codes.repetition import RepetitionCode
from qens.codes.surface import SurfaceCode
from qens.codes.color import ColorCode

# Noise models
from qens.noise.pauli import BitFlipError, PhaseFlipError, DepolarizingError, PauliYError
from qens.noise.measurement import MeasurementError
from qens.noise.gate import CoherentRotationError, CrosstalkError
from qens.noise.correlated import CorrelatedPauliError
from qens.noise.leakage import LeakageError
from qens.noise.composed import ComposedNoiseModel

# Decoders
from qens.decoders.mwpm import MWPMDecoder
from qens.decoders.union_find import UnionFindDecoder
from qens.decoders.lookup import LookupTableDecoder

# Simulation
from qens.simulation.experiment import ThresholdExperiment
from qens.simulation.sampler import NoisySampler
from qens.simulation.result import SimulationResult, ThresholdResult

# Visualization
from qens.viz.circuit_diagram import draw_circuit
from qens.viz.lattice_view import draw_lattice
from qens.viz.decoding_graph import draw_decoding_graph
from qens.viz.stats import plot_threshold, plot_logical_rates, plot_histogram

__all__ = [
    "__version__",
    # Core
    "PauliOp", "Outcome", "Circuit", "Gate", "Moment",
    # Codes
    "RepetitionCode", "SurfaceCode", "ColorCode",
    # Noise
    "BitFlipError", "PhaseFlipError", "DepolarizingError", "PauliYError",
    "MeasurementError", "CoherentRotationError", "CrosstalkError",
    "CorrelatedPauliError", "LeakageError", "ComposedNoiseModel",
    # Decoders
    "MWPMDecoder", "UnionFindDecoder", "LookupTableDecoder",
    # Simulation
    "ThresholdExperiment", "NoisySampler", "SimulationResult", "ThresholdResult",
    # Visualization
    "draw_circuit", "draw_lattice", "draw_decoding_graph",
    "plot_threshold", "plot_logical_rates", "plot_histogram",
]
