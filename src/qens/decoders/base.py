from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


from qens.core.types import Syndrome, PauliString

if TYPE_CHECKING:
    from qens.codes.base import QECCode


@dataclass
class DecoderResult:
    """Result of a decoding attempt.

    Note: ``success`` is a provisional estimate based only on the correction
    (the decoder does not know the actual error). For true success evaluation,
    use ``NoisySampler.run()`` which checks ``is_logical_error(error * correction)``.
    """
    correction: PauliString
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


class Decoder(ABC):
    """Base class for decoders.

    # --- EXTENSION POINT ---
    # To add a new decoder:
    # 1. Subclass Decoder
    # 2. Implement decode() to map syndromes to corrections
    # 3. Override build_decoding_graph() if your decoder uses a graph
    # 4. Register with: decoder_registry.register("my_decoder", MyDecoder)
    """

    def __init__(self, code: QECCode) -> None:
        self._code = code
        self._precomputed: bool = False

    @property
    def code(self) -> QECCode:
        return self._code

    @abstractmethod
    def decode(self, syndrome: Syndrome) -> DecoderResult:
        """Decode a syndrome into a correction operator."""
        ...

    def precompute(self) -> None:
        """Optional: precompute decoding structures (graphs, tables)."""
        self._precomputed = True

    def build_decoding_graph(self) -> dict[str, Any]:
        """Return a graph representation for visualization.

        Returns dict with 'nodes', 'edges', 'boundary_nodes' keys.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not provide a decoding graph."
        )
