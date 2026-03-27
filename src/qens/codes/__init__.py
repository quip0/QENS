from qens.core.registry import Registry
from qens.codes.base import QECCode, Stabilizer, LogicalOperator
from qens.codes.lattice import Lattice, LatticeNode, LatticeEdge
from qens.codes.repetition import RepetitionCode
from qens.codes.surface import SurfaceCode
from qens.codes.color import ColorCode

code_registry = Registry[QECCode]()
code_registry.register("repetition", RepetitionCode)
code_registry.register("surface", SurfaceCode)
code_registry.register("color", ColorCode)

# --- EXTENSION POINT ---
# To register a custom QEC code:
#   from qens.codes import code_registry
#   code_registry.register("my_code", MyCustomCode)

__all__ = [
    "QECCode",
    "Stabilizer",
    "LogicalOperator",
    "Lattice",
    "LatticeNode",
    "LatticeEdge",
    "RepetitionCode",
    "SurfaceCode",
    "ColorCode",
    "code_registry",
]
