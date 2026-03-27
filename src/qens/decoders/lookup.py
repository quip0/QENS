from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import numpy as np

from qens.core.types import Syndrome, PauliString, PauliOp
from qens.decoders.base import Decoder, DecoderResult

if TYPE_CHECKING:
    from qens.codes.base import QECCode


class LookupTableDecoder(Decoder):
    """Lookup table decoder for small codes.

    Precomputes a mapping from every possible syndrome to the minimum-weight
    correction. Only feasible for small codes (distance <= ~7).
    """

    def __init__(self, code: QECCode) -> None:
        super().__init__(code)
        self._table: dict[bytes, PauliString] = {}

    def precompute(self) -> None:
        """Build the syndrome -> correction lookup table."""
        nd = self._code.num_data_qubits
        best: dict[bytes, tuple[int, PauliString]] = {}

        # Enumerate all Pauli errors up to weight floor(d/2)
        max_weight = self._code.code_distance // 2
        for weight in range(max_weight + 1):
            for positions in itertools.combinations(range(nd), weight):
                # For each position, try X, Y, Z
                for paulis in itertools.product([PauliOp.X, PauliOp.Y, PauliOp.Z], repeat=weight):
                    if weight == 0:
                        error = np.zeros(nd, dtype=np.uint8)
                        syndrome = self._code.compute_syndrome(error)
                        key = syndrome.tobytes()
                        if key not in best:
                            best[key] = (0, error.copy())
                        break
                    else:
                        error = np.zeros(nd, dtype=np.uint8)
                        for pos, pauli in zip(positions, paulis):
                            error[pos] = pauli
                        syndrome = self._code.compute_syndrome(error)
                        key = syndrome.tobytes()
                        if key not in best or weight < best[key][0]:
                            best[key] = (weight, error.copy())

        self._table = {k: v[1] for k, v in best.items()}
        super().precompute()

    def decode(self, syndrome: Syndrome) -> DecoderResult:
        if not self._precomputed:
            self.precompute()

        key = syndrome.tobytes()
        if key in self._table:
            correction = self._table[key]
        else:
            # Syndrome not in table — return identity (no correction)
            correction = np.zeros(self._code.num_data_qubits, dtype=np.uint8)

        success = not self._code.is_logical_error(correction)

        return DecoderResult(
            correction=correction,
            success=success,
            metadata={"table_hit": key in self._table},
        )
