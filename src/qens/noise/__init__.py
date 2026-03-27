from qens.core.registry import Registry
from qens.noise.base import ErrorModel
from qens.noise.pauli import BitFlipError, PhaseFlipError, DepolarizingError, PauliYError
from qens.noise.measurement import MeasurementError
from qens.noise.gate import CoherentRotationError, CrosstalkError
from qens.noise.correlated import CorrelatedPauliError
from qens.noise.leakage import LeakageError
from qens.noise.composed import ComposedNoiseModel

noise_registry = Registry[ErrorModel]()
noise_registry.register("bit_flip", BitFlipError)
noise_registry.register("phase_flip", PhaseFlipError)
noise_registry.register("depolarizing", DepolarizingError)
noise_registry.register("pauli_y", PauliYError)
noise_registry.register("measurement", MeasurementError)
noise_registry.register("coherent_rotation", CoherentRotationError)
noise_registry.register("crosstalk", CrosstalkError)
noise_registry.register("correlated_pauli", CorrelatedPauliError)
noise_registry.register("leakage", LeakageError)

# --- EXTENSION POINT ---
# To register a custom error model:
#   from qens.noise import noise_registry
#   noise_registry.register("my_model", MyCustomErrorModel)

__all__ = [
    "ErrorModel",
    "BitFlipError",
    "PhaseFlipError",
    "DepolarizingError",
    "PauliYError",
    "MeasurementError",
    "CoherentRotationError",
    "CrosstalkError",
    "CorrelatedPauliError",
    "LeakageError",
    "ComposedNoiseModel",
    "noise_registry",
]
