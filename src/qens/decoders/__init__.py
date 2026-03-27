from qens.core.registry import Registry
from qens.decoders.base import Decoder, DecoderResult
from qens.decoders.lookup import LookupTableDecoder
from qens.decoders.union_find import UnionFindDecoder
from qens.decoders.mwpm import MWPMDecoder

decoder_registry = Registry[Decoder]()
decoder_registry.register("lookup", LookupTableDecoder)
decoder_registry.register("union_find", UnionFindDecoder)
decoder_registry.register("mwpm", MWPMDecoder)

# --- EXTENSION POINT ---
# To register a custom decoder:
#   from qens.decoders import decoder_registry
#   decoder_registry.register("my_decoder", MyCustomDecoder)

__all__ = [
    "Decoder",
    "DecoderResult",
    "LookupTableDecoder",
    "UnionFindDecoder",
    "MWPMDecoder",
    "decoder_registry",
]
